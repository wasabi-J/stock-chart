import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas.tseries.offsets import BDay

st.set_page_config(page_title="大底・天井スコア", layout="wide")

GROUPS = {
    "📁 保有中": {
        "COIN（コインベース）": "COIN",
        "MSTR（マイクロストラテジー）": "MSTR",
        "1328（金ETF・日本）": "1328.T",
        "6963（ローム・モメンタム柱）": "6963.T",
    },
    "📁 短期戦略": {
        "KRUS（くら寿司USA）": "KRUS",
    },
    "📁 監視": {
        "SHAK（シェイクシャック）": "SHAK",
        "JNJ（J&J・守り優等生）": "JNJ",
        "PG（P&G・守り）": "PG",
        "CRM（セールスフォース・攻め）": "CRM",
        "AVAV（エアロバイロンメント）": "AVAV",
        "BABA（アリババ・売却済→監視）": "BABA",
        "7325（アイリック・見送り→監視）": "7325.T",
        "3549（クスリのアオキ・優待）": "3549.T",
        "MARA（マラソンデジタル）": "MARA",
        "CLSK（クリーンスパーク）": "CLSK",
        "NVDA（エヌビディア）": "NVDA",
        "TSLA（テスラ）": "TSLA",
        "GLD（金ETF米国）": "GLD",
        "SLV（銀ETF）": "SLV",
        "1673（銀ETF・日本/WisdomTree）": "1673.T",
        "SOFI（ソーファイ）": "SOFI",
        "EWZ（ブラジルETF）": "EWZ",
        "AMD": "AMD",
        "ESAB（溶接・切断機器）": "ESAB",
        "TTD（トレードデスク・広告）": "TTD",
        "RIVN（リビアン・EV）": "RIVN",
        "OLED（ユニバーサルディスプレイ）": "OLED",
        "MP（MPマテリアルズ・レアアース）": "MP",
        "TMF（米国債20年3倍・売却済→監視）": "TMF",
        "SOXL（半導体3倍）🔬検証済:対象外": "SOXL",
        "QS（クアンタムスケープ）🔬検証済:対象外": "QS",
        "XLE（エネルギーETF）": "XLE",
        "EC（エコペトロール・売却済）": "EC",
    },
    "📁 指数・コモディティ": {
        "BTC（ビットコイン）": "BTC-USD",
        "米10年金利": "^TNX",
        "S&P500": "^GSPC",
        "NASDAQ": "^IXIC",
        "FANG+（NYSE FANG+）": "^NYFANG",
        "日経平均": "^N225",
        "金（ゴールド）": "GC=F",
        "銀（シルバー）": "SI=F",
        "原油WTI": "CL=F",
        "VIX（恐怖指数）": "^VIX",
    },
}
ALL_TICKERS = [(label, tk) for g in GROUPS.values() for label, tk in g.items()]

# 保有銘柄のティッカー集合（フル点灯の強調判定に使う）
HELD_TICKERS = set(GROUPS["📁 保有中"].values())

@st.cache_data(ttl=3600)
def load_data(ticker, period="5y"):
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # OHLC（4本値）を保持してローソク足描画に使う。指標は終値ベース
    keep = {}
    for src, dst in [("Open", "open"), ("High", "high"), ("Low", "low"), ("Close", "close"), ("Volume", "volume")]:
        if src in df.columns:
            keep[dst] = df[src]
    df = pd.DataFrame(keep)
    if "close" not in df.columns:
        return None
    # OHLCが欠ける指標(金利等)は終値で代用
    for col in ["open", "high", "low"]:
        if col not in df.columns:
            df[col] = df["close"]
    df = df.dropna(subset=["close"])
    if len(df) < 260:
        return None
    df["sma25"] = df["close"].rolling(25).mean()
    df["sma75"] = df["close"].rolling(75).mean()
    df["sma200"] = df["close"].rolling(200).mean()
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    df["rsi"] = 100 - (100 / (1 + gain/loss))
    wk = df["close"].resample("W-FRI").last().dropna()
    wd = wk.diff()
    wg = wd.clip(lower=0).rolling(14).mean()
    wl = (-wd.clip(upper=0)).rolling(14).mean()
    w_rsi = 100 - (100 / (1 + wg/wl))
    df["w_rsi"] = w_rsi.reindex(df.index, method="ffill")
    df["bb_mid"] = df["close"].rolling(20).mean()
    bb_std = df["close"].rolling(20).std()
    df["bb_upper"] = df["bb_mid"] + 2*bb_std
    df["bb_lower"] = df["bb_mid"] - 2*bb_std
    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    df["roll_high"] = df["close"].rolling(252, min_periods=1).max()
    df["roll_low"] = df["close"].rolling(252, min_periods=1).min()
    df["drawdown_pct"] = (df["close"] - df["roll_high"]) / df["roll_high"] * 100
    df["rally_pct"] = (df["close"] - df["roll_low"]) / df["roll_low"] * 100
    closes = df["close"].values
    n = len(closes)
    d_high = [0]*n; d_low = [0]*n
    for i in range(n):
        s = max(0, i-252)
        win = closes[s:i+1]
        d_high[i] = (len(win)-1) - int(win.argmax())
        d_low[i] = (len(win)-1) - int(win.argmin())
    df["days_from_high"] = d_high
    df["days_from_low"] = d_low
    df["ma200_dev"] = (df["close"] - df["sma200"]) / df["sma200"] * 100
    if "volume" in df.columns:
        df["turnover_ma20"] = (df["close"] * df["volume"]).rolling(20).mean()
    else:
        df["turnover_ma20"] = np.nan
    return df

# === PER・PBR取得（trailingPE優先＋株価÷EPSでクロスチェック）===
# 注意：yfinanceの.infoは「現在時点のスナップショット」であり過去PERは取得できない。
# 赤字銘柄はtrailingPEがNone/負になるためN/A扱いとし、PBRを併記して判断材料にする。
@st.cache_data(ttl=3600)
def get_per_pbr(ticker):
    """PER・PBRを取得。
    戻り値: (per, pbr, is_estimated) ※is_estimated=Trueは株価÷EPSの手計算フォールバック"""
    try:
        info = yf.Ticker(ticker).info
        per = info.get("trailingPE")
        pbr = info.get("priceToBook")
        eps = info.get("trailingEps")
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        is_estimated = False
        # trailingPEが欠損 or 異常値なら株価÷実績EPSで再計算
        if (per is None or per <= 0) and eps and price and eps > 0:
            per = price / eps
            is_estimated = True
        if per is not None and per <= 0:
            per = None  # 赤字＝N/A扱い
        return per, pbr, is_estimated
    except Exception:
        return None, None, False

def calc_annual_vol(df):
    """年率ボラティリティ(%)を計算。VIX30時の銘柄選定（45%以上を選ぶ）用。
    直近252営業日の日次リターン標準偏差 × √252"""
    try:
        r = df["close"].pct_change().dropna()
        if len(r) < 60:
            return None
        return float(r.iloc[-252:].std() * np.sqrt(252) * 100)
    except Exception:
        return None

def check_liquidity(df, ticker):
    """20日平均売買代金が閾値以上か判定。日本株1億円/日・米国株10億円/日。
    戻り値: (売買代金, 閾値以上か, 通貨記号)"""
    try:
        to = df["turnover_ma20"].iloc[-1]
        if pd.isna(to):
            return None, None, ""
        is_jp = (".T" in ticker) or ticker.startswith("^N")
        thr = 100_000_000 if is_jp else 1_000_000_000
        sym = "¥" if is_jp else "$"
        return float(to), bool(to >= thr), sym
    except Exception:
        return None, None, ""

