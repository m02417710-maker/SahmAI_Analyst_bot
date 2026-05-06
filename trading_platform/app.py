"""
ملف: app.py (النسخة المبسطة والمستقرة)
المسار: /trading_platform/app.py
الوظيفة: التطبيق الرئيسي - نسخة مستقرة بدون أخطاء
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas_ta as ta
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Optional, Tuple

# تجاهل التحذيرات
warnings.filterwarnings('ignore')

# إعدادات الصفحة
st.set_page_config(
    page_title="البورصجي AI - تحليل الأسهم الذكي",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== إعدادات السمة ======================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
    }
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(0, 255, 136, 0.1);
    }
    .buy-signal {
        background: linear-gradient(135deg, #00ff8820 0%, #00ff8805 100%);
        border-left: 4px solid #00ff88;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .sell-signal {
        background: linear-gradient(135deg, #ff444420 0%, #ff444405 100%);
        border-left: 4px solid #ff4444;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .stButton > button {
        background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
        color: #0a0a0a;
        font-weight: bold;
        border: none;
        border-radius: 10px;
        padding: 10px 25px;
    }
</style>
""", unsafe_allow_html=True)

# ====================== إعدادات Gemini ======================
try:
    import google.generativeai as genai
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except:
    GEMINI_AVAILABLE = False

# ====================== قائمة الأسهم ======================
STOCKS = {
    "🇪🇬 COMI.CA": {"name": "البنك التجاري الدولي (CIB)", "market": "EGX"},
    "🇪🇬 TMGH.CA": {"name": "طلعت مصطفى القابضة", "market": "EGX"},
    "🇪🇬 SWDY.CA": {"name": "السويدي إليكتريك", "market": "EGX"},
    "🇸🇦 2222.SR": {"name": "أرامكو السعودية", "market": "TADAWUL"},
    "🇸🇦 1120.SR": {"name": "مصرف الراجحي", "market": "TADAWUL"},
    "🇺🇸 AAPL": {"name": "Apple Inc.", "market": "NASDAQ"},
    "🇺🇸 MSFT": {"name": "Microsoft Corp.", "market": "NASDAQ"},
    "🇺🇸 TSLA": {"name": "Tesla Inc.", "market": "NASDAQ"},
}

# ====================== دوال جلب البيانات ======================
@st.cache_data(ttl=300)
def get_stock_data(symbol: str, period: str = "1y"):
    """جلب بيانات السهم"""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        
        if df.empty:
            return None, None
        
        # المؤشرات الفنية
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
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
            df['BB_Lower'] = bb['BBL_20_2.0']
        
        df['Volume_SMA'] = ta.sma(df['Volume'], length=20)
        
        return df, stock.info
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return None, None

def generate_signal(df: pd.DataFrame) -> Dict:
    """توليد إشارة تداول"""
    if df is None or df.empty:
        return {"action": "انتظار", "confidence": 0, "reasons": []}
    
    rsi = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
    sma_20 = df['SMA_20'].iloc[-1] if not pd.isna(df['SMA_20'].iloc[-1]) else df['Close'].iloc[-1]
    sma_50 = df['SMA_50'].iloc[-1] if not pd.isna(df['SMA_50'].iloc[-1]) else df['Close'].iloc[-1]
    
    buy_score = 0
    sell_score = 0
    reasons = []
    
    if rsi < 30:
        buy_score += 30
        reasons.append(f"✅ RSI منخفض ({rsi:.1f}) - منطقة شراء")
    elif rsi > 70:
        sell_score += 30
        reasons.append(f"❌ RSI مرتفع ({rsi:.1f}) - منطقة بيع")
    
    if sma_20 > sma_50:
        buy_score += 20
        reasons.append("✅ المتوسط 20 فوق 50 - اتجاه صاعد")
    else:
        sell_score += 20
        reasons.append("❌ المتوسط 20 تحت 50 - اتجاه هابط")
    
    net = buy_score - sell_score
    
    if net >= 30:
        action = "شراء قوي"
    elif net >= 15:
        action = "شراء"
    elif net <= -30:
        action = "بيع قوي"
    elif net <= -15:
        action = "بيع"
    else:
        action = "انتظار"
    
    return {"action": action, "confidence": abs(net), "reasons": reasons[:3]}

