"""
ملف: .streamlit/pages/1_📈_تحليل_السهم.py
المسار: /trading_platform/.streamlit/pages/1_📈_تحليل_السهم.py
الوظيفة: صفحة تحليل الأسهم المتقدمة
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas_ta as ta
from datetime import datetime, timedelta
import sys
sys.path.append('/app')

from backend.api.market_data import MarketDataManager
from backend.agents.trading_agent import TradingAgent

st.set_page_config(
    page_title="تحليل الأسهم - منصة التداول",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
    .stMetric {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #333;
    }
    .buy-signal {
        background-color: #00ff8820;
        border-left: 4px solid #00ff88;
        padding: 10px;
        border-radius: 5px;
    }
    .sell-signal {
        background-color: #ff444420;
        border-left: 4px solid #ff4444;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 تحليل الأسهم المتقدم")
st.markdown("**تحليل فني + ذكاء اصطناعي + مؤشرات متقدمة**")

# ====================== قائمة الأسهم ======================
STOCKS = {
    "🇪🇬 البنك التجاري الدولي (CIB)": "COMI.CA",
    "🇪🇬 طلعت مصطفى القابضة": "TMGH.CA",
    "🇪🇬 السويدي إليكتريك": "SWDY.CA",
    "🇪🇬 الشرقية للدخان": "EAST.CA",
    "🇸🇦 أرامكو السعودية": "2222.SR",
    "🇸🇦 مصرف الراجحي": "1120.SR",
    "🇺🇸 Apple Inc.": "AAPL",
    "🇺🇸 Microsoft Corp.": "MSFT",
    "🇺🇸 Tesla Inc.": "TSLA",
    "🇺🇸 NVIDIA Corp.": "NVDA"
}

# ====================== دوال التحليل ======================
@st.cache_data(ttl=300)
def get_stock_data(symbol: str, period: str = "1y"):
    """جلب بيانات السهم"""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        
        if df.empty:
            return None, None
        
        # حساب المؤشرات الفنية
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['EMA_9'] = ta.ema(df['Close'], length=9)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # MACD
        macd = ta.macd(df['Close'])
        if macd is not None:
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_Signal'] = macd['MACDs_12_26_9']
        
        # Bollinger Bands
        bb = ta.bbands(df['Close'], length=20)
        if bb is not None:
            df['BB_Upper'] = bb['BBU_20_2.0']
            df['BB_Middle'] = bb['BBM_20_2.0']
            df['BB_Lower'] = bb['BBL_20_2.0']
        
        return df, stock.info
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return None, None

def get_trading_signal(rsi: float, sma_20: float, sma_50: float, current_price: float) -> dict:
    """توليد إشارة تداول"""
    signal = {
        "action": "انتظار",
        "color": "neutral",
        "strength": 0,
        "reasons": []
    }
    
    # إشارات RSI
    if rsi < 30:
        signal["strength"] += 30
        signal["reasons"].append(f"RSI منخفض ({rsi:.1f}) - منطقة ذروة بيع")
    elif rsi > 70:
        signal["strength"] -= 30
        signal["reasons"].append(f"RSI مرتفع ({rsi:.1f}) - منطقة ذروة شراء")
    
    # إشارات المتوسطات المتحركة
    if sma_20 > sma_50:
        signal["strength"] += 20
        signal["reasons"].append("المتوسط 20 فوق المتوسط 50 - اتجاه صاعد")
    elif sma_20 < sma_50:
        signal["strength"] -= 20
        signal["reasons"].append("المتوسط 20 تحت المتوسط 50 - اتجاه هابط")
    
    # تحديد الإجراء
    if signal["strength"] >= 30:
        signal["action"] = "شراء قوي"
        signal["color"] = "buy"
    elif signal["strength"] >= 15:
        signal["action"] = "شراء"
        signal["color"] = "buy"
    elif signal["strength"] <= -30:
        signal["action"] = "بيع قوي"
        signal["color"] = "sell"
    elif signal["strength"] <= -15:
        signal["action"] = "بيع"
        signal["color"] = "sell"
    
    return signal

# ====================== الواجهة الرئيسية ======================
col1, col2 = st.columns([2, 1])

with col1:
    selected_name = st.selectbox(
        "🔍 اختر السهم",
        options=list(STOCKS.keys()),
        format_func=lambda x: x
    )
    selected_symbol = STOCKS[selected_name]

with col2:
    period = st.selectbox(
        "📅 الفترة الزمنية",
        ["1mo", "3mo", "6mo", "1y", "2y"],
        index=3
    )

# جلب البيانات
with st.spinner("جاري تحميل البيانات..."):
    df, info = get_stock_data(selected_symbol, period)

if df is not None and not df.empty:
    # ====================== المقاييس الأساسية ======================
    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
    change = current_price - prev_price
    change_percent = (change / prev_price) * 100 if prev_price else 0
    rsi = df['RSI'].iloc[-1]
    volume = df['Volume'].iloc[-1]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💰 السعر الحالي", f"{current_price:.2f}", f"{change:+.2f} ({change_percent:+.2f}%)")
    with col2:
        st.metric("📊 RSI (14)", f"{rsi:.1f}")
    with col3:
        st.metric("📈 SMA 20", f"{df['SMA_20'].iloc[-1]:.2f}")
    with col4:
        st.metric("📉 SMA 50", f"{df['SMA_50'].iloc[-1]:.2f}")
    with col5:
        st.metric("💹 الحجم", f"{volume:,.0f}")
    
    # ====================== إشارة التداول ======================
    signal = get_trading_signal(
        rsi, 
        df['SMA_20'].iloc[-1], 
        df['SMA_50'].iloc[-1], 
        current_price
    )
    
    if signal["action"] != "انتظار":
        if signal["color"] == "buy":
            st.markdown(f"""
            <div class="buy-signal">
                <h3>🟢 {signal['action']}</h3>
                <p>{' • '.join(signal['reasons'])}</p>
                <p><strong>قوة الإشارة:</strong> {abs(signal['strength'])}%</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="sell-signal">
                <h3>🔴 {signal['action']}</h3>
                <p>{' • '.join(signal['reasons'])}</p>
                <p><strong>قوة الإشارة:</strong> {abs(signal['strength'])}%</p>
            </div>
            """, unsafe_allow_html=True)
    
    # ====================== الرسم البياني المتقدم ======================
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.2, 0.15, 0.15],
        subplot_titles=("السعر مع المتوسطات و Bollinger", "RSI", "MACD", "حجم التداول")
    )
    
    # السعر
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name="السعر"
    ), row=1, col=1)
    
    # المتوسطات المتحركة
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name="SMA 20", line=dict(color='orange')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name="SMA 50", line=dict(color='blue')), row=1, col=1)
    
    # Bollinger Bands
    if 'BB_Upper' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name="BB Upper", line=dict(color='gray', dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name="BB Lower", line=dict(color='gray', dash='dash')), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    # MACD
    if 'MACD' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name="MACD", line=dict(color='blue')), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name="Signal", line=dict(color='red')), row=3, col=1)
    
    # الحجم
    colors = ['red' if close < open else 'green' for close, open in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color=colors), row=4, col=1)
    
    fig.update_layout(
        height=800,
        template="plotly_dark",
        title_text=f"تحليل {selected_name}",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    fig.update_xaxes(rangeslider_visible=False)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ====================== التحليل بالذكاء الاصطناعي ======================
    st.subheader("🤖 التحليل بالذكاء الاصطناعي")
    
    if st.button("🚀 تحليل ذكي باستخدام Gemini", type="primary"):
        if "GEMINI_API_KEY" in st.secrets:
            import google.generativeai as genai
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
            قم بتحليل سهم {selected_name} ({selected_symbol}) بناءً على البيانات التالية:
            
            السعر الحالي: {current_price:.2f}
            التغير: {change_percent:+.2f}%
            RSI: {rsi:.1f}
            SMA 20: {df['SMA_20'].iloc[-1]:.2f}
            SMA 50: {df['SMA_50'].iloc[-1]:.2f}
            
            المؤشرات:
            - RSI: {'ذروة بيع' if rsi < 30 else 'ذروة شراء' if rsi > 70 else 'محايد'}
            - الاتجاه: {'صاعد' if df['SMA_20'].iloc[-1] > df['SMA_50'].iloc[-1] else 'هابط'}
            
            قدم تحليلاً شاملاً بالعربية يشمل:
            1. تحليل الاتجاه العام
            2. نقاط الدعم والمقاومة
            3. توصية للمستثمر
            4. نسبة المخاطرة المتوقعة
            """
            
            with st.spinner("جاري التحليل..."):
                try:
                    response = model.generate_content(prompt)
                    st.success("✅ نتيجة التحليل:")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"خطأ في التحليل: {e}")
        else:
            st.warning("⚠️ يرجى إضافة GEMINI_API_KEY في ملف secrets")
    
    # ====================== معلومات إضافية ======================
    with st.expander("📊 معلومات إضافية عن السهم"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**نقاط الدعم والمقاومة**")
            st.write(f"• المقاومة 1: {df['High'].tail(20).max():.2f}")
            st.write(f"• المقاومة 2: {df['High'].tail(50).max():.2f}")
            st.write(f"• الدعم 1: {df['Low'].tail(20).min():.2f}")
            st.write(f"• الدعم 2: {df['Low'].tail(50).min():.2f}")
        
        with col2:
            st.write("**المؤشرات الفنية**")
            st.write(f"• التقلب (ATR): {ta.atr(df['High'], df['Low'], df['Close']).iloc[-1]:.2f}")
            st.write(f"• الحجم النسبي: {(df['Volume'].iloc[-1] / df['Volume'].tail(20).mean()):.2f}x")
            st.write(f"• أعلى 52 أسبوع: {info.get('fiftyTwoWeekHigh', 'N/A')}")
            st.write(f"• أدنى 52 أسبوع: {info.get('fiftyTwoWeekLow', 'N/A')}")

else:
    st.error("❌ تعذر جلب البيانات. تأكد من اتصال الإنترنت وصحة رمز السهم")

st.caption("⚠️ البيانات من Yahoo Finance | التحليل بالذكاء الاصطناعي Gemini | للأغراض التعليمية فقط")
