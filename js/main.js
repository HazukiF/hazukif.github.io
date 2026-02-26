// ══════════════════════════════════════════════════
// Shared Site Functionality
// Persistent dark mode + Full bilingual toggle
// ══════════════════════════════════════════════════

// ── State ──
let isDarkMode = false;
let currentLang = 'en';

// ── Translations ──
const translations = {

    // ── Nav ──
    'nav-portfolio': { en: 'Portfolio', jp: 'ポートフォリオ' },
    'nav-philosophy': { en: 'Philosophy', jp: '投資哲学' },
    'nav-trades': { en: 'Trades', jp: '取引履歴' },
    'nav-research': { en: 'Research', jp: 'リサーチ' },
    'nav-about': { en: 'About', jp: 'プロフィール' },

    // ── Portfolio page ──
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

    // ── Trades page ──
    'trades-title': { en: 'Trade History', jp: '取引履歴' },
    'trades-subtitle': { en: '取引履歴', jp: 'Trade History' },
    'th-date': { en: 'Date', jp: '日付' },
    'th-action': { en: 'Action', jp: '売買' },
    'th-shares': { en: 'Shares', jp: '株数' },
    'th-price': { en: 'Price', jp: '価格' },
    'th-value': { en: 'Value', jp: '金額' },
    'th-notes': { en: 'Notes', jp: '備考' },
    'filter-buys': { en: 'Buys', jp: '買い' },
    'filter-sells': { en: 'Sells', jp: '売り' },

    // ── Philosophy page ──
    'philosophy-title': { en: 'Investment Philosophy', jp: '投資思想' },
    'philosophy-subtitle': { en: '投資思想', jp: 'Investment Philosophy' },
    'philosophy-intro-1': {
        en: 'This portfolio operates on a simple premise: neither pure quantitative models nor pure fundamental analysis produce the best risk-adjusted returns, especially in cross-border investing. The strongest edge comes from knowing exactly where the human brain outperforms the machine — and where it doesn\'t.',
        jp: 'このポートフォリオは、シンプルな前提に基づいています。純粋な計量モデルでも純粋なファンダメンタル分析でもない——クロスボーダー投資において最良のリスク調整後リターンを生み出すのは、人間の頭脳が機械を上回る領域と、その逆の領域を正確に見極めることです。'
    },
    'philosophy-intro-2': {
        en: 'What follows is a four-phase investment process that alternates between automated computation and irreplaceable human judgment. The machine handles data aggregation, covariance estimation, and position sizing. The human handles accounting forensics, geopolitical interpretation, and the identification of structural mispricings that no algorithm can detect.',
        jp: '以下に示すのは、自動計算と代替不可能な人間の判断を交互に用いる4段階の投資プロセスです。機械はデータ集約、共分散推定、ポジションサイジングを担当し、人間は会計フォレンジック、地政学的解釈、そしてアルゴリズムでは検出不可能な構造的ミスプライシングの特定を担当します。'
    },
    'phase1-title': { en: 'The Mechanical Net', jp: '機械のフィルター' },
    'phase1-sub': { en: 'Data Aggregation', jp: 'データ集約' },
    'phase1-body': {
        en: 'The investment universe spans 40–50 cross-border equities across the TSE and US exchanges. Manually monitoring prices, volatilities, and valuations across this universe is not scalable — and introduces behavioral bias before any analysis even begins.',
        jp: '投資ユニバースは東証と米国取引所にまたがる40〜50のクロスボーダー銘柄で構成されます。このユニバース全体の価格、ボラティリティ、バリュエーションを手動でモニタリングすることはスケーラブルではなく、分析が始まる前からバイアスが入り込みます。'
    },
    'phase1-input': {
        en: 'A Python pipeline pulls daily closing prices and valuation metrics (P/B, P/E, EV/EBITDA) for the full ticker universe via automated API calls.',
        jp: 'Pythonパイプラインが自動API呼び出しを通じて、投資ユニバース全銘柄の日次終値とバリュエーション指標（PBR、PER、EV/EBITDA）を取得します。'
    },
    'phase1-process': {
        en: 'The script calculates rolling standard and downside volatility, then flags any company whose Price-to-Book ratio drops below a predefined threshold — for example, below 1.0 on the TSE.',
        jp: 'スクリプトがローリング標準ボラティリティと下方ボラティリティを計算し、PBRが事前設定の閾値（例：東証で1.0倍）を下回った企業をフラグします。'
    },
    'phase1-output': {
        en: 'A shortlist of 3–5 companies that warrant human attention this week. No news, no charts, no noise — just the numbers.',
        jp: '今週人間の注目に値する3〜5社のショートリスト。ニュースなし、チャートなし、ノイズなし——数字だけです。'
    },
    'phase2-title': { en: 'The Numerical Bypass', jp: '数値分析バイパス' },
    'phase2-sub': { en: 'Overcoming the Reading Bottleneck', jp: '読解ボトルネックの克服' },
    'phase2-body': {
        en: 'A 200-page Yuho (有価証券報告書) is a massive time sink, even with strong Japanese fluency. Dense corporate prose and kanji-heavy management narratives slow down analysis for any heritage speaker. The cyborg approach bypasses the narrative entirely and goes straight to the ledger.',
        jp: '200ページの有価証券報告書は、日本語が堪能であっても膨大な時間を要します。難解な企業文体と漢字の多い経営記述は、ヘリテージスピーカーであっても分析を遅らせます。サイボーグ・アプローチはナラティブを完全にバイパスし、帳簿に直接アクセスします。'
    },
    'phase2-machine': {
        en: 'Raw, unadjusted J-GAAP and US-GAAP ledgers are exported directly from data platforms into structured spreadsheets. No PDFs, no narrative — just the accounting lines.',
        jp: '未調整のJ-GAAPおよびUS-GAAPの生データをデータプラットフォームから直接構造化スプレッドシートにエクスポートします。PDFなし、ナラティブなし——会計データのみ。'
    },
    'phase2-human': {
        en: 'With Boki-level accounting vocabulary and direct ledger access, the reading barrier vanishes. Focus goes exclusively to the lines that matter: Retained Earnings (利益剰余金), Goodwill (のれん), and Cross-Shareholdings (持ち合い株).',
        jp: '簿記レベルの会計用語と帳簿への直接アクセスにより、読解の壁は消えます。焦点は重要な項目にのみ——利益剰余金、のれん、持ち合い株。'
    },
    'phase3-title': { en: 'The Human Brain', jp: '人間の頭脳' },
    'phase3-sub': { en: 'Generating Alpha', jp: 'アルファの創出' },
    'phase3-body': {
        en: 'This is the one phase where the machine is completely shut off. No algorithm can interpret that the Bank of Japan\'s yield curve control policy is artificially depressing a specific sector. No model understands that a Japanese industrial company is sandbagging its earnings guidance to manage domestic expectations.',
        jp: 'これは機械を完全にオフにする唯一のフェーズです。日本銀行のイールドカーブ・コントロール政策が特定セクターを人為的に抑圧していることをアルゴリズムは解釈できません。日本の製造業が国内向けの期待管理のために業績予想を控えめに出していることをモデルは理解できません。'
    },
    'phase3-analysis': {
        en: 'The exported ledgers feed a 3-statement DCF model. Aggressive J-GAAP goodwill amortization is added back to find true Free Cash Flow. WACC is adjusted based on a geopolitical read of US-Japan trade dynamics.',
        jp: 'エクスポートされた帳簿データを3表連結DCFモデルに投入します。J-GAAPの積極的なのれん償却を加算してFCFの実態を把握し、日米通商関係の地政学的分析に基づきWACCを調整します。'
    },
    'phase3-output': {
        en: 'An intrinsic value estimate becomes a Black-Litterman View (<em>Q</em>), paired with a confidence parameter (<em>Ω</em>) calibrated to the strength of the accounting adjustment. Rock-solid forensics get high confidence; speculative macro reads get low.',
        jp: '本源的価値の推定がBlack-LittermanのView（<em>Q</em>）となり、会計調整の確度に応じた信頼度パラメータ（<em>Ω</em>）と組み合わされます。堅実な会計分析には高い信頼度、投機的なマクロ読みには低い信頼度を設定します。'
    },
    'phase4-title': { en: 'The Mathematical Enforcer', jp: '数学的リスク管理' },
    'phase4-sub': { en: 'Risk Management & Execution', jp: 'リスク管理と執行' },
    'phase4-body': {
        en: 'A brilliant thesis without disciplined sizing is how portfolios blow up. The human generates the conviction; the machine acts as risk manager, enforcing mathematical constraints that override emotional attachment to any single position.',
        jp: '規律あるサイジングのない優れた投資テーゼは、ポートフォリオを破綻させます。人間が確信を生み出し、機械がリスク管理者として、個別ポジションへの感情的な執着を数学的制約で抑制します。'
    },
    'phase4-input': {
        en: 'The View (<em>Q</em>) feeds into the Python optimization engine built during the EDHEC Investment Management specialization.',
        jp: 'View（<em>Q</em>）をEDHEC Investment Management専門課程で構築したPython最適化エンジンに入力します。'
    },
    'phase4-process': {
        en: 'The optimizer recalculates the Downside-ERC anchor with latest data, applies Ledoit-Wolf shrinkage (τ = 0.5) to the covariance matrix, and runs the Black-Litterman posterior to blend market-implied returns with the fundamental view.',
        jp: 'オプティマイザが最新データでDownside-ERCアンカーを再計算し、共分散行列にLedoit-Wolf縮約（τ = 0.5）を適用、Black-Littermanの事後分布を実行してマーケット・インプライド・リターンとファンダメンタル・ビューを統合します。'
    },
    'phase4-output': {
        en: 'A maximum portfolio weight — not a target, a ceiling. The machine might say: "This stock is undervalued, but it has severe negative skewness and high correlation to existing holdings. Maximum allocation: 4.2%."',
        jp: 'ポートフォリオの最大ウェイト——目標ではなく上限です。機械はこう言うかもしれません：「この銘柄は割安だが、深刻な負のスキューと既存保有銘柄との高い相関がある。最大配分：4.2%。」'
    },
    'roadmap-label': { en: 'Roadmap', jp: '今後の実装' },
    'future-rag-title': { en: 'RAG-Powered Filing Analysis', jp: 'RAG活用の開示書類分析' },
    'future-rag-desc': {
        en: 'An LLM pipeline connected to the EDINET API to automatically extract specific accounting variables from Yuho filings, bypassing the kanji reading bottleneck entirely and feeding structured data directly into valuation models.',
        jp: 'EDINET APIに接続したLLMパイプラインにより、有価証券報告書から特定の会計変数を自動抽出し、漢字の読解ボトルネックを完全にバイパスして構造化データを直接バリュエーションモデルに投入します。'
    },
    'future-hrp-title': { en: 'Geopolitical Hierarchical Risk Parity', jp: '地政学的階層リスクパリティ' },
    'future-hrp-desc': {
        en: 'Replacing the standard covariance matrix with HRP clustering that incorporates supply chain dependencies and geographic revenue exposure — ensuring a single geopolitical shock can\'t cascade across ostensibly uncorrelated positions.',
        jp: '標準的な共分散行列を、サプライチェーン依存関係と地域別売上構成を組み込んだHRPクラスタリングに置き換え、単一の地政学的ショックが一見無相関なポジション間で連鎖しないことを保証します。'
    },
    'future-regime-title': { en: 'Regime Detection', jp: 'レジーム検出' },
    'future-regime-desc': {
        en: 'A Hidden Markov Model monitoring macro indicators (USD/JPY velocity, BOJ signals, VIX) to dynamically adjust shrinkage intensity and risk metric selection between stable and crisis market environments.',
        jp: 'マクロ指標（USD/JPYの変動速度、日銀シグナル、VIX）を監視する隠れマルコフモデルにより、安定期と危機的市場環境に応じて縮約強度とリスク指標の選択を動的に調整します。'
    },
    'future-lib-title': { en: 'Accounting Arbitrage Library', jp: '会計アービトラージ・ライブラリ' },
    'future-lib-desc': {
        en: 'A proprietary Python library automating J-GAAP and US-GAAP adjustments across the full investment universe — recalculating intrinsic values for all 40+ tickers simultaneously and generating a complete Black-Litterman view matrix in seconds.',
        jp: '投資ユニバース全体のJ-GAAPとUS-GAAP調整を自動化する独自Pythonライブラリ——40銘柄以上の本源的価値を同時に再計算し、完全なBlack-Littermanビュー行列を数秒で生成します。'
    },

    // ── Research page ──
    'research-title': { en: 'Research', jp: 'リサーチ' },
    'research-subtitle': { en: 'リサーチ', jp: 'Research' },
    'research-intro': {
        en: 'Investment theses and tear sheets for current and past portfolio positions. Each report details the governance thesis, accounting adjustments, valuation model, and risk assessment that informed the trade.',
        jp: '現在および過去のポートフォリオ・ポジションに関する投資テーゼとティアシート。各レポートは、取引判断の根拠となったガバナンス・テーゼ、会計調整、バリュエーション・モデル、リスク評価を詳述します。'
    },
    'filter-theses': { en: 'Theses', jp: '投資テーゼ' },
    'filter-tearsheets': { en: 'Tear Sheets', jp: 'ティアシート' },

    // ── About page ──
    'about-title': { en: 'About Me', jp: 'プロフィール' },
    'about-background-label': { en: 'Background', jp: '経歴' },
    'about-bg-1': {
        en: 'I was born in Japan, raised in Manhattan, and spent my formative years moving between Tokyo and New York. I attended public school in New York through sixth grade, then returned to Tokyo for two years at Nishimachi International School before enrolling at Keio Academy of New York, a bi-cultural school in Purchase, New York affiliated with Keio University.',
        jp: '日本で生まれ、マンハッタンで育ち、東京とニューヨークを行き来する中で人格形成期を過ごしました。ニューヨークの公立学校に6年生まで通った後、東京の西町インターナショナルスクールで2年間過ごし、その後慶應義塾ニューヨーク学院に入学しました。'
    },
    'about-bg-2': {
        en: 'This constant movement between two worlds gave me something I didn\'t fully appreciate until later: <strong>the ability to see both markets from the inside</strong>. I think in English but I understand Japanese corporate culture intuitively. I can read a 10-K and an 有価証券報告書 with equal comfort. That dual fluency — linguistic and financial — is the foundation everything else is built on.',
        jp: '二つの世界を絶えず行き来する生活は、後になるまで十分に理解できなかった強みを与えてくれました。<strong>両方の市場を内側から見る力</strong>です。英語で思考しながら、日本の企業文化を直感的に理解します。10-Kも有価証券報告書も同じように読みこなせます。この二重の流暢さ——言語と金融の両面における——が、全ての基盤です。'
    },
    'about-bg-3': {
        en: 'I\'m currently a first-year student at <strong>George Washington University\'s Elliott School of International Affairs</strong>, where I study international economics with a focus on the political economy of corporate governance reform in Japan.',
        jp: '現在、<strong>ジョージ・ワシントン大学エリオット国際関係大学院</strong>の1年生として、日本のコーポレート・ガバナンス改革の政治経済学を中心に国際経済学を学んでいます。'
    },
    'about-philosophy-label': { en: 'Investment Philosophy', jp: '投資哲学' },
    'about-phil-1': {
        en: 'I\'m fascinated by the structural differences between how American and Japanese firms organize themselves, allocate capital, and make decisions. Japan\'s corporate governance revolution — the shift from cross-shareholdings and consensus-driven stasis toward shareholder value and board independence — is one of the most consequential investment themes of this decade, and most Western analysts are only seeing it from the outside.',
        jp: '米国企業と日本企業の組織構造、資本配分、意思決定における構造的な違いに深い関心を持っています。日本のコーポレート・ガバナンス改革——持ち合いとコンセンサス重視の膠着状態から株主価値と取締役会の独立性への転換——は今の10年間で最も重要な投資テーマの一つであり、ほとんどの欧米アナリストは外側からしか見ていません。'
    },
    'about-phil-2': {
        en: 'My investment approach begins with governance. I look for companies where structural reform is unlocking value that the market hasn\'t fully priced in — whether that\'s unwinding cross-shareholdings, improving capital allocation, or appointing independent directors who actually push for change. I pair this top-down governance lens with bottom-up financial analysis to build concentrated positions in companies I understand deeply.',
        jp: '投資アプローチはガバナンスから始まります。構造改革が市場に十分織り込まれていない価値を解き放つ企業を探します——持ち合い解消、資本配分の改善、あるいは実際に変革を推進する独立取締役の選任など。このトップダウンのガバナンス視点とボトムアップの財務分析を組み合わせ、深く理解した企業に集中的にポジションを構築します。'
    },
    'about-phil-3': {
        en: 'This portfolio is benchmarked primarily against the <strong>Nikkei 225</strong> and secondarily against the <strong>S&P 500</strong>, reflecting my conviction that the most compelling opportunities right now are in Japanese equities — but with selective US exposure where I see asymmetric risk-reward.',
        jp: 'このポートフォリオは主に<strong>日経225</strong>、副次的に<strong>S&P 500</strong>をベンチマークとしています。これは、現在最も魅力的な投資機会が日本株にあるという確信を反映していますが、非対称なリスク・リターンが見込める場合には選択的に米国エクスポージャーも取ります。'
    },
    'about-career-label': { en: 'Career Focus', jp: 'キャリア' },
    'about-career-1': {
        en: 'I\'m pursuing a career in <strong>asset management at a foreign-affiliated firm in Tokyo</strong> — firms like Goldman Sachs Asset Management, BlackRock Japan, or Fidelity International. I want to work in environments that value independent thinking and analytical rigor over seniority and conformity.',
        jp: '<strong>東京の外資系資産運用会社</strong>——ゴールドマン・サックス・アセット・マネジメント、ブラックロック・ジャパン、フィデリティ・インターナショナルなど——でのキャリアを目指しています。年功序列や画一性よりも、独立した思考と分析の厳密さを重視する環境で働きたいと考えています。'
    },
    'about-career-2': {
        en: 'My edge is positioning: I can bridge American analytical frameworks with deep Japanese market knowledge in a way that\'s difficult to replicate. I\'m not a foreigner trying to learn Japan, and I\'m not a domestic candidate unfamiliar with global best practices. I sit in between — and that\'s where the most interesting investment work happens.',
        jp: '私の強みはポジショニングにあります。米国の分析フレームワークと日本市場の深い知識を、再現が難しい形で橋渡しできます。日本を学ぼうとする外国人でもなく、グローバルなベストプラクティスに疎い国内候補者でもありません。その間に立つ——そこに最も興味深い投資の仕事があります。'
    },
    'about-path-label': { en: 'Path', jp: '歩み' },
    'about-credentials-label': { en: 'Credentials', jp: '資格' },
    'about-languages-label': { en: 'Languages', jp: '言語' },
    'about-tools-label': { en: 'Tools', jp: 'ツール' },

    // ── Footer ──
    'footer-disclaimer': {
        en: 'Shadow portfolio for educational purposes only. Not investment advice.<br>Data refreshed daily via automated pipeline. Past performance does not indicate future results.',
        jp: '教育目的のシャドウ・ポートフォリオです。投資助言ではありません。<br>データは自動パイプラインにより毎日更新されます。過去の成績は将来の結果を保証するものではありません。'
    },
    'footer-short': {
        en: 'Shadow portfolio for educational purposes only. Not investment advice.',
        jp: '教育目的のシャドウ・ポートフォリオです。投資助言ではありません。'
    },
};