def calc_bottom_score(r):
    checks = [
        ("RSI≤30（日足）", bool(pd.notna(r["rsi"]) and r["rsi"] <= 30), f"現在{r['rsi']:.1f}" if pd.notna(r["rsi"]) else "-"),
        ("BB下限タッチ", bool(pd.notna(r["bb_lower"]) and r["close"] <= r["bb_lower"]*1.05), ""),
        ("MA25を下回る", bool(pd.notna(r["sma25"]) and r["close"] < r["sma25"]), ""),
        ("MA200を下回る", bool(pd.notna(r["sma200"]) and r["close"] < r["sma200"]), ""),
        ("MACDヒスト<0", bool(pd.notna(r["macd_hist"]) and r["macd_hist"] < 0), ""),
        ("高値から-30%以上", bool(r["drawdown_pct"] <= -30), f"現在{r['drawdown_pct']:.1f}%"),
        ("高値から60日以上", bool(r["days_from_high"] >= 60), f"現在{int(r['days_from_high'])}日"),
        ("週足RSI≤30", bool(pd.notna(r["w_rsi"]) and r["w_rsi"] <= 30), f"現在{r['w_rsi']:.1f}" if pd.notna(r["w_rsi"]) else "-"),
        ("52週安値から±5%以内", bool(r["rally_pct"] <= 5), f"現在+{r['rally_pct']:.1f}%"),
        ("MA200から-20%以上乖離", bool(pd.notna(r["ma200_dev"]) and r["ma200_dev"] <= -20), f"現在{r['ma200_dev']:.1f}%" if pd.notna(r["ma200_dev"]) else "-"),
    ]
    return sum(1 for _,ok,_ in checks if ok), checks

def calc_top_score(r):
    checks = [
        ("RSI≥70（日足）", bool(pd.notna(r["rsi"]) and r["rsi"] >= 70), f"現在{r['rsi']:.1f}" if pd.notna(r["rsi"]) else "-"),
        ("BB上限タッチ", bool(pd.notna(r["bb_upper"]) and r["close"] >= r["bb_upper"]*0.95), ""),
        ("MA25を上回る", bool(pd.notna(r["sma25"]) and r["close"] > r["sma25"]), ""),
        ("MA200を上回る", bool(pd.notna(r["sma200"]) and r["close"] > r["sma200"]), ""),
        ("MACDヒスト>0", bool(pd.notna(r["macd_hist"]) and r["macd_hist"] > 0), ""),
        ("安値から+50%以上", bool(r["rally_pct"] >= 50), f"現在+{r['rally_pct']:.1f}%"),
        ("安値から60日以上", bool(r["days_from_low"] >= 60), f"現在{int(r['days_from_low'])}日"),
        ("MA200から+30%以上乖離", bool(pd.notna(r["ma200_dev"]) and r["ma200_dev"] >= 30), f"現在{r['ma200_dev']:.1f}%" if pd.notna(r["ma200_dev"]) else "-"),
        ("週足RSI≥70", bool(pd.notna(r["w_rsi"]) and r["w_rsi"] >= 70), f"現在{r['w_rsi']:.1f}" if pd.notna(r["w_rsi"]) else "-"),
    ]
    return sum(1 for _,ok,_ in checks if ok), checks

def calc_weekly_bottom_score(df):
    """週足バーで大底10条件を計算（検証2026-07-03：週足<5は足切り・7-8は資金厚めの材料・9は満点警戒）。
    完成した週足バーのみ使用（進行中の週は除外＝ルックアヘッド防止）。上位足チェックは月足RSI≤30。
    戻り値: (週足スコア, 週足フル判定可能か)"""
    try:
        c = df["close"].resample("W-FRI").last().dropna()
        if len(c) < 60:
            return None, False
        # 進行中の週を除外（最新バーの金曜が未来or今日なら落とす）
        last_fri = c.index[-1]
        if last_fri.normalize() >= pd.Timestamp.now().normalize():
            c = c.iloc[:-1]
        if len(c) < 60:
            return None, False
        w = pd.DataFrame({"close": c})
        w["sma25"] = w["close"].rolling(25).mean()
        w["sma200"] = w["close"].rolling(200).mean()
        d = w["close"].diff()
        g = d.clip(lower=0).rolling(14).mean()
        l = (-d.clip(upper=0)).rolling(14).mean()
        w["rsi"] = 100 - (100/(1+g/l))
        mid = w["close"].rolling(20).mean()
        sd = w["close"].rolling(20).std()
        w["bb_lower"] = mid - 2*sd
        e12 = w["close"].ewm(span=12).mean()
        e26 = w["close"].ewm(span=26).mean()
        w["macd_hist"] = (e12-e26) - (e12-e26).ewm(span=9).mean()
        w["roll_high"] = w["close"].rolling(52, min_periods=1).max()
        w["roll_low"] = w["close"].rolling(52, min_periods=1).min()
        w["dd"] = (w["close"]-w["roll_high"])/w["roll_high"]*100
        w["rally"] = (w["close"]-w["roll_low"])/w["roll_low"]*100
        vals = w["close"].values
        n = len(vals)
        wfh = [0]*n
        for i in range(n):
            win = vals[max(0,i-52):i+1]
            wfh[i] = (len(win)-1) - int(win.argmax())
        w["wfh"] = wfh
        w["dev"] = (w["close"]-w["sma200"])/w["sma200"]*100
        m = df["close"].resample("ME").last().dropna()
        md = m.diff()
        mg = md.clip(lower=0).rolling(14).mean()
        ml = (-md.clip(upper=0)).rolling(14).mean()
        m_rsi = (100 - (100/(1+mg/ml))).reindex(w.index, method="ffill")
        w["m_rsi"] = m_rsi
        r = w.iloc[-1]
        score = 0
        score += 1 if (pd.notna(r["rsi"]) and r["rsi"] <= 30) else 0
        score += 1 if (pd.notna(r["bb_lower"]) and r["close"] <= r["bb_lower"]*1.05) else 0
        score += 1 if (pd.notna(r["sma25"]) and r["close"] < r["sma25"]) else 0
        score += 1 if (pd.notna(r["sma200"]) and r["close"] < r["sma200"]) else 0
        score += 1 if (pd.notna(r["macd_hist"]) and r["macd_hist"] < 0) else 0
        score += 1 if (r["dd"] <= -30) else 0
        score += 1 if (r["wfh"] >= 12) else 0
        score += 1 if (pd.notna(r["m_rsi"]) and r["m_rsi"] <= 30) else 0
        score += 1 if (r["rally"] <= 5) else 0
        score += 1 if (pd.notna(r["dev"]) and r["dev"] <= -20) else 0
        w_full = pd.notna(r["sma200"])
        return score, bool(w_full)
    except Exception:
        return None, False

@st.cache_data(ttl=3600)
def scan_all():
    results = []
    for label, tk in ALL_TICKERS:
        try:
            d = load_data(tk, "5y")
            if d is None:
                continue
            bs, _ = calc_bottom_score(d.iloc[-1])
            ts, _ = calc_top_score(d.iloc[-1])
            results.append((label, tk, bs, ts))
        except Exception:
            continue
    return results

