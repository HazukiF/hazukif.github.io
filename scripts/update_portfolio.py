"""
Shadow Portfolio Pipeline
=========================
Reads trades.csv, pulls current and historical prices via yfinance,
calculates portfolio metrics, and outputs data/portfolio.json for
the website frontend to consume.

Run manually:   python scripts/update_portfolio.py
Run via CI:     GitHub Actions runs this on a daily cron schedule
"""

import json
import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf


# ── Configuration ──────────────────────────────────────────────

STARTING_CAPITAL = 100_000  # USD
RISK_FREE_RATE = 0.05       # annualized, for Sharpe calculation
USD_JPY_TICKER = "JPY=X"    # USD/JPY exchange rate

BENCHMARKS = {
    "Nikkei 225": "^N225",
    "S&P 500": "^GSPC",
}

SECTOR_MAP = {
    "6501.T": "Industrials",
    "8306.T": "Financials",
    "6758.T": "Technology",
    "8035.T": "Semiconductors",
    "7203.T": "Autos",
    "9984.T": "Technology",
    "4063.T": "Materials",
    "2914.T": "Consumer Staples",
    "AAPL":   "Technology",
    "MSFT":   "Technology",
    "GOOGL":  "Technology",
    "V":      "Financials",
}

TRADES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trades.csv")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "portfolio.json")


# ── Data Loading ───────────────────────────────────────────────

def load_trades(path: str) -> pd.DataFrame:
    """Load and validate the trades CSV."""
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    required_cols = {"date", "ticker", "action", "shares", "price", "currency"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"trades.csv is missing columns: {missing}")

    return df


def get_fx_rate() -> float:
    """Get current USD/JPY exchange rate."""
    try:
        fx = yf.Ticker(USD_JPY_TICKER)
        rate = fx.fast_info.get("lastPrice", None)
        if rate and rate > 0:
            return rate
    except Exception:
        pass
    # Fallback
    return 150.0


def get_all_tickers(trades: pd.DataFrame) -> list:
    """Extract unique tickers from trades."""
    return trades["ticker"].unique().tolist()


def fetch_prices(tickers: list, start_date: str) -> pd.DataFrame:
    """Fetch historical daily close prices for all tickers."""
    all_tickers = tickers + list(BENCHMARKS.values()) + [USD_JPY_TICKER]
    data = yf.download(all_tickers, start=start_date, auto_adjust=True, progress=False)

    # Handle single vs multi ticker return format
    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"]
    else:
        prices = data[["Close"]]
        prices.columns = all_tickers[:1]

    prices = prices.ffill().bfill()
    return prices


# ── Portfolio Construction ─────────────────────────────────────

def build_positions(trades: pd.DataFrame) -> pd.DataFrame:
    """Aggregate trades into current positions."""
    positions = []

    for ticker, group in trades.groupby("ticker"):
        buys = group[group["action"] == "BUY"]
        sells = group[group["action"] == "SELL"]

        total_bought = buys["shares"].sum()
        total_sold = sells["shares"].sum() if len(sells) > 0 else 0
        current_shares = total_bought - total_sold

        if current_shares <= 0:
            continue

        # Weighted average cost
        avg_cost = (buys["shares"] * buys["price"]).sum() / buys["shares"].sum()
        currency = buys["currency"].iloc[0]
        first_buy = buys["date"].min()

        positions.append({
            "ticker": ticker,
            "shares": current_shares,
            "avg_cost": round(avg_cost, 2),
            "currency": currency,
            "sector": SECTOR_MAP.get(ticker, "Other"),
            "first_buy": first_buy.strftime("%Y-%m-%d"),
        })

    return pd.DataFrame(positions)


def calculate_holdings(positions: pd.DataFrame, prices: pd.DataFrame, fx_rate: float) -> list:
    """Calculate current value and return for each position."""
    holdings = []

    for _, pos in positions.iterrows():
        ticker = pos["ticker"]
        if ticker not in prices.columns:
            continue

        current_price = prices[ticker].dropna().iloc[-1]
        avg_cost = pos["avg_cost"]
        shares = pos["shares"]
        currency = pos["currency"]

        # Calculate values in USD
        if currency == "JPY":
            cost_usd = (avg_cost * shares) / fx_rate
            value_usd = (current_price * shares) / fx_rate
            display_cost = f"¥{avg_cost:,.0f}"
            display_current = f"¥{current_price:,.0f}"
        else:
            cost_usd = avg_cost * shares
            value_usd = current_price * shares
            display_cost = f"${avg_cost:,.2f}"
            display_current = f"${current_price:,.2f}"

        pct_return = ((current_price - avg_cost) / avg_cost) * 100

        # Get company name from yfinance
        try:
            info = yf.Ticker(ticker).info
            company_name = info.get("shortName", info.get("longName", ticker))
        except Exception:
            company_name = ticker

        holdings.append({
            "ticker": ticker,
            "company_name": company_name,
            "sector": pos["sector"],
            "shares": int(shares),
            "avg_cost": avg_cost,
            "current_price": round(float(current_price), 2),
            "display_cost": display_cost,
            "display_current": display_current,
            "currency": currency,
            "cost_usd": round(cost_usd, 2),
            "value_usd": round(value_usd, 2),
            "return_pct": round(pct_return, 2),
        })

    # Sort by value descending
    holdings.sort(key=lambda x: x["value_usd"], reverse=True)
    return holdings


