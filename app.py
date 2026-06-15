import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas.tseries.offsets import BDay

st.set_page_config(page_title="大底・天井スコア", layout="wide")

GROUPS = {
    "📁 保有中": {
        "COIN（コインベース）": "COIN",
        "MARA（マラソンデジタル）": "MARA",
        "TMF（米国債20年3倍）": "TMF",
        "1328（金ETF・日本）": "1328.T",
    },
    "📁 短期戦略": {
        "KRUS（くら寿司USA）": "KRUS",
    },
    "📁 監視": {
        "CLSK（クリーンスパーク）": "CLSK",
        "NVDA（エヌビディア）": "NVDA",
        "TSLA（テスラ）": "TSLA",
        "GLD（金ETF米国）": "GLD",
        "SLV（銀ETF）": "SLV",
        "SOFI（ソーファイ）": "SOFI",
        "EWZ（ブラジルETF）": "EWZ",
        "AMD": "AMD",
        "SOXL（半導体3倍）⚠️未検証": "SOXL",
        "QS（クアンタムスケープ）⚠️未検証": "QS",
        "XLE（エネルギーETF）": "XLE",
    },
    "📁 指数・コモディティ": {
        "S&P500": "^GSPC",
        "NASDAQ": "^IXIC",
        "日経平均": "^N225",
        "金（ゴールド）": "GC=F",
        "銀（シルバー）": "SI=F",
        "原油WTI": "CL=F",
        "VIX（恐怖指数）": "^VIX",
    },
}
ALL_TICKERS = [(label, tk) for g in GROUPS.values() for label, tk in g.items()]

@st.cache_data(ttl=3600)
def load_data(ticker, period="5y"):
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Close"]].copy()
    df.columns = ["close"]
    df = df.dropna()
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
    return df
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

st.title("📈 大底・天井スコア")
st.caption("大底10条件・天井9条件 | 15銘柄・36年・250大底で検証 | 買い:スコア9+ 売り:天井8+")
with st.expander("📖 運用ルール（必ず確認）"):
    st.markdown("""
**シグナル点灯時**: まず売買せずClaudeに相談。買いは3分割(0/+15/+30営業日)各1/3、TP+50%/SL-15%/最大180日。売りは半分利確＋残りに逆指値(高値-8〜10%)。
**集中リスク**: 暗号資産系(COIN/MARA/CLSK/TMF)は1銘柄まで。半導体系(NVDA/SOXL)も1銘柄まで。
**未検証(⚠️)**: SOFI/SOXL/QSは売買対象外・参考表示のみ。上場4年未満も対象外。
**ボーナス資金**: 指数9/10+の歴史的局面のみ。投信積立は不変、追加資金は暗号資産以外(XLE/EWZ/SLV/AMD等)優先。
""")

with st.spinner("登録銘柄をスキャン中（初回は20秒ほど）..."):
    scan = scan_all()

alerts = []
for label, tk, bs, ts in scan:
    vix_b = "（VIX底=株の楽観・天井警戒）" if tk == "^VIX" else ""
    vix_t = "（VIX天井=恐怖最大=株の買い場）" if tk == "^VIX" else ""
    if bs >= 9:
        alerts.append(("error", f"🟢 **{label}** 買いシグナル（大底{bs}/10）{vix_b}"))
    elif bs == 8:
        alerts.append(("warning", f"⚠️ **{label}** 買いゾーン接近（大底{bs}/10）{vix_b}"))
    if ts >= 8:
        alerts.append(("error", f"🔴 **{label}** 売りシグナル（天井{ts}/9）{vix_t}"))
    elif ts == 7:
        alerts.append(("warning", f"⚠️ **{label}** 天井警戒（天井{ts}/9）{vix_t}"))

if alerts:
    st.markdown("### 🚨 シグナル点灯中")
    for kind, msg in alerts:
        if kind == "error":
            st.error(msg)
        else:
            st.warning(msg)
else:
    st.success(f"✅ 本日のシグナルなし（{len(scan)}銘柄スキャン済み）")
st.divider()

col_g, col_t = st.columns([1,2])
with col_g:
    group_name = st.selectbox("グループ", list(GROUPS.keys()))
with col_t:
    ticker_name = st.selectbox("銘柄を選択", list(GROUPS[group_name].keys()))
custom = st.text_input("直接入力（米国株:AAPL / 日本株:4桁数字でOK 例:7203）", "")

_c = custom.strip()
ticker = (_c + ".T" if _c.isdigit() and len(_c) == 4 else _c.upper()) if _c else GROUPS[group_name][ticker_name]
period = st.selectbox("データ期間（スコア計算用・5y推奨）", ["2y","5y","10y","max"], index=1)

if _c:
    st.warning("⚠️ 直接入力銘柄は未検証です。スコアは参考表示のみとし、売買前に検証を依頼してください。")
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
st.markdown(f"### {ticker}")
c1,c2,c3,c4 = st.columns(4)
c1.metric("現在値", f"{symbol}{float(latest['close']):,.2f}", f"{change:+,.2f}（{change_pct:+.2f}%）")
c2.metric("日足RSI / 週足RSI", f"{float(latest['rsi']):.1f} / {float(latest['w_rsi']):.1f}" if pd.notna(latest['w_rsi']) else f"{float(latest['rsi']):.1f} / -")
c3.metric("大底スコア", f"{bottom_score}/10")
c4.metric("天井スコア", f"{top_score}/9")

