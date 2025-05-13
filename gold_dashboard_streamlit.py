import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pytz

# Configure page
st.set_page_config(
    page_title="XAU/USD Gold Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Improved color scheme for better visibility
st.markdown("""
<style>
    .gold-header {
        color: #FFD700 !important;
        font-weight: bold !important;
    }
    .metric-card {
        border-left: 4px solid #FFD700;
        padding: 15px;
        background-color: #1E1E1E;
        border-radius: 5px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .positive {
        color: #00FF00 !important;  /* Bright green */
        font-weight: bold;
    }
    .negative {
        color: #FF0000 !important;  /* Bright red */
        font-weight: bold;
    }
    .neutral {
        color: #FFFFFF !important;  /* White */
    }
    .stAlert {
        background-color: #1E1E1E !important;
    }
    .st-b7 {
        color: #FFD700 !important;
    }
    .st-cj {
        background-color: #FFD700 !important;
    }
</style>
""", unsafe_allow_html=True)

# Cache data functions for performance
@st.cache_data(ttl=60*15)
def get_gold_data():
    data = yf.download('GC=F', period='1mo', interval='15m')
    if data.empty:
        return pd.DataFrame()
    return data[['Open', 'High', 'Low', 'Close', 'Volume']]

# Dashboard Header
st.title("🪙 XAU/USD Gold Trading Dashboard")
st.markdown("---")

# Fetch data
data = get_gold_data()

if data.empty:
    st.error("Failed to fetch gold price data. Please try again later.")
    st.stop()

# Calculate indicators
data['SMA_20'] = data['Close'].rolling(20).mean()
data['SMA_50'] = data['Close'].rolling(50).mean()
delta = data['Close'].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()
rs = avg_gain / avg_loss
data['RSI'] = 100 - (100 / (1 + rs))

# Get current values (ensure they're scalar values)
current_price = float(data['Close'].iloc[-1])
prev_close = float(data['Close'].iloc[-2]) if len(data) > 1 else current_price
price_change = current_price - prev_close
percent_change = (price_change / prev_close) * 100
rsi_value = float(data['RSI'].iloc[-1])

# Metrics Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class='metric-card'>
            <h3 class='gold-header'>Current Price</h3>
            <h2 class='neutral'>${current_price:.2f}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    change_class = "positive" if price_change >= 0 else "negative"
    change_icon = "▲" if price_change >= 0 else "▼"
    st.markdown(
        f"""
        <div class='metric-card'>
            <h3 class='gold-header'>24h Change</h3>
            <h2 class='{change_class}'>
                {change_icon} ${abs(price_change):.2f} ({abs(percent_change):.2f}%)
            </h2>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    rsi_class = "negative" if rsi_value > 70 else "positive" if rsi_value < 30 else "neutral"
    st.markdown(
        f"""
        <div class='metric-card'>
            <h3 class='gold-header'>RSI (14)</h3>
            <h2 class='{rsi_class}'>{rsi_value:.1f}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f"""
        <div class='metric-card'>
            <h3 class='gold-header'>Today's Range</h3>
            <h2 class='neutral'>${float(data['Low'].min()):.2f} - ${float(data['High'].max()):.2f}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

# Main Chart
st.markdown("### Price Analysis")
fig = go.Figure()

# Candlestick chart with improved visibility
fig.add_trace(go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    name='XAU/USD',
    increasing_line_color='#00FF00',  # Bright green
    decreasing_line_color='#FF0000',  # Bright red
    increasing_fillcolor='rgba(0, 255, 0, 0.8)',
    decreasing_fillcolor='rgba(255, 0, 0, 0.8)'
))

# Moving averages
fig.add_trace(go.Scatter(
    x=data.index,
    y=data['SMA_20'],
    line=dict(color='#FFA500', width=2),  # Orange
    name='20 SMA'
))

fig.add_trace(go.Scatter(
    x=data.index,
    y=data['SMA_50'],
    line=dict(color='#FF00FF', width=2),  # Magenta
    name='50 SMA'
))

fig.update_layout(
    template='plotly_dark',
    margin=dict(l=20, r=20, t=30, b=20),
    showlegend=True,
    legend=dict(orientation='h', y=1.1),
    xaxis_rangeslider_visible=False,
    yaxis_title='Price (USD)',
    height=500,
    hovermode="x unified",
    plot_bgcolor='#1E1E1E',
    paper_bgcolor='#1E1E1E',
    font=dict(color='white')
)

st.plotly_chart(fig, use_container_width=True)

# Technical Indicators
st.markdown("### Technical Indicators")
tab1, tab2, tab3 = st.tabs(["RSI", "MACD", "Volume"])

with tab1:
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(
        x=data.index,
        y=data['RSI'],
        line=dict(color='#FFD700', width=2),
        name='RSI'
    ))
    rsi_fig.add_hline(y=70, line_dash="dash", line_color="red")
    rsi_fig.add_hline(y=30, line_dash="dash", line_color="green")
    rsi_fig.update_layout(
        template='plotly_dark',
        height=300,
        showlegend=False,
        plot_bgcolor='#1E1E1E',
        paper_bgcolor='#1E1E1E'
    )
    st.plotly_chart(rsi_fig, use_container_width=True)

# Add MACD and Volume tabs content here...

# Auto-refresh button
if st.button('Refresh Data'):
    st.cache_data.clear()
    st.experimental_rerun()

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")