import streamlit as st
from pathlib import Path
import appdirs as ad

# حل مشكلة الكاش الخاصة بـ yfinance على Streamlit Cloud
CACHE_DIR = ".cache"
ad.user_cache_dir = lambda *args: CACHE_DIR
Path(CACHE_DIR).mkdir(exist_ok=True)

# استيراد باقي المكتبات
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai
import pandas_ta as ta
import requests  # مهم لدالة تلجرام

# ====================== 1. إعداد الصفحة ======================
st.set_page_config(
    page_title="Stock AI Analyst Pro 📈",
    layout="wide"
)

st.markdown("""
    <style>
    .stMetric { 
        background-color: #161b22; 
        border-radius: 10px; 
        padding: 15px; 
        border: 1px solid #30363d; 
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 بوت تحليل الأسهم الذكي - النسخة الكاملة")

# ====================== 2. دالة إرسال تلجرام ======================
def send_telegram_msg(message):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        response = requests.post(url, data=data)
        return response.ok
    except Exception as e:
        st.error(f"خطأ في إرسال تلجرام: {e}")
        return False

# ====================== 3. إعداد Gemini ======================
def initialize_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.warning("⚠️ يرجى إضافة GEMINI_API_KEY في Secrets")
        return None

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    model_names = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "models/gemini-1.5-flash"
    ]
    
    for name in model_names:
        try:
            test_model = genai.GenerativeModel(model_name=name)
            # اختبار سريع
            test_model.generate_content("ping", generation_config={"max_output_tokens": 1})
            return test_model
        except Exception:
            continue
            
    return None

# تهيئة Gemini
model = initialize_gemini()

if model:
    st.success(f"✅ تم تفعيل Gemini بنجاح ({model.model_name.split('/')[-1]})")
else:
    st.error("❌ فشل الاتصال بـ Gemini. تأكد من صلاحية API Key")

# ====================== 4. جلب البيانات ======================
@st.cache_data(ttl=600)
def get_stock_data(ticker, period="1y"):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None, None
        
        # إضافة المؤشرات الفنية
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['EMA_9'] = ta.ema(df['Close'], length=9)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        return df, stock.info
    except Exception:
        return None, None

# ====================== 5. الشريط الجانبي ======================
with st.sidebar:
    st.header("⚙️ الإعدادات")
    ticker_input = st.text_input("رمز السهم", value="2222.SR").upper().strip()
    period_select = st.selectbox("الفترة", ["3mo", "6mo", "1y", "2y"], index=2)
    st.divider()

# ====================== 6. العرض الرئيسي ======================
if ticker_input:
    hist, info = get_stock_data(ticker_input, period_select)
    
    if hist is not None and not hist.empty:
        curr_price = info.get('currentPrice') or hist['Close'].iloc[-1]
        rsi_val = hist['RSI'].iloc[-1] if 'RSI' in hist.columns else None
        
        # عرض المقاييس
        c1, c2, c3 = st.columns(3)
        c1.metric("السعر الحالي", f"{curr_price:.2f}")
        c2.metric("RSI (14)", f"{rsi_val:.1f}" if rsi_val else "N/A")
        c3.metric("اسم الشركة", info.get('longName', ticker_input))

        # الرسم البياني
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        
        fig.add_trace(go.Candlestick(
            x=hist.index, 
            open=hist['Open'], 
            high=hist['High'], 
            low=hist['Low'], 
            close=hist['Close'], 
            name="السعر"
        ), row=1, col=1)
        
        if rsi_val is not None:
            fig.add_trace(go.Scatter(
                x=hist.index, 
                y=hist['RSI'], 
                name="RSI", 
                line=dict(color='magenta')
            ), row=2, col=1)
        
        fig.update_layout(
            height=550, 
            template="plotly_dark", 
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # التحليل بالذكاء الاصطناعي
        st.subheader("🚀 التحليل الذكي")
        
        prompt_text = f"""
        أنت محلل أسهم محترف. حلل السهم {ticker_input} باللغة العربية.
        السعر الحالي: {curr_price:.2f}
        مؤشر RSI: {rsi_val:.2f if rsi_val else 'غير متوفر'}
        أعطِ تحليلاً فنياً مختصراً يشمل:
        - الاتجاه العام
        - نقاط الدعم والمقاومة المهمة
        - توصية واضحة (شراء / بيع / انتظار)
        """

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🤖 طلب تحليل Gemini", use_container_width=True):
                if model:
                    with st.spinner("جاري التحليل..."):
                        try:
                            response = model.generate_content(prompt_text)
                            st.session_state['last_analysis'] = response.text
                            st.markdown("### 📝 نتيجة التحليل:")
                            st.write(response.text)
                        except Exception as e:
                            st.error(f"خطأ في توليد التحليل: {e}")
                else:
                    st.error("لم يتم تهيئة Gemini بشكل صحيح")

        with col2:
            if st.button("📱 إرسال إلى تلجرام", use_container_width=True):
                if 'last_analysis' in st.session_state:
                    message = f"تقرير سهم {ticker_input}:\n\n{st.session_state['last_analysis']}"
                    if send_telegram_msg(message):
                        st.success("✅ تم الإرسال إلى تلجرام بنجاح!")
                else:
                    st.warning("يرجى عمل تحليل Gemini أولاً")
    else:
        st.error("تعذر جلب البيانات. تأكد من صحة رمز السهم (مثال: 2222.SR أو AAPL)")
else:
    st.info("أدخل رمز السهم في الشريط الجانبي للبدء")
