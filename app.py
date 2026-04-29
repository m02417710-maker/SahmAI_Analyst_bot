import streamlit as st
from pathlib import Path
import appdirs as ad
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai
import pandas_ta as ta
from datetime import datetime

# حل مشكلة الكاش
CACHE_DIR = ".cache"
ad.user_cache_dir = lambda *args: CACHE_DIR
Path(CACHE_DIR).mkdir(exist_ok=True)

st.set_page_config(page_title="Stock AI Analyst - مصر 📈", page_icon="🇪🇬", layout="wide")

st.title("📈 بوت تحليل الأسهم المصرية الذكي")
st.markdown("**البورصة المصرية (EGX) • تحليل فني + ذكاء اصطناعي + أخبار**")

# ====================== إعداد Gemini ======================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ يرجى إضافة GEMINI_API_KEY في .streamlit/secrets.toml")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# ====================== قائمة الأسهم المصرية المحدثة ======================
egyptian_stocks = {
    "COMI.CA": "البنك التجاري الدولي (CIB)",
    "TMGH.CA": "طلعت مصطفى القابضة",
    "SWDY.CA": "السويدي إليكتريك",
    "ETEL.CA": "تليكوم مصر",
    "EGAL.CA": "مصر للألومنيوم",
    "EAST.CA": "الشرقية للدخان",
    "MFPC.CA": "مصر لإنتاج الأسمدة (موبكو)",
    "ORAS.CA": "أوراسكوم للإنشاءات",
    "JUFO.CA": "جي بي أوتو",
    "ABUK.CA": "أبو قير للأسمدة",
    "HRHO.CA": "البنك الهولندي",
    "SUGR.CA": "سكر الحدود",
}

# ====================== دالة جلب البيانات ======================
@st.cache_data(ttl=180)
def get_egyptian_stock(ticker: str, period: str = "1y"):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None, None, ticker
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        return df, stock.info, ticker
    except:
        return None, None, ticker

# ====================== التنقل بين الصفحات ======================
page = st.sidebar.radio("اختر القسم", 
    ["تحليل سهم واحد", "أداء الأسهم المصرية (صعود/هبوط)", "أخبار وتحليل عام"])

