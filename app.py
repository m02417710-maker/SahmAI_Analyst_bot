import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai
import pandas_ta as ta

# ====================== إعداد الصفحة ======================
st.set_page_config(
    page_title="Stock AI Analyst Pro 📈",
    page_icon="📊",
    layout="wide"
)

# تصميم واجهة محسنة
st.markdown("""
    <style>
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 بوت تحليل الأسهم الذكي - النسخة المطورة")

# ====================== إعداد Gemini ======================
try:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ يرجى إضافة GEMINI_API_KEY في ملف .streamlit/secrets.toml")
        st.stop()

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")

except Exception as e:
    st.error(f"❌ خطأ في تهيئة Gemini: {e}")
    st.stop()

# ====================== دوال المساعدة ======================
@st.cache_data(ttl=600) # التخزين المؤقت لمدة 10 دقائق
def get_stock_data(ticker: str, period: str = "1y"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty: return None, None
        
        # إضافة المؤشرات الفنية (محسنة)
        hist['SMA_20'] = ta.sma(hist['Close'], length=20)
        hist['EMA_9'] = ta.ema(hist['Close'], length=9) # متوسط سريع
        hist['RSI'] = ta.rsi(hist['Close'], length=14)
        return hist, stock.info
    except:
        return None, None

# ====================== الشريط الجانبي ======================
with st.sidebar:
    st.header("⚙️ الإعدادات")
    ticker = st.text_input("رمز السهم", value="2222.SR").upper()
    period = st.selectbox("الفترة الزمنية", ["3mo", "6mo", "1y", "2y", "5y"], index=2)
    
    st.divider()
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ====================== الجزء الرئيسي ======================
if ticker:
    with st.spinner(f"جاري جلب بيانات {ticker}..."):
        hist, info = get_stock_data(ticker, period)
    
    if hist is not None:
        # استخراج الأسعار بأمان (Safe Extraction)
        curr_price = info.get('currentPrice') or info.get('regularMarketPrice') or hist['Close'].iloc[-1]
        prev_close = info.get('regularMarketPreviousClose') or hist['Close'].iloc[-2]
        change_pct = ((curr_price - prev_close) / prev_close) * 100
        
        # صف المؤشرات العلوية
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("السعر الحالي", f"{curr_price:.2f}", f"{change_pct:.2f}%")
        
        # تحليل RSI فورياً
        rsi_val = hist['RSI'].iloc[-1]
        rsi_signal = "تشبع شراء ⚠️" if rsi_val > 70 else "تشبع بيع ✅" if rsi_val < 30 else "محايد ⚖️"
        c2.metric("حالة RSI", rsi_signal, delta=f"{rsi_val:.1f}")
        
        c3.metric("أعلى سعر (52 أسبوع)", f"{info.get('fiftyTwoWeekHigh', 'N/A')}")
        c4.metric("القيمة السوقية", f"{info.get('marketCap', 0)/1e9:.1f}B")

        # ==================== الرسم البياني الاحترافي ====================
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           row_heights=[0.7, 0.3], vertical_spacing=0.05)

        # الشموع اليابانية والمتوسطات
        fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'],
                                   low=hist['Low'], close=hist['Close'], name="السعر"), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=hist.index, y=hist['EMA_9'], name="EMA 9 (سريع)", 
                               line=dict(color='#00d4ff', width=1)), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_20'], name="SMA 20 (اتجاه)", 
                               line=dict(color='#ff9900', width=1.5)), row=1, col=1)

        # مؤشر RSI
        fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", 
                               line=dict(color='#e100ff')), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

        fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
        
        # إخفاء أيام العطلات في الرسم البياني
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])]) 
        
        st.plotly_chart(fig, use_container_width=True)

        # ====================== تحليل الذكاء الاصطناعي ======================
        st.subheader("💬 التحليل الذكي مع Gemini")
        user_query = st.text_input("اسأل Gemini عن هذا السهم (مثلاً: ما هي مستويات الدعم القادمة؟)")

        if st.button("🚀 اطلب التحليل الفني"):
            prompt = f"""
            بصفتك محلل مالي محترف، حلل سهم {ticker} ({info.get('longName')}).
            البيانات الحالية:
            - السعر: {curr_price}
            - RSI: {rsi_val:.2f}
            - اتجاه المتوسط 20 يوم: {hist['SMA_20'].iloc[-1]:.2f}
            
            بناءً على الرسم البياني، ما هو توقعك للاتجاه القادم؟ وما هي نصيحتك للمستثمر حالياً؟ 
            أجب بالعربية بشكل نقاط منظمة.
            """
            with st.spinner("جاري التفكير..."):
                try:
                    response = model.generate_content(prompt)
                    st.markdown("### 📝 تقرير الخبير:")
                    st.success(response.text)
                except Exception as e:
                    st.error(f"خطأ: {e}")

    else:
        st.info("أدخل رمز سهم صحيح للبدء (مثلاً: AAPL للأسهم الأمريكية أو 2222.SR لأرامكو)")
      