# ── Portfolio Analytics ────────────────────────────────────────

def calculate_daily_nav(trades: pd.DataFrame, prices: pd.DataFrame, fx_rate_series: pd.Series) -> pd.Series:
    """
    Calculate daily portfolio NAV (net asset value) from inception.
    Tracks cash + holdings value each day.
    """
    tickers = trades["ticker"].unique()
    dates = prices.index
    inception = trades["date"].min()
    dates = dates[dates >= pd.Timestamp(inception)]

    # Build position history: shares held per ticker per day
    nav_series = []

    for date in dates:
        cash = STARTING_CAPITAL
        holdings_value = 0

        # Process all trades up to this date
        trades_to_date = trades[trades["date"] <= date]
        position_shares = {}

        for _, trade in trades_to_date.iterrows():
            t = trade["ticker"]
            if t not in position_shares:
                position_shares[t] = 0

            cost = trade["shares"] * trade["price"]
            if trade["currency"] == "JPY":
                # Convert trade cost to USD using rate at trade date
                fx_at_trade = fx_rate_series.asof(trade["date"])
                if pd.isna(fx_at_trade) or fx_at_trade <= 0:
                    fx_at_trade = 150.0
                cost = cost / fx_at_trade

            if trade["action"] == "BUY":
                position_shares[t] = position_shares[t] + trade["shares"]
                cash -= cost
            elif trade["action"] == "SELL":
                position_shares[t] = position_shares[t] - trade["shares"]
                cash += cost

        # Value holdings at current date's prices
        fx_today = fx_rate_series.asof(date)
        if pd.isna(fx_today) or fx_today <= 0:
            fx_today = 150.0

        for t, shares in position_shares.items():
            if shares <= 0 or t not in prices.columns:
                continue
            price = prices[t].asof(date)
            if pd.isna(price):
                continue

            currency = trades[trades["ticker"] == t]["currency"].iloc[0]
            if currency == "JPY":
                holdings_value += (price * shares) / fx_today
            else:
                holdings_value += price * shares

        total = cash + holdings_value
        nav_series.append({"date": date, "nav": total})

    nav_df = pd.DataFrame(nav_series).set_index("date")
    return nav_df["nav"]