# ====================== صفحة 1: تحليل سهم واحد ======================
if page == "تحليل سهم واحد":
    st.header("تحليل سهم فردي")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected = st.selectbox("اختر السهم", 
            options=list(egyptian_stocks.keys()),
            format_func=lambda x: f"{x} — {egyptian_stocks[x]}")
    
    with col2:
        if st.button("🔄 تحديث البيانات", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    period = st.selectbox("الفترة", ["3mo", "6mo", "1y", "2y"], index=2)
    
    hist, info, ticker = get_egyptian_stock(selected, period)
    
    if hist is not None and not hist.empty:
        curr_price = info.get('currentPrice') or hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else curr_price
        change_pct = ((curr_price - prev_price) / prev_price) * 100 if prev_price else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("السعر الحالي", f"{curr_price:.2f} ج.م", f"{change_pct:.2f}%")
        c2.metric("RSI (14)", f"{hist['RSI'].iloc[-1]:.1f}")
        c3.metric("الشركة", egyptian_stocks.get(ticker, ticker))
        c4.metric("آخر تحديث", datetime.now().strftime("%H:%M"))

        # الرسم البياني
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'],
                                    low=hist['Low'], close=hist['Close']), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
        fig.update_layout(height=650, template="plotly_dark", title=f"تحليل {ticker}", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # تحليل Gemini
        if st.button("🤖 تحليل ذكي مفصل", type="primary"):
            with st.spinner("جاري التحليل..."):
                prompt = f"""أنت محلل أسهم مصري محترف. حلل السهم {ticker} ({egyptian_stocks.get(ticker)}) 
                السعر الحالي: {curr_price:.2f} جنيه | RSI: {hist['RSI'].iloc[-1]:.1f}
                أعطِ تحليلاً شاملاً بالعربية يشمل: الاتجاه، الدعم والمقاومة، التوصية."""
                try:
                    resp = model.generate_content(prompt)
                    st.write(resp.text)
                except Exception as e:
                    st.error(e)
    else:
        st.error("تعذر جلب البيانات، جرب تحديث البيانات")

# ====================== صفحة 2: أداء الأسهم (صعود وهبوط) ======================
elif page == "أداء الأسهم المصرية (صعود/هبوط)":
    st.header("📊 أداء الأسهم المصرية اليوم")
    
    if st.button("🔄 تحديث قائمة الأداء"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("جاري تحليل أداء الأسهم..."):
        results = []
        for ticker in list(egyptian_stocks.keys())[:12]:   # تحليل أول 12 سهماً
            try:
                df = yf.Ticker(ticker).history(period="5d")
                if not df.empty:
                    change = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                    results.append({
                        "الرمز": ticker,
                        "الاسم": egyptian_stocks[ticker],
                        "التغير %": round(change, 2),
                        "السعر": round(df['Close'].iloc[-1], 2)
                    })
            except:
                pass
        
        if results:
            df_perf = pd.DataFrame(results)
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🚀 أقوى الأسهم صعوداً")
                gainers = df_perf.nlargest(6, "التغير %")
                st.dataframe(gainers, use_container_width=True, hide_index=True)
            
            with col2:
                st.subheader("🔻 أقوى الأسهم هبوطاً")
                losers = df_perf.nsmallest(6, "التغير %")
                st.dataframe(losers, use_container_width=True, hide_index=True)
            
            # تحليل عام بـ Gemini
            if st.button("📈 تحليل عام للسوق المصري"):
                with st.spinner("جاري تحليل السوق..."):
                    prompt = "قم بتحليل عام للبورصة المصرية اليوم مع التركيز على أقوى القطاعات والأسهم الصاعدة والهابطة."
                    try:
                        resp = model.generate_content(prompt)
                        st.write(resp.text)
                    except Exception as e:
                        st.error(e)
        else:
            st.warning("لم يتم جلب بيانات كافية")

# ====================== صفحة 3: أخبار وتحليل عام ======================
else:
    st.header("📰 أخبار وتحليل عام للبورصة المصرية")
    
    if st.button("🔄 تحديث الأخبار والتحليل"):
        st.rerun()
    
    prompt_news = """
    أعطني ملخصاً بالعربية عن آخر تطورات البورصة المصرية (EGX) اليوم أو هذا الأسبوع، 
    مع التركيز على:
    - أداء مؤشر EGX30
    - أهم الأسهم النشطة
    - أي أخبار اقتصادية مؤثرة (فائدة البنوك، الدولار، التضخم...)
    """
    
    with st.spinner("جاري تحليل الأخبار والسوق..."):
        try:
            response = model.generate_content(prompt_news)
            st.markdown("### 📝 التحليل والملخص")
            st.write(response.text)
        except Exception as e:
            st.error(f"خطأ: {e}")

st.caption("⚠️ البيانات من yfinance • التحليل بـ Google Gemini • للأغراض التعليمية فقط")
# 1. أولاً: نجهز النص (الـ prompt)
prompt_text = f"""
بصفتك محلل مالي، حلل سهم {ticker}. 
السعر الحالي: {curr_price}. 
أعطني تحليل فني سريع ونقاط الدعم والمقاومة بالعربية.
"""

# 2. ثانياً: نستخدمه داخل الزر
if st.button("🚀 اطلب التحليل الفني"):
    with st.spinner("جاري التفكير..."):
        try:
            # نمرر المتغير الذي أنشأناه (prompt_text) للموديل
            response = model.generate_content(prompt_text) 
            
            st.markdown("### 📝 تقرير الخبير:")
            st.success(response.text)
            
            # حفظ النتيجة لإرسالها لتلجرام لاحقاً
            st.session_state['last_response'] = response.text
        except Exception as e:
            st.error(f"خطأ أثناء التوليد: {e}")