# === フル点灯（大底10/10・天井9/9）の履歴を全銘柄ぶん集計（直近1年）===
@st.cache_data(ttl=3600)
def scan_full_history(days_back=365):
    """全登録銘柄について、直近days_back日のフル点灯（大底10/10・天井9/9）を集める。
    連続点灯はクラスタ化して1イベント1行にまとめる。各クラスタは点灯した最初の日を代表とする。"""
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days_back)
    events = []  # (date, label, ticker, kind, is_held)
    for label, tk in ALL_TICKERS:
        try:
            d = load_data(tk, "2y")
            if d is None:
                continue
            raw_b = []
            raw_t = []
            for idx in range(260, len(d)):
                r = d.iloc[idx]
                dt = d.index[idx]
                if dt < cutoff:
                    continue
                # 早期スキップ：フル点灯は必須条件を満たさない日は数学的に不可能
                # 大底10/10にはRSI≤30が必須、天井9/9にはRSI≥70が必須
                rsi_v = r["rsi"]
                can_bottom = pd.notna(rsi_v) and rsi_v <= 30
                can_top = pd.notna(rsi_v) and rsi_v >= 70
                if not can_bottom and not can_top:
                    continue
                if can_bottom:
                    bs, _ = calc_bottom_score(r)
                    if bs >= 10:
                        raw_b.append(idx)
                if can_top:
                    ts, _ = calc_top_score(r)
                    if ts >= 9:
                        raw_t.append(idx)
            def clusterize(raw):
                if not raw:
                    return []
                clusters = []
                cur = [raw[0]]
                for x in raw[1:]:
                    if x - cur[-1] <= 10:
                        cur.append(x)
                    else:
                        clusters.append(cur)
                        cur = [x]
                clusters.append(cur)
                return [c[0] for c in clusters]
            is_held = tk in HELD_TICKERS
            for idx in clusterize(raw_b):
                events.append((d.index[idx], label, tk, "大底10/10", is_held))
            for idx in clusterize(raw_t):
                events.append((d.index[idx], label, tk, "天井9/9", is_held))
        except Exception:
            continue
    events.sort(key=lambda e: e[0], reverse=True)
    return events
# === モメンタムシグナル一覧（expander展開時のみ計算）===
@st.cache_data(ttl=3600)
def scan_momentum():
    """全登録銘柄のモメンタム判定を集計。判定に必要なのは6ヶ月上昇率とMA200のみなので
    2yデータで十分（maxと結果は完全同一・速度のみ向上）。
    戻り値: (買いリスト, 売りリスト)。各要素=(label, ticker, 6ヶ月上昇率, is_held)"""
    buys, sells = [], []
    for label, tk in ALL_TICKERS:
        if tk in ("^VIX", "^TNX"):
            continue
        try:
            d = load_data(tk, "2y")
            if d is None or len(d) < 200:
                continue
            c = d["close"]
            ma200 = c.rolling(200).mean().iloc[-1]
            price = c.iloc[-1]
            if pd.isna(ma200) or len(c) < 127:
                continue
            ret_6m = (price - c.iloc[-127]) / c.iloc[-127] * 100
            is_held = tk in HELD_TICKERS
            if ret_6m >= 50 and price > ma200:
                buys.append((label, tk, ret_6m, is_held))
            elif price < ma200:
                sells.append((label, tk, ret_6m, is_held))
        except Exception:
            continue
    buys.sort(key=lambda x: -x[2])          # 上昇率の高い順
    sells.sort(key=lambda x: (not x[3]))    # 保有を先頭に
    return buys, sells

# トレンドラインが効かない銘柄（暗号資産・高ボラ株）。これらはトレンド方向フィルター対象外
TREND_EXCLUDE = {"COIN","MSTR","MARA","CLSK","RIOT","BTDR","SOXL","QS","SOFI"}

@st.cache_data(ttl=3600)
def monthly_trend_direction(ticker, period="max"):
    """月足の移動チャネル（窓18ヶ月・相関0.3以上）で、直近のトレンド方向を判定。
    戻り値: 'up'（上昇）/ 'down'（下降）/ 'range'（レンジ）/ None（対象外・データ不足）
    検証結果：上昇トレンド中の大底はEV+34.8%・勝率47%（フィルター無し+19.7%より+15pt改善、前半後半とも成立=頑健）"""
    if ticker in TREND_EXCLUDE:
        return None  # 暗号資産・高ボラ株はトレンドライン無効
    try:
        d = load_data(ticker, period)
        if d is None:
            return None
        s = d["close"].resample("ME").last().dropna()
        vals = s.values
        window = 18
        if len(vals) < window + 1:
            return None
        seg = vals[-window:]
        x = np.arange(len(seg))
        corr = np.corrcoef(x, seg)[0, 1]
        a, _ = np.polyfit(x, seg, 1)
        slope_pct = a / seg.mean() * 100
        if abs(corr) < 0.3:
            return "range"
        if slope_pct > 0.5:
            return "up"
        if slope_pct < -0.5:
            return "down"
        return "range"
    except Exception:
        return None

# === (え) モメンタム判定 ===
# 検証：暗号資産・高ボラ株で「過去6ヶ月+50%上昇かつMA200より上」が買い、「MA200割れ」が売り
# 全銘柄でフラットに表示（効かない銘柄も含めて経験として学ぶ方針）
@st.cache_data(ttl=3600)
def momentum_signal(ticker, period="max"):
    """モメンタムシグナルを判定。
    戻り値: 'buy'（過去6ヶ月+50%上昇かつMA200上）/ 'sell'（MA200割れ）/ None（どちらでもない・データ不足）"""
    try:
        d = load_data(ticker, period)
        if d is None:
            return None
        c = d["close"]
        if len(c) < 200:
            return None
        ma200 = c.rolling(200).mean().iloc[-1]
        price = c.iloc[-1]
        if pd.isna(ma200):
            return None
        # 過去6ヶ月（126営業日）の上昇率
        if len(c) < 127:
            return None
        ret_6m = (price - c.iloc[-127]) / c.iloc[-127] * 100
        # 買い：6ヶ月+50%上昇 かつ MA200より上
        if ret_6m >= 50 and price > ma200:
            return "buy"
        # 売り：MA200を割れた
        if price < ma200:
            return "sell"
        return None
    except Exception:
        return None

def calc_ret_6m(df):
    """6ヶ月（126営業日）上昇率。サマリー出力にモメンタムの実数を載せる用"""
    try:
        c = df["close"]
        if len(c) < 127:
            return None
        return float((c.iloc[-1] - c.iloc[-127]) / c.iloc[-127] * 100)
    except Exception:
        return None

# === (お) ダイバージェンス判定 ===
# 強気ダイバージェンス＝株価は安値更新だがRSI(14)は切り上げ かつ RSI<45
# 検証：月足=勝率79%（超強気の買い場サイン）、日足=勝率74%（補助）。週足は日足と大差なく不採用
# 重要：「待つサイン」ではなく「もう底・買い場のサイン」
def _rsi_series(c, period=14):
    d = c.diff()
    g = d.clip(lower=0).rolling(period).mean()
    l = (-d.clip(upper=0)).rolling(period).mean()
    return 100 - (100 / (1 + g / l))

def _detect_divergence(s):
    """直近で強気ダイバージェンスが発生しているか判定。発生していればTrue"""
    r = _rsi_series(s)
    vals = s.values
    rvals = r.values
    n = len(vals)
    if n < 30:
        return False
    w = 3
    lows = []
    for i in range(max(w, n - 60), n - w):  # 直近60本以内の局所安値
        if vals[i] == vals[i - w:i + w + 1].min():
            lows.append(i)
    for k in range(1, len(lows)):
        ip, ic = lows[k - 1], lows[k]
        if np.isnan(rvals[ip]) or np.isnan(rvals[ic]):
            continue
        # 株価は安値更新（下げ）だがRSIは切り上げ かつ RSI<45
        if vals[ic] < vals[ip] and rvals[ic] > rvals[ip] and rvals[ic] < 45:
            return True
    return False

@st.cache_data(ttl=3600)
def divergence_signals(ticker, period="max"):
    """月足・日足の強気ダイバージェンスを判定。
    戻り値: dict {'monthly': bool, 'daily': bool}"""
    result = {"monthly": False, "daily": False}
    try:
        d = load_data(ticker, period)
        if d is None:
            return result
        c = d["close"]
        # 日足
        result["daily"] = _detect_divergence(c)
        # 月足
        sm = c.resample("ME").last().dropna()
        result["monthly"] = _detect_divergence(sm)
    except Exception:
        pass
    return result