def calculate_metrics(nav: pd.Series) -> dict:
    """Calculate key portfolio statistics from NAV series."""
    # Returns
    total_return = ((nav.iloc[-1] / nav.iloc[0]) - 1) * 100

    # YTD
    current_year = datetime.now().year
    ytd_start = nav.index[nav.index >= pd.Timestamp(f"{current_year}-01-01")]
    if len(ytd_start) > 0:
        ytd_return = ((nav.iloc[-1] / nav.asof(ytd_start[0])) - 1) * 100
    else:
        ytd_return = total_return

    # Daily returns for Sharpe
    daily_returns = nav.pct_change().dropna()
    if len(daily_returns) > 1:
        excess_returns = daily_returns - (RISK_FREE_RATE / 252)
        sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
    else:
        sharpe = 0

    # Max drawdown
    cummax = nav.cummax()
    drawdown = (nav - cummax) / cummax
    max_drawdown = drawdown.min() * 100
    max_dd_date = drawdown.idxmin()

    return {
        "total_return": round(total_return, 2),
        "ytd_return": round(ytd_return, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown": round(max_drawdown, 2),
        "max_drawdown_date": max_dd_date.strftime("%b %Y") if not pd.isna(max_dd_date) else "",
        "current_nav": round(nav.iloc[-1], 2),
    }


def calculate_benchmark_returns(prices: pd.DataFrame, inception_date) -> dict:
    """Calculate benchmark cumulative return series."""
    benchmarks = {}
    for name, ticker in BENCHMARKS.items():
        if ticker in prices.columns:
            series = prices[ticker].dropna()
            series = series[series.index >= pd.Timestamp(inception_date)]
            if len(series) > 0:
                cumulative = ((series / series.iloc[0]) - 1) * 100
                benchmarks[name] = {
                    "current": round(cumulative.iloc[-1], 2),
                }
    return benchmarks


def calculate_allocations(holdings: list, total_value: float) -> dict:
    """Calculate geography and sector breakdowns."""
    geo = {}
    sector = {}

    for h in holdings:
        weight = h["value_usd"] / total_value if total_value > 0 else 0

        # Geography
        country = "Japan" if h["currency"] == "JPY" else "United States"
        geo[country] = geo.get(country, 0) + weight

        # Sector
        s = h["sector"]
        sector[s] = sector.get(s, 0) + weight

    # Sort descending
    geo = {k: round(v * 100, 1) for k, v in sorted(geo.items(), key=lambda x: -x[1])}
    sector = {k: round(v * 100, 1) for k, v in sorted(sector.items(), key=lambda x: -x[1])}

    return {"geography": geo, "sector": sector}


def build_chart_series(nav: pd.Series, prices: pd.DataFrame, inception_date) -> dict:
    """Build time series data for the performance chart."""
    # Resample to weekly for cleaner chart
    nav_weekly = nav.resample("W").last()
    cumulative = ((nav_weekly / nav_weekly.iloc[0]) - 1) * 100

    chart = {
        "dates": [d.strftime("%Y-%m-%d") for d in cumulative.index],
        "portfolio": [round(v, 2) for v in cumulative.values],
    }

    for name, ticker in BENCHMARKS.items():
        if ticker in prices.columns:
            bench = prices[ticker].dropna()
            bench = bench[bench.index >= pd.Timestamp(inception_date)]
            if len(bench) > 0:
                bench_weekly = bench.resample("W").last()
                # Align to same dates
                bench_weekly = bench_weekly.reindex(nav_weekly.index, method="ffill")
                bench_cum = ((bench_weekly / bench_weekly.iloc[0]) - 1) * 100
                chart[name] = [round(v, 2) if not pd.isna(v) else 0 for v in bench_cum.values]

    return chart


# ── Main Pipeline ──────────────────────────────────────────────

def main():
    print("Loading trades...")
    trades = load_trades(TRADES_PATH)
    inception_date = trades["date"].min().strftime("%Y-%m-%d")
    tickers = get_all_tickers(trades)

    print(f"Found {len(trades)} trades across {len(tickers)} tickers")
    print(f"Inception date: {inception_date}")

    print("Fetching prices...")
    prices = fetch_prices(tickers, start_date=inception_date)

    print("Getting FX rate...")
    fx_rate = get_fx_rate()
    fx_series = prices[USD_JPY_TICKER] if USD_JPY_TICKER in prices.columns else pd.Series(fx_rate, index=prices.index)
    print(f"USD/JPY: {fx_rate:.2f}")

    print("Building positions...")
    positions = build_positions(trades)
    print(f"Active positions: {len(positions)}")

    print("Calculating holdings...")
    holdings = calculate_holdings(positions, prices, fx_rate)

    total_invested = sum(h["value_usd"] for h in holdings)
    total_value = STARTING_CAPITAL  # Will be overwritten by NAV

    print("Calculating daily NAV...")
    nav = calculate_daily_nav(trades, prices, fx_series)
    total_value = nav.iloc[-1]

    cash_usd = total_value - total_invested
    cash_pct = (cash_usd / total_value) * 100 if total_value > 0 else 0

    print("Calculating metrics...")
    metrics = calculate_metrics(nav)
    benchmarks = calculate_benchmark_returns(prices, inception_date)

    print("Calculating allocations...")
    allocations = calculate_allocations(holdings, total_value)
    allocations["geography"]["Cash"] = round(cash_pct, 1)

    print("Building chart data...")
    chart = build_chart_series(nav, prices, inception_date)

    # Calculate weight for each holding
    for h in holdings:
        h["weight"] = round((h["value_usd"] / total_value) * 100, 1) if total_value > 0 else 0

    # ── Assemble output ──
    output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "inception_date": inception_date,
        "starting_capital": STARTING_CAPITAL,
        "summary": {
            "portfolio_value": round(total_value, 2),
            "total_return": metrics["total_return"],
            "ytd_return": metrics["ytd_return"],
            "sharpe_ratio": metrics["sharpe_ratio"],
            "max_drawdown": metrics["max_drawdown"],
            "max_drawdown_date": metrics["max_drawdown_date"],
            "positions_count": len(holdings),
            "jp_count": sum(1 for h in holdings if h["currency"] == "JPY"),
            "us_count": sum(1 for h in holdings if h["currency"] == "USD"),
            "cash_usd": round(cash_usd, 2),
            "cash_pct": round(cash_pct, 1),
        },
        "benchmarks": benchmarks,
        "holdings": holdings,
        "allocations": allocations,
        "chart": chart,
    }

    # ── Write JSON ──
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nPortfolio JSON written to {OUTPUT_PATH}")
    print(f"Portfolio value: ${total_value:,.2f}")
    print(f"Total return: {metrics['total_return']:+.2f}%")
    print(f"Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max drawdown: {metrics['max_drawdown']:.2f}%")


if __name__ == "__main__":
    main()
