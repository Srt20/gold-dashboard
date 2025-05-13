import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pytz

# ========== SETUP ==========
st.set_page_config(
    page_title="XAU/USD Gold Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for high visibility
st.markdown("""
<style>
    .gold-text { color: #FFD700 !important; }
    .positive { color: #00FF00 !important; }
    .negative { color: #FF6347 !important; }
    .metric-card {
        background: #1E1E1E;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #FFD700;
    }
    .stAlert { background-color: #2E2E2E !important; }
</style>
""", unsafe_allow_html=True)

# ========== DATA FUNCTIONS ==========
@st.cache_data(ttl=60*15)  # 15-minute cache
def get_data():
    df = yf.download('GC=F', period='1mo', interval='15m')
    if df.empty:
        st.error("❌ Failed to fetch data. Try again later.")
        st.stop()
    
    # Calculate indicators
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    
    # RSI Calculation
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(span=14).mean()
    avg_loss = loss.ewm(span=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

@st.cache_data(ttl=60*60)  # 1-hour cache
def get_news():
    try:
        url = "https://www.kitco.com/news/"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        return [
            {"title": a.text.strip(), "url": f"https://www.kitco.com{a['href']}"}
            for a in soup.select('h3.title a')[:5]
        ]
    except:
        return []

# ========== DASHBOARD LAYOUT ==========
st.title("🪙 XAU/USD Gold Trading Dashboard", anchor=False)
st.markdown("---")

# Fetch data
data = get_data()
news = get_news()
current_price = float(data['Close'].iloc[-1])
price_change = float(current_price - data['Close'].iloc[-2])
pct_change = (price_change / current_price) * 100

# ========== METRICS ROW ==========
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class='metric-card'>
        <h3 class='gold-text'>LIVE PRICE</h3>
        <h1>${current_price:,.2f}</h1>
    </div>
    """, unsafe_allow_html=True)

with col2:
    change_class = "positive" if price_change >= 0 else "negative"
    st.markdown(f"""
    <div class='metric-card'>
        <h3 class='gold-text'>24H CHANGE</h3>
        <h1 class='{change_class}'>
            {'↑' if price_change >=0 else '↓'} ${abs(price_change):.2f} ({abs(pct_change):.2f}%)
        </h1>
    </div>
    """, unsafe_allow_html=True)

with col3:
    rsi = float(data['RSI'].iloc[-1])
    rsi_class = "negative" if rsi > 70 else "positive" if rsi < 30 else "gold-text"
    st.markdown(f"""
    <div class='metric-card'>
        <h3 class='gold-text'>RSI (14)</h3>
        <h1 class='{rsi_class}'>{rsi:.1f}</h1>
    </div>
    """, unsafe_allow_html=True)

# ========== PRICE CHART ==========
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    name='Price',
    increasing_line_color='#00FF00',
    decreasing_line_color='#FF0000'
))
fig.add_trace(go.Scatter(
    x=data.index,
    y=data['SMA_20'],
    line=dict(color='orange', width=2),
    name='20 SMA'
))
fig.update_layout(
    height=500,
    template='plotly_dark',
    xaxis_rangeslider_visible=False,
    margin=dict(l=20, r=20, t=30, b=20)
)
st.plotly_chart(fig, use_container_width=True)

# ========== NEWS SECTION ==========
st.markdown("### 🔍 Latest Gold News")
if news:
    for item in news:
        st.markdown(f"""
        <div style="margin-bottom: 10px;">
            <a href="{item['url']}" target="_blank" style="color: #FFD700 !important;">
                → {item['title']}
            </a>
        </div>
        """, unsafe_allow_html=True)
else:
    st.warning("No news fetched. Check connection.")

# ========== FOOTER ==========
st.markdown("---")
st.caption(f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("⚠️ For educational purposes only - Not financial advice")

# ========== AUTO-REFRESH ==========
st.button("🔄 Refresh Data", on_click=st.cache_data.clear)