# ====================== الواجهة الرئيسية ======================
def main():
    st.title("📈 البورصجي AI - تحليل الأسهم الذكي")
    st.markdown("**تحليل فني متقدم + إشارات تداول فورية**")
    st.markdown("---")
    
    # الشريط الجانبي
    with st.sidebar:
        st.markdown("## ⚙️ الإعدادات")
        
        selected_display = st.selectbox(
            "🔍 اختر السهم",
            options=list(STOCKS.keys()),
            format_func=lambda x: f"{x} - {STOCKS[x]['name']}"
        )
        
        selected_symbol = selected_display.split()[1]
        stock_name = STOCKS[selected_display]['name']
        
        period = st.selectbox(
            "📅 الفترة الزمنية",
            ["1mo", "3mo", "6mo", "1y", "2y"],
            index=3
        )
        
        st.markdown("---")
        if GEMINI_AVAILABLE:
            st.success("🤖 Gemini AI: متصل")
        else:
            st.warning("⚠️ Gemini AI: غير متصل")
    
    # جلب البيانات
    with st.spinner("📡 جاري تحميل البيانات..."):
        df, info = get_stock_data(selected_symbol, period)
    
    if df is not None and not df.empty:
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        change = current_price - prev_price
        change_percent = (change / prev_price) * 100 if prev_price else 0
        rsi = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
        
        # المقاييس
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 السعر", f"{current_price:.2f}", f"{change:+.2f} ({change_percent:+.2f}%)")
        col2.metric("📊 RSI", f"{rsi:.1f}")
        col3.metric("📈 SMA 20", f"{df['SMA_20'].iloc[-1]:.2f}")
        col4.metric("📉 SMA 50", f"{df['SMA_50'].iloc[-1]:.2f}")
        
        # إشارة التداول
        signal = generate_signal(df)
        
        if "شراء" in signal['action']:
            st.markdown(f"""
            <div class="buy-signal">
                <h3>🟢 {signal['action']}</h3>
                <p>💪 الثقة: {signal['confidence']}%</p>
                <ul>
                    {''.join([f'<li>{r}</li>' for r in signal['reasons']])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif "بيع" in signal['action']:
            st.markdown(f"""
            <div class="sell-signal">
                <h3>🔴 {signal['action']}</h3>
                <p>💪 الثقة: {signal['confidence']}%</p>
                <ul>
                    {''.join([f'<li>{r}</li>' for r in signal['reasons']])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info(f"🟡 {signal['action']}")
        
        st.markdown("---")
        
        # الرسم البياني
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name="السعر"
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name="SMA 20", line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        fig.update_layout(height=600, template="plotly_dark", title=f"{stock_name} ({selected_symbol})")
        fig.update_xaxes(rangeslider_visible=False)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # تحليل Gemini
        if GEMINI_AVAILABLE and st.button("🤖 تحليل ذكي", type="primary"):
            with st.spinner("جاري التحليل..."):
                try:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    prompt = f"""
                    حلل سهم {stock_name} ({selected_symbol}):
                    السعر: {current_price:.2f}
                    RSI: {rsi:.1f}
                    التغير: {change_percent:+.2f}%
                    الإشارة: {signal['action']}
                    
                    قدم تحليلاً مختصراً بالعربية (توصية، أسباب، مخاطرة).
                    """
                    response = model.generate_content(prompt)
                    st.success(response.text)
                except Exception as e:
                    st.error(f"خطأ: {e}")
    
    else:
        st.error("❌ تعذر جلب البيانات")

if __name__ == "__main__":
    main()