if ticker == "^VIX":
    st.info("ℹ️ VIXは読み替え注意：VIXの天井=恐怖最大=株の買い場 / VIXの底=楽観=株の天井警戒")

if bottom_score >= 9:
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

if top_score >= 8:
    st.error(f"🔴 **売りシグナル点灯（天井スコア{top_score}/9）**：保有していれば利確・リスク管理を検討")
elif top_score == 7:
    st.warning(f"⚠️ 天井警戒（天井スコア{top_score}/9）")

with st.expander("📋 スコア詳細（タップで開閉）", expanded=(bottom_score>=8 or top_score>=7)):
    col_b, col_t2 = st.columns(2)
    with col_b:
        st.markdown(f"**大底スコア {bottom_score}/10**")
        for label, ok, detail in bottom_checks:
            st.markdown(f"{'✅' if ok else '❌'} {label}　{detail}")
    with col_t2:
        st.markdown(f"**天井スコア {top_score}/9**")
        for label, ok, detail in top_checks:
            st.markdown(f"{'✅' if ok else '❌'} {label}　{detail}")

tf = st.radio("チャート時間軸", ["日足","週足","月足"], index=0, horizontal=True)

def make_chart_frame(df, tf):
    if tf == "日足":
        base = df["close"]
    elif tf == "週足":
        base = df["close"].resample("W-FRI").last().dropna()
    else:
        try:
            base = df["close"].resample("ME").last().dropna()
        except ValueError:
            base = df["close"].resample("M").last().dropna()
    cd = pd.DataFrame({"close": base})
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

# === 過去のシグナル点灯日を計算（クラスタリングで1山1マーカー）===
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

    def clusterize(raw, pick="low"):
        if not raw:
            return []
        clusters = []
        cur = [raw[0]]
        for item in raw[1:]:
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
        return result

    bottom_days = clusterize(raw_bottom, pick="low")
    top_days = clusterize(raw_top, pick="high")
    return bottom_days, top_days

sig_bottoms, sig_tops = calc_signal_history(df, ticker)

show_signals = st.checkbox("📍 過去のシグナル点灯位置をチャートに表示", value=True,
    help="日足で大底9以上/天井8以上が点灯した日を価格チャート上に▲▼で表示")
show_hlines = st.checkbox("➖ 過去高値/安値の水平ラインを表示", value=False,
    help="意識されやすい過去の高値(赤)・安値(水色)に水平線を引く")
show_legend = st.checkbox("🏷️ チャート上部の線の説明（凡例）を表示", value=True)

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
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["close"],
    name="終値", line=dict(color="#3a8fff",width=1.5)), row=1, col=1)

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
        fig.add_hline(y=lv, line_dash="dot", line_color="rgba(244,63,94,0.35)",
                      line_width=1, row=1, col=1)
    for lv in thin(lows):
        fig.add_hline(y=lv, line_dash="dot", line_color="rgba(34,211,238,0.35)",
                      line_width=1, row=1, col=1)

if show_signals:
    x_min = chart_df.index.min()
    x_max = chart_df.index.max()
    b_x = [d for d,p,s in sig_bottoms if x_min <= d <= x_max]
    b_y = [p for d,p,s in sig_bottoms if x_min <= d <= x_max]
    b_s = [s for d,p,s in sig_bottoms if x_min <= d <= x_max]
    t_x = [d for d,p,s in sig_tops if x_min <= d <= x_max]
    t_y = [p for d,p,s in sig_tops if x_min <= d <= x_max]
    t_s = [s for d,p,s in sig_tops if x_min <= d <= x_max]
    if b_x:
        fig.add_trace(go.Scatter(x=b_x, y=b_y, mode="markers", name="大底点灯",
            marker=dict(symbol="triangle-up", size=11, color="#22d3ee",
                        line=dict(color="white", width=1)),
            text=[f"大底{s}/10" for s in b_s], hoverinfo="text+x"), row=1, col=1)
    if t_x:
        fig.add_trace(go.Scatter(x=t_x, y=t_y, mode="markers", name="天井点灯",
            marker=dict(symbol="triangle-down", size=11, color="#f43f5e",
                        line=dict(color="white", width=1)),
            text=[f"天井{s}/9" for s in t_s], hoverinfo="text+x"), row=1, col=1)

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
    font=dict(color="#c8d8e8"), legend=dict(orientation="h", y=1.02),
    showlegend=show_legend, margin=dict(t=10,b=10))
fig.update_xaxes(gridcolor="#1a2a3a")
fig.update_yaxes(gridcolor="#1a2a3a")
fig.update_yaxes(title_text="RSI", row=2, col=1)
fig.update_yaxes(title_text="MACD", row=3, col=1)
st.plotly_chart(fig, use_container_width=True,
    config={"staticPlot": False, "scrollZoom": True, "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"]})

st.caption(f"出典: yfinance | データ最終日: {df.index[-1].strftime('%Y-%m-%d')} | スコアは常に日足データで計算（チャート時間軸とは独立）| 出口: 3分割買い+TP50%/SL15%/180日（EV+10.4%）")