// ── Dark Mode ──

function toggleDarkMode() {
    isDarkMode = !isDarkMode;
    document.body.classList.toggle('dark', isDarkMode);
    const btn = document.getElementById('dark-mode-btn');
    if (btn) btn.textContent = isDarkMode ? '☀' : '☾';
    try { localStorage.setItem('darkMode', isDarkMode ? '1' : '0'); } catch(e) {}
}

function applyDarkMode() {
    try {
        const saved = localStorage.getItem('darkMode');
        if (saved === '1') {
            isDarkMode = true;
            document.body.classList.add('dark');
            const btn = document.getElementById('dark-mode-btn');
            if (btn) btn.textContent = '☀';
        }
    } catch(e) {}
}

// ── Language Toggle ──

function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        if (translations[key] && translations[key][currentLang]) {
            el.innerHTML = translations[key][currentLang];
        }
    });

    const btn = document.getElementById('lang-toggle-btn');
    if (btn) btn.textContent = currentLang === 'en' ? 'JP' : 'EN';

    document.dispatchEvent(new CustomEvent('langchange', { detail: { lang: currentLang } }));
}

function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'jp' : 'en';
    applyTranslations();
    try { localStorage.setItem('lang', currentLang); } catch(e) {}
}

function applyLanguage() {
    try {
        const saved = localStorage.getItem('lang');
        if (saved === 'jp') {
            currentLang = 'jp';
            applyTranslations();
        }
    } catch(e) {}
}

// ── Initialize ──

function initSiteControls() {
    // Apply saved preferences immediately
    applyDarkMode();
    applyLanguage();

    const darkBtn = document.getElementById('dark-mode-btn');
    const langBtn = document.getElementById('lang-toggle-btn');

    if (darkBtn) darkBtn.addEventListener('click', toggleDarkMode);
    if (langBtn) langBtn.addEventListener('click', toggleLanguage);
}

// Run as soon as possible
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSiteControls);
} else {
    initSiteControls();
}