# === ここぞ判定（最強条件アラート用）===
# 検証で最強だった3つの強化条件：VIX30以上(EV+56%)・高ボラ(暗号資産EV+67%)・月足ダイバージェンス(勝率79%)
# 大底8以上を必須に、3つ揃う=案A(🔥確定演出)、2つ揃う=案B(⭐ここぞ)
@st.cache_data(ttl=3600)
def is_high_vol(ticker, period="5y"):
    """直近20日ボラが60日平均より高いか"""
    try:
        d = load_data(ticker, period)
        if d is None:
            return False
        c = d["close"]
        vol20 = c.pct_change().rolling(20).std()
        vol_ma = vol20.rolling(60).mean()
        v, vm = vol20.iloc[-1], vol_ma.iloc[-1]
        if pd.isna(v) or pd.isna(vm):
            return False
        return bool(v > vm)
    except Exception:
        return False

@st.cache_data(ttl=3600)
def get_vix_level():
    """現在のVIX水準を取得"""
    try:
        d = load_data("^VIX", "5y")
        return float(d["close"].iloc[-1]) if d is not None else None
    except Exception:
        return None

def check_strongest(scan):
    """大底8以上の銘柄で最強条件を判定。検証結果(2026-06-24)に基づきVIX30+高ボラベース。
    検証：2条件の正体は「VIX30+高ボラ」(173回EV+45%・暗号資産+84%)、月足ダイバはここぞ判定には不要
    (VIX30+月足ダイバは0回・高ボラ+月足ダイバはVIX30無しで-9.8%)。
    🔥確定演出=大底8+VIX30+高ボラ(両方)、⭐ここぞ=大底8+どちらか1つ。
    戻り値: (case_a=確定演出リスト, case_b=ここぞリスト)。各要素=(label,tk,bs,is_held,揃った条件名リスト)"""
    vix = get_vix_level()
    vix30 = (vix is not None and vix >= 30)
    case_a, case_b = [], []
    for label, tk, bs, ts in scan:
        if bs < 8 or tk in ("^VIX", "^TNX"):
            continue
        conds = []
        if vix30:
            conds.append("VIX30")
        if is_high_vol(tk):
            conds.append("高ボラ")
        is_held = tk in HELD_TICKERS
        if len(conds) >= 2:        # VIX30 + 高ボラ = 本物のここぞ
            case_a.append((label, tk, bs, is_held, conds))
        elif len(conds) == 1:      # どちらか片方
            case_b.append((label, tk, bs, is_held, conds))
    return case_a, case_b

st.title("📈 大底・天井スコア")
st.caption("大底10条件・天井9条件 | 買い:スコア9+ 売り:天井8+")

