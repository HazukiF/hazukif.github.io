// ══════════════════════════════════════════════════
// Shared Site Functionality
// Dark mode + Language toggle
// ══════════════════════════════════════════════════

// ── State ──
let isDarkMode = false;
let currentLang = 'en';

// ── Translations ──
const translations = {
    // Nav
    'nav-portfolio': { en: 'Portfolio', jp: 'ポートフォリオ' },
    'nav-philosophy': { en: 'Philosophy', jp: '投資哲学' },
    'nav-trades': { en: 'Trades', jp: '取引履歴' },
    'nav-research': { en: 'Research', jp: 'リサーチ' },
    'nav-about': { en: 'About', jp: 'プロフィール' },

    // Portfolio page
    'portfolio-label': { en: 'Portfolio Value', jp: '運用総額' },
    'stat-ytd-label': { en: 'YTD Return', jp: '年初来リターン' },
    'stat-sharpe-label': { en: 'Sharpe Ratio', jp: 'シャープレシオ' },
    'stat-sharpe-sub': { en: 'Annualized', jp: '年率換算' },
    'stat-drawdown-label': { en: 'Max Drawdown', jp: '最大ドローダウン' },
    'stat-positions-label': { en: 'Positions', jp: 'ポジション数' },
    'stat-cash-label': { en: 'Cash', jp: '現金' },
    'chart-title': { en: 'Cumulative Return', jp: '累積リターン' },
    'holdings-title': { en: 'Current Holdings', jp: '保有銘柄' },
    'geo-label': { en: 'Geography', jp: '地域配分' },
    'sector-label': { en: 'Sector', jp: 'セクター配分' },
    'th-ticker': { en: 'Ticker', jp: '銘柄コード' },
    'th-sector': { en: 'Sector', jp: 'セクター' },
    'th-weight': { en: 'Weight', jp: '比率' },
    'th-avg-cost': { en: 'Avg Cost', jp: '平均取得価格' },
    'th-current': { en: 'Current', jp: '現在価格' },
    'th-return': { en: 'Return', jp: 'リターン' },
    'filter-all': { en: 'All', jp: '全て' },
    'filter-japan': { en: 'Japan', jp: '日本' },
    'filter-us': { en: 'US', jp: '米国' },

    // Trades page
    'trades-title': { en: 'Trade History', jp: '取引履歴' },
    'th-date': { en: 'Date', jp: '日付' },
    'th-action': { en: 'Action', jp: '売買' },
    'th-shares': { en: 'Shares', jp: '株数' },
    'th-price': { en: 'Price', jp: '価格' },
    'th-value': { en: 'Value', jp: '金額' },
    'th-notes': { en: 'Notes', jp: '備考' },
    'filter-buys': { en: 'Buys', jp: '買い' },
    'filter-sells': { en: 'Sells', jp: '売り' },

    // Philosophy page
    'philosophy-title': { en: 'The Cyborg Investor', jp: 'サイボーグ投資家' },
    'phase1-title': { en: 'The Mechanical Net', jp: '機械のフィルター' },
    'phase1-sub': { en: 'Data Aggregation', jp: 'データ集約' },
    'phase2-title': { en: 'The Numerical Bypass', jp: '数値分析バイパス' },
    'phase2-sub': { en: 'Overcoming the Reading Bottleneck', jp: '読解ボトルネックの克服' },
    'phase3-title': { en: 'The Human Brain', jp: '人間の頭脳' },
    'phase3-sub': { en: 'Generating Alpha', jp: 'アルファの創出' },
    'phase4-title': { en: 'The Mathematical Enforcer', jp: '数学的リスク管理' },
    'phase4-sub': { en: 'Risk Management & Execution', jp: 'リスク管理と執行' },
    'roadmap-label': { en: 'Roadmap', jp: '今後の実装' },

    // Research page
    'research-title': { en: 'Research', jp: '投資リサーチ' },
    'filter-theses': { en: 'Theses', jp: '投資テーゼ' },
    'filter-tearsheets': { en: 'Tear Sheets', jp: 'ティアシート' },

    // About page
    'about-title': { en: 'Between Two Markets', jp: '二つの市場のあいだで' },
    'about-background-label': { en: 'Background', jp: '経歴' },
    'about-philosophy-label': { en: 'Investment Philosophy', jp: '投資哲学' },
    'about-career-label': { en: 'Career Focus', jp: 'キャリア' },
    'about-path-label': { en: 'Path', jp: '歩み' },
    'about-credentials-label': { en: 'Credentials', jp: '資格' },
    'about-languages-label': { en: 'Languages', jp: '言語' },
    'about-tools-label': { en: 'Tools', jp: 'ツール' },

    // Footer
    'footer-disclaimer': {
        en: 'Shadow portfolio for educational purposes only. Not investment advice.<br>Data refreshed daily via automated pipeline. Past performance does not indicate future results.',
        jp: '教育目的のシャドウ・ポートフォリオです。投資助言ではありません。<br>データは自動パイプラインにより毎日更新されます。過去の成績は将来の結果を保証するものではありません。'
    },
};

// ── Dark Mode ──

function toggleDarkMode() {
    isDarkMode = !isDarkMode;
    document.body.classList.toggle('dark', isDarkMode);
    const btn = document.getElementById('dark-mode-btn');
    if (btn) btn.textContent = isDarkMode ? '☀' : '☾';
}

// ── Language Toggle ──

function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'jp' : 'en';

    // Update all translatable elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        if (translations[key] && translations[key][currentLang]) {
            if (el.tagName === 'INPUT' || el.tagName === 'BUTTON') {
                el.textContent = translations[key][currentLang];
            } else {
                el.innerHTML = translations[key][currentLang];
            }
        }
    });

    // Update toggle button
    const btn = document.getElementById('lang-toggle-btn');
    if (btn) btn.textContent = currentLang === 'en' ? 'JP' : 'EN';

    // Fire custom event so page-specific JS can react
    document.dispatchEvent(new CustomEvent('langchange', { detail: { lang: currentLang } }));
}

// ── Initialize Controls ──

function initSiteControls() {
    const darkBtn = document.getElementById('dark-mode-btn');
    const langBtn = document.getElementById('lang-toggle-btn');

    if (darkBtn) darkBtn.addEventListener('click', toggleDarkMode);
    if (langBtn) langBtn.addEventListener('click', toggleLanguage);
}

// Run on load
document.addEventListener('DOMContentLoaded', initSiteControls);
