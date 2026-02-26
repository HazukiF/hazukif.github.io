"""
Shadow Portfolio Pipeline
=========================
Reads trades.csv, pulls current and historical prices via yfinance,
calculates portfolio metrics, and outputs data/portfolio.json for
the website frontend to consume.

Primary currency: JPY (Japanese Yen)
USD positions are converted to JPY at current exchange rate.

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

STARTING_CAPITAL = 15_000_000  # JPY
RISK_FREE_RATE = 0.05          # annualized, for Sharpe calculation
USD_JPY_TICKER = "JPY=X"       # USD/JPY exchange rate

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
    return 150.0


def get_all_tickers(trades: pd.DataFrame) -> list:
    """Extract unique tickers from trades."""
    return trades["ticker"].unique().tolist()


def fetch_prices(tickers: list, start_date: str) -> pd.DataFrame:
    """Fetch historical daily close prices for all tickers with retry logic."""
    all_tickers = tickers + list(BENCHMARKS.values()) + [USD_JPY_TICKER]

    prices = pd.DataFrame()

    # Try bulk download first
    for attempt in range(3):
        try:
            data = yf.download(all_tickers, start=start_date, auto_adjust=True, progress=False)
            if isinstance(data.columns, pd.MultiIndex):
                prices = data["Close"]
            else:
                prices = data[["Close"]]
                prices.columns = all_tickers[:1]
            break
        except Exception as e:
            print(f"  Bulk download attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                print("  Bulk download failed, trying individual tickers...")

    # Retry any tickers that are missing or empty
    for ticker in all_tickers:
        if ticker not in prices.columns or prices[ticker].dropna().empty:
            print(f"  Retrying individual download for {ticker}...")
            for attempt in range(2):
                try:
                    single = yf.download(ticker, start=start_date, auto_adjust=True, progress=False)
                    if not single.empty:
                        if isinstance(single.columns, pd.MultiIndex):
                            prices[ticker] = single["Close"][ticker]
                        else:
                            prices[ticker] = single["Close"]
                        print(f"  ✓ Got {ticker} on retry")
                        break
                except Exception:
                    pass

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
    """Calculate current value and return for each position. All values in JPY."""
    holdings = []

    for _, pos in positions.iterrows():
        ticker = pos["ticker"]
        if ticker not in prices.columns:
            print(f"  Skipping {ticker}: not in price data")
            continue

        ticker_prices = prices[ticker].dropna()
        if len(ticker_prices) == 0:
            print(f"  Skipping {ticker}: no price data available")
            continue

        current_price = ticker_prices.iloc[-1]
        avg_cost = pos["avg_cost"]
        shares = pos["shares"]
        currency = pos["currency"]

        # Calculate values in JPY (primary currency)
        if currency == "JPY":
            cost_jpy = avg_cost * shares
            value_jpy = current_price * shares
            display_cost = f"¥{avg_cost:,.0f}"
            display_current = f"¥{current_price:,.0f}"
        else:
            # USD positions: convert to JPY
            cost_jpy = avg_cost * shares * fx_rate
            value_jpy = current_price * shares * fx_rate
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
            "cost_jpy": round(cost_jpy, 0),
            "value_jpy": round(value_jpy, 0),
            "return_pct": round(pct_return, 2),
        })

    # Sort by value descending
    holdings.sort(key=lambda x: x["value_jpy"], reverse=True)
    return holdings


# ── Portfolio Analytics ────────────────────────────────────────

def calculate_daily_nav(trades: pd.DataFrame, prices: pd.DataFrame, fx_rate_series: pd.Series) -> pd.Series:
    """
    Calculate daily portfolio NAV in JPY from inception.
    Tracks cash + holdings value each day.
    """
    tickers = trades["ticker"].unique()
    dates = prices.index
    inception = trades["date"].min()
    dates = dates[dates >= pd.Timestamp(inception)]

    nav_series = []

    for date in dates:
        cash_jpy = STARTING_CAPITAL
        holdings_value = 0

        # Process all trades up to this date
        trades_to_date = trades[trades["date"] <= date]
        position_shares = {}

        for _, trade in trades_to_date.iterrows():
            t = trade["ticker"]
            if t not in position_shares:
                position_shares[t] = 0

            cost_in_native = trade["shares"] * trade["price"]

            if trade["currency"] == "JPY":
                cost_jpy_trade = cost_in_native
            else:
                # Convert USD cost to JPY at trade date
                fx_at_trade = fx_rate_series.asof(trade["date"])
                if pd.isna(fx_at_trade) or fx_at_trade <= 0:
                    fx_at_trade = 150.0
                cost_jpy_trade = cost_in_native * fx_at_trade

            if trade["action"] == "BUY":
                position_shares[t] = position_shares[t] + trade["shares"]
                cash_jpy -= cost_jpy_trade
            elif trade["action"] == "SELL":
                position_shares[t] = position_shares[t] - trade["shares"]
                cash_jpy += cost_jpy_trade

        # Value holdings at current date's prices (all in JPY)
        fx_today = fx_rate_series.asof(date)
        if pd.isna(fx_today) or fx_today <= 0:
            fx_today = 150.0

        for t, shares in position_shares.items():
            if shares <= 0 or t not in prices.columns:
                continue
            price_series = prices[t].dropna()
            if len(price_series) == 0:
                continue
            price = price_series.asof(date)
            if pd.isna(price):
                continue

            currency = trades[trades["ticker"] == t]["currency"].iloc[0]
            if currency == "JPY":
                holdings_value += price * shares
            else:
                holdings_value += price * shares * fx_today

        total = cash_jpy + holdings_value
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
        "current_nav": round(nav.iloc[-1], 0),
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
        weight = h["value_jpy"] / total_value if total_value > 0 else 0

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

    total_invested_jpy = sum(h["value_jpy"] for h in holdings)

    print("Calculating daily NAV...")
    nav = calculate_daily_nav(trades, prices, fx_series)
    total_value_jpy = nav.iloc[-1]

    cash_jpy = total_value_jpy - total_invested_jpy
    cash_pct = (cash_jpy / total_value_jpy) * 100 if total_value_jpy > 0 else 0

    print("Calculating metrics...")
    metrics = calculate_metrics(nav)
    benchmarks = calculate_benchmark_returns(prices, inception_date)

    print("Calculating allocations...")
    allocations = calculate_allocations(holdings, total_value_jpy)
    allocations["geography"]["Cash"] = round(cash_pct, 1)

    print("Building chart data...")
    chart = build_chart_series(nav, prices, inception_date)

    # Calculate weight for each holding
    for h in holdings:
        h["weight"] = round((h["value_jpy"] / total_value_jpy) * 100, 1) if total_value_jpy > 0 else 0

    # ── Assemble output ──
    output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "inception_date": inception_date,
        "starting_capital": STARTING_CAPITAL,
        "fx_rate": round(fx_rate, 2),
        "summary": {
            "portfolio_value": round(total_value_jpy, 0),
            "total_return": metrics["total_return"],
            "ytd_return": metrics["ytd_return"],
            "sharpe_ratio": metrics["sharpe_ratio"],
            "max_drawdown": metrics["max_drawdown"],
            "max_drawdown_date": metrics["max_drawdown_date"],
            "positions_count": len(holdings),
            "jp_count": sum(1 for h in holdings if h["currency"] == "JPY"),
            "us_count": sum(1 for h in holdings if h["currency"] == "USD"),
            "cash_jpy": round(cash_jpy, 0),
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
    print(f"Portfolio value: ¥{total_value_jpy:,.0f}")
    print(f"USD/JPY: {fx_rate:.2f}")
    print(f"Total return: {metrics['total_return']:+.2f}%")
    print(f"Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max drawdown: {metrics['max_drawdown']:.2f}%")


if __name__ == "__main__":
    main()
