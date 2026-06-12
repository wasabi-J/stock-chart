import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas.tseries.offsets import BDay

st.set_page_config(page_title="大底・天井スコア", layout="wide")

TICKERS = {
    "KRUS（くら寿司USA）": "KRUS",
    "COIN（コインベース）": "COIN",
    "1328（金ETF）": "1328.T",
    "NVDA（エヌビディア）": "NVDA",
    "TSLA（テスラ）": "TSLA",
    "GLD（金ETF米国）": "GLD",
    "S&P500": "^GSPC",
    "NASDAQ": "^IXIC",
    "日経平均": "^N225",
}

st.title("📈 大底・天井スコア")
st.caption("大底10条件・天井9条件 | 15銘柄・36年・250大底で検証 | 買い:スコア9+ 売り:天井8+")

col_l, col_r = st.columns([2,1])
with col_l:
    ticker_name = st.selectbox("銘柄を選択", list(TICKERS.keys()))
with col_r:
    custom = st.text_input("直接入力（例：AAPL）", "")

ticker = custom.upper().strip() if custom.strip() else TICKERS[ticker_name]
period = st.selectbox("データ期間（2年以上推奨）", ["2y","5y","10y","max"], index=1)

@st.cache_data(ttl=3600)
def load_data(ticker, period):
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

bottom_score, bottom_checks = calc_bottom_score(latest)
top_score, top_checks = calc_top_score(latest)
st.markdown(f"### {ticker}")
c1,c2,c3,c4 = st.columns(4)
c1.metric("現在値", f"{symbol}{float(latest['close']):,.2f}", f"{change:+,.2f}（{change_pct:+.2f}%）")
c2.metric("日足RSI / 週足RSI", f"{float(latest['rsi']):.1f} / {float(latest['w_rsi']):.1f}" if pd.notna(latest['w_rsi']) else f"{float(latest['rsi']):.1f} / -")
c3.metric("大底スコア", f"{bottom_score}/10")
c4.metric("天井スコア", f"{top_score}/9")

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
    col_b, col_t = st.columns(2)
    with col_b:
        st.markdown(f"**大底スコア {bottom_score}/10**")
        for label, ok, detail in bottom_checks:
            mark = "✅" if ok else "❌"
            st.markdown(f"{mark} {label}　{detail}")
    with col_t:
        st.markdown(f"**天井スコア {top_score}/9**")
        for label, ok, detail in top_checks:
            mark = "✅" if ok else "❌"
            st.markdown(f"{mark} {label}　{detail}")

period_options = {"3ヶ月":90,"6ヶ月":180,"1年":365,"2年":730,"全期間":99999}
disp = st.radio("表示期間", list(period_options.keys()), index=2, horizontal=True)
days = period_options[disp]
chart_df = df if days >= 99999 else df[df.index >= pd.Timestamp.now() - pd.Timedelta(days=days)]

fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                    row_heights=[0.55,0.25,0.20], vertical_spacing=0.03)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["bb_upper"],
    line=dict(color="rgba(100,100,255,0.2)",width=1), showlegend=False), row=1, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["bb_lower"],
    fill="tonexty", fillcolor="rgba(100,100,255,0.05)",
    line=dict(color="rgba(100,100,255,0.2)",width=1), showlegend=False), row=1, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["close"],
    name="終値", line=dict(color="#3a8fff",width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["sma25"],
    name="MA25", line=dict(color="#f59e0b",width=1,dash="dash")), row=1, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["sma75"],
    name="MA75", line=dict(color="#a78bfa",width=1,dash="dash")), row=1, col=1)
if not chart_df["sma200"].isna().all():
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["sma200"],
        name="MA200", line=dict(color="#f87171",width=1,dash="dot")), row=1, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["rsi"],
    name="RSI", line=dict(color="#34d399",width=1.5)), row=2, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["w_rsi"],
    name="週足RSI", line=dict(color="#fbbf24",width=1,dash="dot")), row=2, col=1)
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
    margin=dict(t=10,b=10))
fig.update_xaxes(gridcolor="#1a2a3a")
fig.update_yaxes(gridcolor="#1a2a3a")
fig.update_yaxes(title_text="RSI", row=2, col=1)
fig.update_yaxes(title_text="MACD", row=3, col=1)
st.plotly_chart(fig, use_container_width=True)
st.caption(f"出典: yfinance | データ最終日: {df.index[-1].strftime('%Y-%m-%d')} | 買いシグナル的中率77%（クラスタ単位88-100%）| 出口: 3分割買い+TP50%/SL15%/180日（EV+10.4%）")