# === 更新ボタン（放置でフリーズ・文字が白くなる対策）===
# 押すとキャッシュを全クリアして最新データで再実行する
if st.button("🔄 データ更新（最新の株価を取り直す）", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

with st.expander("📖 運用ルール（必ず確認）"):
    st.markdown("""
**シグナル点灯時**: まず売買せずClaudeに相談。買いは3分割(0/+15/+30営業日)各1/3、TP+50%/SL-15%/最大180日。売りは半分利確＋残りに逆指値(高値-8〜10%)。
**集中リスク**: 暗号資産系(COIN/MSTR/MARA/CLSK)は1銘柄まで。半導体系(NVDA/SOXL/AMD)も1銘柄まで。
**未検証(⚠️)**: SOFIは売買対象外・参考表示のみ。上場4年未満も対象外。
**検証済(対象外)**: SOXL/QSは検証完了だが売買対象外。SOXL=レバETFゆえ🔥確定演出級のみC枠SL必須・VIX<25の点灯は無視。QS=赤字構造でSTEP2弾き・買い筋はファンダ好材料のみ・VIX高は罠。
**MP（レアアース）**: 通常より厳しい買い条件＝大底9＋月足トレンドup＋できればVIX25以上。月足downなら落ちるナイフ扱いで見送り。
**ボーナス資金**: 指数9/10+の歴史的局面のみ。投信積立は不変、追加資金は暗号資産以外(XLE/EWZ/SLV/AMD等)優先。
**銘柄の保有/監視の移動**: 売買したらClaudeに相談ついでに伝えてコードを直してもらう運用。
""")

with st.spinner("登録銘柄をスキャン中（初回は20秒ほど）..."):
    scan = scan_all()

# === 最上段：ここぞアラート（VIX30+高ボラ＝検証で最強の局面）===
# 🔥確定演出=大底8+VIX30+高ボラ(両方・EV+45%/暗号資産+84%・歴史的暴落の底)、⭐ここぞ=大底8+片方
# フォント=Mochiy Pop One(Google Fonts・丸字ポップ)。確定演出は迫力を残し小さめ、ここぞは相談を促す控えめ表示
case_a, case_b = check_strongest(scan)
_FONT_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Mochiy+Pop+One&display=swap');
.kakutei-box{background:linear-gradient(135deg,#3a0a0a,#6e1010);border:1.5px solid #ff4040;
 border-radius:9px;padding:9px 12px;margin-bottom:6px;box-shadow:0 0 10px rgba(255,50,50,0.4);
 font-family:'Mochiy Pop One',sans-serif;}
.kakutei-ttl{font-size:17px;color:#fff;text-shadow:0 0 6px #ff4040;margin-bottom:3px;}
.kakutei-bdy{font-size:12px;line-height:1.45;color:#ffd8d8;}
.kakutei-ev{color:#ffd040;}
.kokozo-box{background:#2c2607;border:1px solid #b89020;border-radius:7px;
 padding:7px 11px;margin-bottom:6px;font-family:'Mochiy Pop One',sans-serif;}
.kokozo-ttl{font-size:13px;color:#e8d28a;margin-bottom:2px;}
.kokozo-bdy{font-size:11px;line-height:1.4;color:#cabb80;}
.held-tag{background:#1a4a2a;color:#5fe;font-size:10px;padding:0 5px;border-radius:3px;margin-right:4px;}
</style>"""
if case_a or case_b:
    parts = [_FONT_CSS]
    for label, tk, bs, is_held, conds in case_a:
        hm = '<span class="held-tag">保有</span>' if is_held else ""
        parts.append(f'<div class="kakutei-box"><div class="kakutei-ttl">🔥 確定演出：{hm}{label}</div>'
            f'<div class="kakutei-bdy">VIX30＋高ボラが揃った（大底{bs}）→ 歴史的暴落の底。'
            f'<span class="kakutei-ev">検証EV+45%(暗号資産+84%)</span>。損切りライン決めて即行動を検討！</div></div>')
    for label, tk, bs, is_held, conds in case_b:
        hm = '<span class="held-tag">保有</span>' if is_held else ""
        other = '高ボラ' if 'VIX30' in conds else 'VIX30'
        parts.append(f'<div class="kokozo-box"><div class="kokozo-ttl">⭐ ここぞ：{hm}{label}</div>'
            f'<div class="kokozo-bdy">大底{bs}＋{" ＋ ".join(conds)} → もう片方({other})も揃えば確定演出。相談して検討</div></div>')
    st.markdown("".join(parts), unsafe_allow_html=True)
    if case_a:
        st.toast("🔥 確定演出！買い場確定！", icon="🔥")
    st.divider()

# === フル点灯チェック（最上段の特大警告用）===
full_bottom = []  # (label, ticker, score, is_held)
full_top = []
for label, tk, bs, ts in scan:
    if bs >= 10:
        full_bottom.append((label, tk, bs, tk in HELD_TICKERS))
    if ts >= 9:
        full_top.append((label, tk, ts, tk in HELD_TICKERS))

# 最上段：フル点灯の特大警告（保有銘柄は特に強調）
if full_bottom or full_top:
    has_held = any(h for *_, h in full_bottom) or any(h for *_, h in full_top)
    if has_held:
        st.markdown("# 🚨🚨 保有銘柄がフル点灯中 🚨🚨")
    else:
        st.markdown("# 🚨 フル点灯中 🚨")

    def render_full(items, emoji, kind_label):
        held = [x for x in items if x[3]]
        others = [x for x in items if not x[3]]
        for label, tk, score, is_held in held + others:
            if is_held:
                st.error(f"## {emoji}【保有】{label} {kind_label}（{score}点満点）→ 売買をClaudeに相談")
            else:
                st.error(f"### {emoji}{label} {kind_label}（{score}点満点）")

    render_full(full_bottom, "💎", "大底フル点灯")
    render_full(full_top, "⛔", "天井フル点灯")
    st.divider()

alerts = []
for label, tk, bs, ts in scan:
    # 短縮表示用に銘柄記号だけ抽出（"BABA（アリババ…）"→"BABA"）。日本株は.Tを除去
    short = label.split("（")[0].strip()
    if short == "" or short.startswith("📁"):
        short = tk.replace(".T", "")
    vix_b = "（VIX底=楽観・天井警戒）" if tk == "^VIX" else ""
    vix_t = "（VIX天井=恐怖最大=買い場）" if tk == "^VIX" else ""
    # フル点灯は上で特大表示済みなので、ここではフル未満を従来通り表示
    if bs == 9:
        alerts.append(("error", f"🟢{short}買い{bs}{vix_b}"))
    elif bs == 8:
        alerts.append(("warning", f"⚠️{short}買いゾーン{bs}{vix_b}"))
    if ts == 8:
        alerts.append(("error", f"🔴{short}売り{ts}{vix_t}"))
    elif ts == 7:
        alerts.append(("warning", f"⚠️{short}天井警戒{ts}{vix_t}"))

if alerts:
    # 見出しを0.8倍に縮小（iPhoneで2行→1行に収める）
    st.markdown("<div style='font-size:0.8em;font-weight:700;margin:4px 0;'>🚨 シグナル点灯中（フル未満）</div>", unsafe_allow_html=True)
    for kind, msg in alerts:
        if kind == "error":
            st.error(msg)
        else:
            st.warning(msg)
elif not (full_bottom or full_top):
    st.success(f"✅ 本日のシグナルなし（{len(scan)}銘柄スキャン済み）")
# === モメンタムシグナル一覧（折りたたみ・買い/売りの2枠）===
with st.expander("🚀 モメンタムシグナル一覧（タップで開く｜買い=6ヶ月+50%かつMA200上／売り=MA200割れ）"):
    with st.spinner("モメンタム判定中..."):
        mom_buys, mom_sells = scan_momentum()
    st.markdown("#### 🚀 モメンタム買い点灯中")
    if mom_buys:
        for label, tk, r6, is_held in mom_buys:
            hm = "【保有】" if is_held else ""
            st.markdown(f"- {hm}**{label}**　6ヶ月 **{r6:+.0f}%**　（MA200上）")
        st.caption("3銘柄分散・1銘柄約3万円で検討。買う買わないは都度判断。")
    else:
        st.caption("モメンタム買いの点灯はなしなのだ。")
    st.markdown("#### 📉 モメンタム売り点灯中（MA200割れ＝トレンド終了）")
    if mom_sells:
        for label, tk, r6, is_held in mom_sells:
            hm = "【保有】" if is_held else ""
            if is_held:
                st.error(f"{hm}**{label}**　6ヶ月 {r6:+.0f}%　→ モメンタム保有なら売り検討")
            else:
                st.markdown(f"- {label}　6ヶ月 {r6:+.0f}%")
    else:
        st.caption("モメンタム売りの点灯はなしなのだ。")

# === フル点灯の履歴（折りたたみ・直近1年・保有銘柄を強調）===
with st.expander("🏆 フル点灯の履歴（直近1年・大底10/10・天井9/9のみ）"):
    st.caption("多忙・体調不良で見逃した時の回収用。保有銘柄を最上部に強調表示。")
    with st.spinner("履歴を集計中..."):
        full_events = scan_full_history(365)
    if not full_events:
        st.info("直近1年でフル点灯（満点）はなかったのだ。")
    else:
        held_events = [e for e in full_events if e[4]]
        other_events = [e for e in full_events if not e[4]]
        # 枠1：保有銘柄（直近1年すべて）
        st.markdown("#### ⭐ 保有銘柄のフル点灯（直近1年）")
        if held_events:
            for dt, label, tk, kind, _ in held_events:
                mark = "💎" if "大底" in kind else "⛔"
                st.markdown(f"- **{dt.strftime('%Y-%m-%d')}**　{mark} **{label}**　{kind}")
        else:
            st.caption("保有銘柄のフル点灯はなかったのだ。")
        # 枠2：それ以外の銘柄（直近10件だけ）
        st.markdown("#### 監視・その他銘柄のフル点灯（直近10件）")
        if other_events:
            for dt, label, tk, kind, _ in other_events[:10]:
                mark = "💎" if "大底" in kind else "⛔"
                st.markdown(f"- {dt.strftime('%Y-%m-%d')}　{mark} {label}　{kind}")
            if len(other_events) > 10:
                st.caption(f"（ほか{len(other_events)-10}件は省略。直近10件のみ表示）")
        else:
            st.caption("該当なしなのだ。")

st.divider()

col_g, col_t = st.columns([1,2])
with col_g:
    group_name = st.radio("グループ", list(GROUPS.keys()))
with col_t:
    ticker_name = st.radio("銘柄を選択", list(GROUPS[group_name].keys()))

# === 直接入力＋✖️クリアボタン ===
# 文字が残ると登録銘柄の選択を上書きし続けるため、ワンタップで消せるようにした
col_in, col_x = st.columns([5,1])
with col_in:
    st.text_input("直接入力（米国株:AAPL / 日本株:4桁数字でOK 例:7203）", key="custom_ticker")
with col_x:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("✖️", key="clear_custom", help="入力をクリアして登録銘柄の表示に戻す"):
        st.session_state["custom_ticker"] = ""
        st.rerun()

_c = st.session_state.get("custom_ticker", "").strip()
ticker = (_c + ".T" if _c.isdigit() and len(_c) == 4 else _c.upper()) if _c else GROUPS[group_name][ticker_name]
period = st.radio("データ期間（スコア計算用・5y推奨）", ["2y","5y","10y","max"], index=1, horizontal=True)

if _c:
    st.warning("⚠️ 直接入力銘柄は未検証です。スコアは参考表示のみとし、売買前に検証を依頼してください。（✖️で入力をクリアすると登録銘柄に戻る）")
with st.spinner("データ取得中..."):
    df = load_data(ticker, period)

if df is None:
    st.error("データ不足です。期間を長くするかティッカーを確認してください（最低260営業日必要）。")
    st.stop()

latest = df.iloc[-1]
prev = df.iloc[-2]
change = float(latest["close"]) - float(prev["close"])
change_pct = change / float(prev["close"]) * 100
symbol = "¥" if (".T" in ticker or ticker.startswith("^N")) else "$"

bottom_score, bottom_checks = calc_bottom_score(latest)
top_score, top_checks = calc_top_score(latest)
w_score, _ = calc_weekly_bottom_score(df)

st.markdown(f"### {ticker}")
c1,c2,c3,c4 = st.columns(4)
c1.metric("現在値", f"{symbol}{float(latest['close']):,.2f}", f"{change:+,.2f}（{change_pct:+.2f}%）")
c2.metric("日足RSI / 週足RSI", f"{float(latest['rsi']):.1f} / {float(latest['w_rsi']):.1f}" if pd.notna(latest['w_rsi']) else f"{float(latest['rsi']):.1f} / -")
c3.metric("大底スコア", f"{bottom_score}/10")
c4.metric("天井スコア", f"{top_score}/9")

# === PER・PBR表示 ===
# 赤字銘柄はPERがN/Aになるため、PBRを併記して判断材料にする（点灯記録ログの記法と統一）
_per, _pbr, _per_est = get_per_pbr(ticker)
_per_txt = (f"{_per:.1f}倍" + ("（株価÷EPS概算）" if _per_est else "")) if _per else "N/A（赤字 or 取得不可）"
_pbr_txt = f"{_pbr:.2f}倍" if _pbr else "-"
st.caption(f"📐 PER {_per_txt}　｜　PBR {_pbr_txt}　※現在値のスナップショット（過去PERは取得不可）")

if w_score is not None:
    if w_score >= 5:
        st.caption(f"📅 週足スコア {w_score}/10（日足={bottom_score}）｜7-8=資金厚めの材料・9は満点警戒。日足シグナルの確認バッジ")
    else:
        st.caption(f"💧 週足スコア {w_score}/10（日足={bottom_score}）｜週足<5=浅い底で見送り寄り")
_to, _liq, _tsym = check_liquidity(df, ticker)
if _to is not None:
    _to_disp = f"{_to/1e8:.1f}億" if _tsym == "¥" else f"{_to/1e6:.0f}百万"
    if _liq:
        st.caption(f"💰 20日平均売買代金 {_tsym}{_to_disp}/日｜流動性OK（テクニカルが機能する水準）")
    else:
        st.caption(f"💧 20日平均売買代金 {_tsym}{_to_disp}/日｜薄商い（テクニカルがダマシになりやすい・7325型）")

_p = float(latest["close"])
st.caption(f"🎯 今買うなら｜損切り-15%＝{symbol}{_p*0.85:,.2f}｜+50%＝{symbol}{_p*1.5:,.2f}｜+100%＝{symbol}{_p*2:,.2f}｜+300%＝{symbol}{_p*4:,.2f}｜+500%＝{symbol}{_p*6:,.2f}（※3分割後は平均取得単価が基準）")

if ticker == "^VIX":
    st.info("ℹ️ VIXは読み替え注意：VIXの天井=恐怖最大=株の買い場 / VIXの底=楽観=株の天井警戒")

if bottom_score >= 10:
    st.error(f"💎🚨 **大底フル点灯（{bottom_score}/10 満点）**")
    t1 = pd.Timestamp.today()
    t2 = (t1 + BDay(15)).strftime("%m/%d")
    t3 = (t1 + BDay(30)).strftime("%m/%d")
    st.markdown(f"""**📋 大底ホームラン戦略（検証済：勝率54% EV+10.4%）**
- 第1回買い: 本日（資金の1/3）
- 第2回買い: {t2}頃（+15営業日、1/3）
- 第3回買い: {t3}頃（+30営業日、1/3）
- 利確: 平均取得単価 **+50%** / 損切: 平均取得単価 **-15%** / 最大保有180日
- ⚠️ ファンダメンタル（事業・財務）の確認を忘れずに""")
elif bottom_score == 9:
    st.error(f"🟢 **買いシグナル点灯（大底スコア{bottom_score}/10）**")
    t1 = pd.Timestamp.today()
    t2 = (t1 + BDay(15)).strftime("%m/%d")
    t3 = (t1 + BDay(30)).strftime("%m/%d")
    st.markdown(f"""**📋 大底ホームラン戦略（検証済：勝率54% EV+10.4%）**
- 第1回買い: 本日（資金の1/3）
- 第2回買い: {t2}頃（+15営業日、1/3）
- 第3回買い: {t3}頃（+30営業日、1/3）
- 利確: 平均取得単価 **+50%** / 損切: 平均取得単価 **-15%** / 最大保有180日
- ⚠️ ファンダメンタル（事業・財務）の確認を忘れずに""")
elif bottom_score == 8:
    st.warning(f"⚠️ 買いゾーン接近（大底スコア{bottom_score}/10）：あと1条件で買いシグナル")
elif bottom_score >= 6:
    st.info(f"📊 大底圏（{bottom_score}/10）：監視継続")

# === トレンド方向フィルター（常時表示に変更・閾値撤廃）===
# 検証：上昇トレンド中の大底はEV+34.8%・勝率47%（フィルター無し+19.7%より+15pt改善・前半後半とも成立=頑健）
# 「大局は順張り（上昇トレンド）、エントリーは逆張り（大底）」が最強
# 大底8以上のときは判断材料として大きく表示、それ未満でも地形把握のため常時caption表示する
trend = monthly_trend_direction(ticker)
if bottom_score >= 8:
    if trend == "up":
        st.success("📈 **月足トレンド：上昇中** → 上昇トレンド中の大底はEV+34.8%・勝率47%（最強の買い場）。資金を厚めに検討")
    elif trend == "down":
        st.warning("📉 **月足トレンド：下降中** → 下降トレンド中の大底はEV+12%と弱め。慎重に")
    elif trend == "range":
        st.info("➡️ **月足トレンド：レンジ（方向感なし）** → EV+16%と平凡。様子見も一案")
    else:
        st.caption("ℹ️ この銘柄はトレンド方向フィルター対象外（暗号資産・高ボラ株はトレンドラインが効かないため）")
else:
    _tmap = {"up": "📈 月足トレンド：上昇中（大底点灯時は最強の買い場・EV+34.8%）",
             "down": "📉 月足トレンド：下降中（大底が出ても弱め・EV+12%）",
             "range": "➡️ 月足トレンド：レンジ（方向感なし・EV+16%）"}
    st.caption(_tmap.get(trend, "ℹ️ 月足トレンド：対象外（暗号資産・高ボラ株はトレンドラインが効かない）"))

if top_score >= 9:
    st.error(f"⛔🚨 **天井フル点灯（{top_score}/9 満点）**：保有していれば利確・リスク管理を検討")
elif top_score == 8:
    st.error(f"🔴 **売りシグナル点灯（天井スコア{top_score}/9）**：保有していれば利確・リスク管理を検討")
elif top_score == 7:
    st.warning(f"⚠️ 天井警戒（天井スコア{top_score}/9）")

# === (お) ダイバージェンス表示 ===
# 月足=超強気の買い場サイン（勝率79%）、日足=補助（勝率74%）。「もう底・買い場」の意味
_div = divergence_signals(ticker)
if _div["monthly"]:
    st.success("‼️‼️‼️ **月足ダイバージェンス発生** ‼️‼️‼ → 超強気の買い場サイン（検証勝率79%・最強格）。株価は安値更新だがRSIは底打ち＝もう底が近い。待たずに買い場として検討")
if _div["daily"]:
    st.info("🔎 **日足ダイバージェンス発生** → 「そろそろ底・買い場が近い」の補助サイン（株価は下げているがRSIは下げ渋り）。待つより買い場として意識（取得単価を下げたいなら分割買い）")

# === (え) モメンタムシグナル表示（全銘柄フラット）===
# 買い=6ヶ月+50%上昇かつMA200上、売り=MA200割れ。買う買わないはわさびが都度判断
_mom = momentum_signal(ticker)
if _mom == "buy":
    st.success("🚀 **モメンタム買いシグナル** → 過去6ヶ月+50%以上上昇かつMA200より上（順張りの勢い継続中）。3銘柄分散・1銘柄約3万円で検討")
elif _mom == "sell":
    st.warning("📉 **モメンタム売りシグナル** → MA200を割れた（順張りトレンド終了）。モメンタムで保有していれば売り検討")

with st.expander("📋 スコア詳細（タップで開閉）", expanded=False):
    col_b, col_t2 = st.columns(2)
    with col_b:
        st.markdown(f"**大底スコア {bottom_score}/10**")
        for label, ok, detail in bottom_checks:
            st.markdown(f"{'✅' if ok else '❌'} {label}　{detail}")
    with col_t2:
        st.markdown(f"**天井スコア {top_score}/9**")
        for label, ok, detail in top_checks:
            st.markdown(f"{'✅' if ok else '❌'} {label}　{detail}")

# === 過去のシグナル点灯日を計算（クラスタリングで1山1マーカー。フル点灯は全て個別表示）===
# ※コピー用サマリーでも点灯履歴を使うため、チャートより手前で計算しておく
@st.cache_data(ttl=3600)
def calc_signal_history(_df, ticker_key):
    raw_bottom = []
    raw_top = []
    for idx in range(260, len(_df)):
        r = _df.iloc[idx]
        bs, _ = calc_bottom_score(r)
        ts, _ = calc_top_score(r)
        if bs >= 9:
            raw_bottom.append((idx, _df.index[idx], float(r["close"]), bs))
        if ts >= 8:
            raw_top.append((idx, _df.index[idx], float(r["close"]), ts))

    def clusterize(raw, pick="low", full_thr=None):
        if not raw:
            return []
        # フル点灯（full_thr以上）は集約せず全て個別に残す
        full_days = [(item[1], item[2], item[3]) for item in raw
                     if full_thr is not None and item[3] >= full_thr]
        # フル未満だけクラスタリング対象にする
        sub = [item for item in raw
               if not (full_thr is not None and item[3] >= full_thr)]
        clusters = []
        if sub:
            cur = [sub[0]]
            for item in sub[1:]:
                if item[0] - cur[-1][0] <= 10:
                    cur.append(item)
                else:
                    clusters.append(cur)
                    cur = [item]
            clusters.append(cur)
        result = []
        for c in clusters:
            if pick == "low":
                best = min(c, key=lambda x: x[2])
            else:
                best = max(c, key=lambda x: x[2])
            result.append((best[1], best[2], best[3]))
        # フル点灯を全て加えて日付順にソート
        result.extend(full_days)
        result.sort(key=lambda x: x[0])
        return result

    bottom_days = clusterize(raw_bottom, pick="low", full_thr=10)
    top_days = clusterize(raw_top, pick="high", full_thr=9)
    return bottom_days, top_days

sig_bottoms, sig_tops = calc_signal_history(df, ticker)

# === コピー用サマリー（Claude相談用・画面に出ている情報を全部入り）===
with st.expander("📄 コピー用サマリー（Claude相談用・タップで開く）", expanded=False):
    _vix_now = get_vix_level()
    _ret6 = calc_ret_6m(df)
    _avol = calc_annual_vol(df)

    # ここぞ判定（個別銘柄版・check_strongestと同じロジック）
    _conds = []
    if _vix_now is not None and _vix_now >= 30:
        _conds.append("VIX30")
    if is_high_vol(ticker):
        _conds.append("高ボラ")
    if bottom_score >= 8 and len(_conds) >= 2:
        _kokozo = f"🔥確定演出（{' + '.join(_conds)}）"
    elif bottom_score >= 8 and len(_conds) == 1:
        _kokozo = f"⭐ここぞ（{_conds[0]}のみ）"
    else:
        _kokozo = f"該当なし（成立条件: {'・'.join(_conds) if _conds else 'なし'}）"

    # 週足スコアの帯
    if w_score is None:
        _wtxt = "算出不可"
    elif w_score < 5:
        _wtxt = f"{w_score}/10 💧足切り"
    elif w_score >= 9:
        _wtxt = f"{w_score}/10 ⚠️満点警戒"
    elif w_score >= 7:
        _wtxt = f"{w_score}/10 🎯最良帯"
    else:
        _wtxt = f"{w_score}/10"

    _trend_txt = {"up": "上昇(up)", "down": "下降(down)", "range": "レンジ(range)"}.get(trend, "対象外(暗号資産・高ボラ)")
    _mom_txt = {"buy": "🚀買い", "sell": "📉売り"}.get(_mom, "なし")
    _mom_txt += f"（6ヶ月 {_ret6:+.1f}%）" if _ret6 is not None else ""

    # 大底9以上の点灯履歴（検証4＝初点灯かの判定材料）
    if sig_bottoms:
        _b_dates = [d.strftime("%Y-%m-%d") for d, p, s in sig_bottoms]
        _hist_txt = f"データ期間({period})内 {len(sig_bottoms)}回 / 最終 {_b_dates[-1]}"
        _hist_txt += f" / 初回 {_b_dates[0]}"
    else:
        _hist_txt = f"データ期間({period})内 0回 ← 初点灯なら◎高信頼(的中率99%)"

    if _to is not None:
        _liq_disp = f"{_tsym}{_to/1e8:.1f}億/日" if _tsym == "¥" else f"{_tsym}{_to/1e6:.0f}百万/日"
        _liq_disp += "（流動性OK）" if _liq else "（薄商い・ダマシ注意）"
    else:
        _liq_disp = "取得不可"

    _summary = f"""【{ticker}】{df.index[-1].strftime('%Y-%m-%d')}
株価: {symbol}{_p:,.2f}（{change:+,.2f} / {change_pct:+.2f}%）
PER: {_per_txt} ｜ PBR: {_pbr_txt}
--- スコア ---
大底スコア: {bottom_score}/10
天井スコア: {top_score}/9
週足スコア: {_wtxt}
月足トレンド: {_trend_txt}
ダイバージェンス: 月足={'あり(勝率79%)' if _div['monthly'] else 'なし'} / 日足={'あり(勝率74%)' if _div['daily'] else 'なし'}
モメンタム: {_mom_txt}
ここぞ判定: {_kokozo}
VIX: {f'{_vix_now:.1f}' if _vix_now is not None else '取得不可'}
--- 補助指標 ---
MA200乖離: {f"{latest['ma200_dev']:+.1f}%" if pd.notna(latest['ma200_dev']) else '-'}
下落深度(52週高値から): {latest['drawdown_pct']:.1f}%
高値からの経過: {int(latest['days_from_high'])}日
52週安値から: {latest['rally_pct']:+.1f}%{' ← 新安値更新中' if latest['rally_pct'] <= 5 else ''}
年率ボラ: {f'{_avol:.1f}%' if _avol is not None else '-'}{'（VIX30時の適格ライン45%以上）' if _avol is not None and _avol >= 45 else ''}
売買代金(20日平均): {_liq_disp}
大底9以上の点灯履歴: {_hist_txt}
--- ライン ---
SL-15%: {symbol}{_p*0.85:,.2f}
+50%: {symbol}{_p*1.5:,.2f} / +100%: {symbol}{_p*2:,.2f} / +300%: {symbol}{_p*4:,.2f} / +500%: {symbol}{_p*6:,.2f}"""

    st.code(_summary, language=None)
    st.caption("右上のコピーアイコンで全文コピーできるのだ。そのままClaudeに貼れば相談が一発なのだ。")

tf = st.radio("チャート時間軸", ["日足","週足","月足"], index=0, horizontal=True)

def make_chart_frame(df, tf):
    if tf == "日足":
        cd = pd.DataFrame({
            "open": df["open"], "high": df["high"],
            "low": df["low"], "close": df["close"],
        })
    else:
        rule = "W-FRI" if tf == "週足" else "ME"
        try:
            o = df["open"].resample(rule).first()
            h = df["high"].resample(rule).max()
            lo = df["low"].resample(rule).min()
            c = df["close"].resample(rule).last()
        except ValueError:
            rule = "W-FRI" if tf == "週足" else "M"
            o = df["open"].resample(rule).first()
            h = df["high"].resample(rule).max()
            lo = df["low"].resample(rule).min()
            c = df["close"].resample(rule).last()
        cd = pd.DataFrame({"open": o, "high": h, "low": lo, "close": c}).dropna(subset=["close"])
    cd["sma25"] = cd["close"].rolling(25).mean()
    cd["sma75"] = cd["close"].rolling(75).mean()
    cd["sma200"] = cd["close"].rolling(200).mean()
    delta = cd["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    cd["rsi"] = 100 - (100/(1+gain/loss))
    cd["bb_mid"] = cd["close"].rolling(20).mean()
    s = cd["close"].rolling(20).std()
    cd["bb_upper"] = cd["bb_mid"] + 2*s
    cd["bb_lower"] = cd["bb_mid"] - 2*s
    e12 = cd["close"].ewm(span=12).mean()
    e26 = cd["close"].ewm(span=26).mean()
    cd["macd"] = e12 - e26
    cd["macd_signal"] = cd["macd"].ewm(span=9).mean()
    cd["macd_hist"] = cd["macd"] - cd["macd_signal"]
    return cd

cframe = make_chart_frame(df, tf)

show_signals = st.checkbox("📍 過去のシグナル点灯位置をチャートに表示", value=True,
    help="日足で大底9以上/天井8以上が点灯した日を価格チャート上に▲▼(フル点灯は💎⛔)で表示")
show_hlines = st.checkbox("➖ 過去高値/安値の水平ラインを表示", value=False,
    help="意識されやすい過去の高値(赤)・安値(水色)に水平線を引く")
show_legend = st.checkbox("🏷️ チャート上部の線の説明（凡例）を表示", value=False)

period_options = {"6ヶ月":180,"1年":365,"2年":730,"全期間":99999}
disp = st.radio("表示期間", list(period_options.keys()), index=1, horizontal=True)
days = period_options[disp]
chart_df = cframe if days >= 99999 else cframe[cframe.index >= pd.Timestamp.now() - pd.Timedelta(days=days)]
if len(chart_df) < 5:
    chart_df = cframe

fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                    row_heights=[0.55,0.25,0.20], vertical_spacing=0.03)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["bb_upper"],
    line=dict(color="rgba(100,100,255,0.2)",width=1), showlegend=False), row=1, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["bb_lower"],
    fill="tonexty", fillcolor="rgba(100,100,255,0.05)",
    line=dict(color="rgba(100,100,255,0.2)",width=1), showlegend=False), row=1, col=1)
fig.add_trace(go.Candlestick(x=chart_df.index,
    open=chart_df["open"], high=chart_df["high"],
    low=chart_df["low"], close=chart_df["close"],
    name="株価", increasing_line_color="#ef4444", decreasing_line_color="#3a8fff",
    increasing_fillcolor="#ef4444", decreasing_fillcolor="#3a8fff",
    line=dict(width=1)), row=1, col=1)

# === 過去高値/安値の水平ライン（意識される価格帯）===
if show_hlines and len(chart_df) > 20:
    piv_w = 15
    cl = chart_df["close"].values
    highs = []
    lows = []
    for i in range(piv_w, len(cl)-piv_w):
        win = cl[i-piv_w:i+piv_w+1]
        if cl[i] == win.max():
            highs.append(cl[i])
        if cl[i] == win.min():
            lows.append(cl[i])
    def thin(levels, n=4):
        if not levels:
            return []
        levels = sorted(set(round(v,2) for v in levels))
        if len(levels) <= n:
            return levels
        step = len(levels) / n
        return [levels[int(k*step)] for k in range(n)]
    for lv in thin(highs):
        fig.add_hline(y=lv, line_dash="dot", line_color="rgba(244,63,94,0.75)",
                      line_width=1.5, row=1, col=1)
    for lv in thin(lows):
        fig.add_hline(y=lv, line_dash="dot", line_color="rgba(34,211,238,0.75)",
                      line_width=1.5, row=1, col=1)

if show_signals:
    x_min = chart_df.index.min()
    x_max = chart_df.index.max()
    # フル点灯(大底10/天井9)とそれ未満を分離。フルは💎⛔、未満は▲▼
    b_reg = [(d,p,s) for d,p,s in sig_bottoms if x_min <= d <= x_max and s < 10]
    b_full = [(d,p,s) for d,p,s in sig_bottoms if x_min <= d <= x_max and s >= 10]
    t_reg = [(d,p,s) for d,p,s in sig_tops if x_min <= d <= x_max and s < 9]
    t_full = [(d,p,s) for d,p,s in sig_tops if x_min <= d <= x_max and s >= 9]
    if b_reg:
        fig.add_trace(go.Scatter(x=[d for d,p,s in b_reg], y=[p for d,p,s in b_reg],
            mode="markers", name="大底点灯",
            marker=dict(symbol="triangle-up", size=11, color="#22d3ee",
                        line=dict(color="white", width=1)),
            text=[f"大底{s}/10" for d,p,s in b_reg], hoverinfo="text+x"), row=1, col=1)
    if t_reg:
        fig.add_trace(go.Scatter(x=[d for d,p,s in t_reg], y=[p for d,p,s in t_reg],
            mode="markers", name="天井点灯",
            marker=dict(symbol="triangle-down", size=11, color="#f43f5e",
                        line=dict(color="white", width=1)),
            text=[f"天井{s}/9" for d,p,s in t_reg], hoverinfo="text+x"), row=1, col=1)
    if b_full:
        fig.add_trace(go.Scatter(x=[d for d,p,s in b_full], y=[p for d,p,s in b_full],
            mode="text", name="大底フル点灯",
            text=["💎" for _ in b_full], textposition="bottom center",
            textfont=dict(size=20),
            hovertext=[f"大底フル{s}/10" for d,p,s in b_full], hoverinfo="text+x"), row=1, col=1)
    if t_full:
        fig.add_trace(go.Scatter(x=[d for d,p,s in t_full], y=[p for d,p,s in t_full],
            mode="text", name="天井フル点灯",
            text=["⛔" for _ in t_full], textposition="top center",
            textfont=dict(size=20),
            hovertext=[f"天井フル{s}/9" for d,p,s in t_full], hoverinfo="text+x"), row=1, col=1)

fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["sma25"],
    name="MA25", line=dict(color="#f59e0b",width=1,dash="dash")), row=1, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["sma75"],
    name="MA75", line=dict(color="#a78bfa",width=1,dash="dash")), row=1, col=1)
if not chart_df["sma200"].isna().all():
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["sma200"],
        name="MA200", line=dict(color="#f87171",width=1,dash="dot")), row=1, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["rsi"],
    name=f"RSI（{tf}）", line=dict(color="#34d399",width=1.5)), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
colors_hist = ["#4ade80" if v>=0 else "#f87171" for v in chart_df["macd_hist"].fillna(0)]
fig.add_trace(go.Bar(x=chart_df.index, y=chart_df["macd_hist"],
    marker_color=colors_hist, showlegend=False), row=3, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["macd"],
    name="MACD", line=dict(color="#3a8fff",width=1)), row=3, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["macd_signal"],
    name="シグナル", line=dict(color="#f87171",width=1)), row=3, col=1)
fig.update_layout(height=700, paper_bgcolor="#070f18", plot_bgcolor="#0c1a28",
    font=dict(color="#c8d8e8"), legend=dict(orientation="h", y=1.02, font=dict(color="#ffffff")),
    showlegend=show_legend, margin=dict(t=10,b=10),
    xaxis_rangeslider_visible=False)
fig.update_xaxes(gridcolor="#1a2a3a")
fig.update_yaxes(gridcolor="#1a2a3a")
fig.update_yaxes(title_text="RSI", row=2, col=1)
fig.update_yaxes(title_text="MACD", row=3, col=1)
st.plotly_chart(fig, use_container_width=True,
    config={"staticPlot": False, "scrollZoom": True, "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"]})

st.caption(f"出典: yfinance | データ最終日: {df.index[-1].strftime('%Y-%m-%d')} | スコアは常に日足データで計算（チャート時間軸とは独立）| 出口: 3分割買い+TP50%/SL15%/180日（EV+10.4%）")
