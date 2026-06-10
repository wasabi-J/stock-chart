import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="株価チャート", layout="wide")

TICKERS = {
    "KRUS（くら寿司USA）": "KRUS",
    "1328（金ETF）": "1328.T",
}

st.title("📈 株価チャート＋シグナル")

ticker_name = st.selectbox("銘柄を選択", list(TICKERS.keys()))
ticker = TICKERS[ticker_name]
period = st.selectbox("期間", ["3mo", "6mo", "1y", "2y", "5y"], index=2)

@st.cache_data(ttl=3600)
def load_data(ticker, period):
    df = yf.download(ticker, period=period, auto_adjust=True)
    df = df[["Close"]].copy()
    df.columns = ["close"]
    df["sma25"] = df["close"].rolling(25).mean()
    df["sma75"] = df["close"].rolling(75).mean()
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    return df

with st.spinner("データ取得中..."):
    df = load_data(ticker, period)

latest = df.iloc[-1]
prev = df.iloc[-2]
change = latest["close"] - prev["close"]
change_pct = change / prev["close"] * 100

col1, col2, col3 = st.columns(3)
col1.metric("現在値", f"{'$' if '.T' not in ticker else '¥'}{latest['close']:.2f}", f"{change:+.2f}（{change_pct:+.2f}%）")
col2.metric("RSI", f"{latest['rsi']:.1f}")
col3.metric("MA25", f"{latest['sma25']:.2f}")

# シグナル判断
rsi_thresh = 60
falling = latest["close"] < prev["close"]
signal = latest["rsi"] <= rsi_thresh and falling

if signal:
    st.success("▶ エントリーシグナル点灯（RSI≤60かつ下落）")
else:
    st.info(f"待機中 | RSI {latest['rsi']:.1f} / 条件: RSI≤{rsi_thresh}かつ下落")

fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    row_heights=[0.7, 0.3], vertical_spacing=0.05)

fig.add_trace(go.Scatter(x=df.index, y=df["close"], name="終値", line=dict(color="#3a8fff", width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["sma25"], name="MA25", line=dict(color="#f59e0b", width=1, dash="dash")), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["sma75"], name="MA75", line=dict(color="#a78bfa", width=1, dash="dash")), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["rsi"], name="RSI", line=dict(color="#34d399", width=1.5)), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
fig.add_hline(y=60, line_dash="dot", line_color="orange", opacity=0.5, row=2, col=1)

fig.update_layout(height=600, paper_bgcolor="#070f18", plot_bgcolor="#0c1a28",
                  font=dict(color="#c8d8e8"), legend=dict(orientation="h"))
fig.update_xaxes(gridcolor="#1a2a3a")
fig.update_yaxes(gridcolor="#1a2a3a")

st.plotly_chart(fig, use_container_width=True)
st.caption(f"データ取得: yfinance | 最終更新: {df.index[-1].strftime('%Y-%m-%d')}")
