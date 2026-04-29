import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai
import pandas_ta as ta
import requests

# ====================== 1. إعداد الصفحة والمظهر ======================
st.set_page_config(page_title="Stock AI Analyst Pro 📈", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 بوت تحليل الأسهم الذكي - النسخة النهائية")

# ====================== 2. دالة إرسال تلجرام ======================
def send_telegram_msg(message):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        requests.post(url, data=data)
    except Exception as e:
        st.error(f"خطأ في إرسال تلجرام: {e}")

# ====================== 3. إعداد Gemini ======================
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
try:
    model = genai.GenerativeModel(
        model_name="models/gemini-1.5-flash"  # أضفنا كلمة models/ قبل الاسم
    )
except Exception as e:
    # كخطة بديلة إذا فشل الفلاش، نستخدم النسخة العادية
    model = genai.GenerativeModel("gemini-pro") 

    else:
        st.warning("⚠️ يرجى إضافة GEMINI_API_KEY في Secrets")
except Exception as e:
    st.error(f"❌ خطأ في تهيئة الذكاء الاصطناعي: {e}")

# ====================== 4. جلب البيانات والمؤشرات ======================
@st.cache_data(ttl=600)
def get_stock_data(ticker, period="1y"):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty: return None, None
        
        # إضافة المؤشرات الفنية
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['EMA_9'] = ta.ema(df['Close'], length=9)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        return df, stock.info
    except:
        return None, None

# ====================== 5. الواجهة الجانبية ======================
with st.sidebar:
    st.header("⚙️ الإعدادات")
    ticker = st.text_input("رمز السهم", value="2222.SR").upper()
    period = st.selectbox("الفترة", ["3mo", "6mo", "1y", "2y"], index=2)
    st.divider()

# ====================== 6. العرض الرئيسي والتحليل ======================
if ticker:
    hist, info = get_stock_data(ticker, period)
    
    if hist is not None:
        # عرض المقاييس الأساسية
        curr_price = info.get('currentPrice') or hist['Close'].iloc[-1]
        rsi_val = hist['RSI'].iloc[-1]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("السعر الحالي", f"{curr_price:.2f}")
        c2.metric("RSI", f"{rsi_val:.1f}")
        c3.metric("اسم الشركة", info.get('longName', ticker))

        # الرسم البياني
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="السعر"), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # التحليل بالذكاء الاصطناعي
        st.subheader("🚀 التحليل الذكي")
        
        # تعريف الـ Prompt هنا لضمان وجوده قبل الاستخدام
        prompt_text = f"حلل سهم {ticker} فنياً. السعر: {curr_price:.2f}. RSI: {rsi_val:.2f}. أجب بالعربية بنقاط واضحة."

        if st.button("إجراء التحليل الفني"):
            with st.spinner("جاري تحليل البيانات..."):
                try:
                    response = model.generate_content(prompt_text)
                    st.session_state['last_analysis'] = response.text
                    st.success("تم التحليل بنجاح!")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"فشل التحليل: {e}")

        # زر إرسال تلجرام (يعمل فقط بعد إجراء التحليل)
        if st.button("إرسال التقرير إلى تلجرام 📱"):
            if 'last_analysis' in st.session_state:
                full_message = f"تقرير سهم {ticker}:\n\n{st.session_state['last_analysis']}"
                send_telegram_msg(full_message)
                st.info("تم إرسال الرسالة إلى هاتفك")
            else:
                st.warning("يرجى إجراء التحليل أولاً بالضغط على الزر أعلاه.")
    else:
        st.error("تعذر جلب البيانات. تأكد من رمز السهم.")
