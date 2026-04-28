# -stock---ai--analyst-arabic-stock-analysis-bot-
 
 بوت تحليل الأسهم الذكي باستخدام Streamlit + yfinance + Google Gemini (يدعم الأسهم السعودية والعالمية)
 stock-ai-analyst/
├── app.py                  # الكود الرئيسي (Streamlit)
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── secrets.toml        # (يُضاف في .gitignore)
├── README.md
├── LICENSE (اختياري)
└── utils/
    ├── __init__.py
    ├── data_fetcher.py     # جلب البيانات + المؤشرات الفنية
    └── ai_analyzer.py      # التعامل مع Gemini
    streamlit
yfinance
pandas
plotly
google-generativeai
python-dotenv
pandas_ta          # مهم جداً لـ RSI, MACD, Bollinger...
GEMINI_API_KEY = "AIzaSy..."
GEMINI_API_KEY=AIzaSy...
# داخل Sidebar، بعد إعدادات السهم الواحد
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai
from datetime import datetime
import pandas_ta as ta

# ====================== إعداد الصفحة ======================
st.set_page_config(
    page_title="Stock AI Analyst 📈",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 بوت تحليل الأسهم الذكي - Stock AI Analyst")
st.markdown("**واجهة عربية تفاعلية تجمع بين بيانات حية + رسوم احترافية + تحليل ذكي بـ Gemini**")

# ====================== إعداد Gemini ======================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("يرجى إضافة GEMINI_API_KEY في secrets.toml")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')   # أو gemini-1.5-pro لتحليل أعمق

# ====================== دوال المساعدة ======================
@st.cache_data(ttl=300)  # تحديث كل 5 دقائق
def get_stock_data(ticker: str, period: str = "1y"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        info = stock.info
        return hist, info
    except Exception as e:
        st.error(f"خطأ في جلب بيانات {ticker}: {e}")
        return None, None

def add_technical_indicators(df):
    df = df.copy()
    # Moving Averages
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['EMA_20'] = df['Close'].ewm(span=20).mean()
    
    # RSI & MACD
    df['RSI'] = ta.rsi(df['Close'], length=14)
    macd = ta.macd(df['Close'])
    df = pd.concat([df, macd], axis=1)
    
    return df

# ====================== Sidebar ======================
with st.sidebar:
    st.header("إعدادات التحليل")
    
    ticker = st.text_input("رمز السهم", value="2222.SR", help="مثال: 2222.SR لأرامكو، AAPL، TSLA...")
    period = st.selectbox("الفترة الزمنية", 
                         options=["1mo", "3mo", "6mo", "1y", "2y", "5y"], 
                         index=3)
    
    show_indicators = st.checkbox("إظهار المؤشرات الفنية (RSI + MACD)", value=True)
    
    analysis_type = st.radio("نوع التحليل", 
                            ["تحليل سريع", "تحليل فني مفصل", "مقارنة سهمين"])

# ====================== الجزء الرئيسي ======================
if ticker:
    hist, info = get_stock_data(ticker, period)
    
    if hist is not None and not hist.empty:
        hist = add_technical_indicators(hist)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("السعر الحالي", f"{info.get('currentPrice', 'N/A'):.2f}")
        with col2:
            change = info.get('regularMarketChangePercent', 0)
            st.metric("التغيير اليومي", f"{change:.2f}%", delta=f"{change:.2f}%")
        with col3:
            st.metric("القيمة السوقية", f"{info.get('marketCap', 0)/1e9:.1f}B")
        with col4:
            st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
        
        # رسم بياني رئيسي
        fig = make_subplots(rows=3 if show_indicators else 1, 
                           cols=1, 
                           shared_xaxes=True,
                           row_heights=[0.6, 0.2, 0.2] if show_indicators else [1],
                           subplot_titles=("سعر السهم", "MACD", "RSI") if show_indicators else None)
        
        # Candlestick
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name="Candlestick"
        ), row=1, col=1)
        
        # Moving Averages
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_20'], name="SMA 20", line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], name="SMA 50", line=dict(color='blue')), row=1, col=1)
        
        if show_indicators:
            # MACD
            fig.add_trace(go.Scatter(x=hist.index, y=hist['MACD_12_26_9'], name="MACD", line=dict(color='green')), row=2, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist['MACDs_12_26_9'], name="Signal", line=dict(color='red')), row=2, col=1)
            
            # RSI
            fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", line=dict(color='purple')), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        
        fig.update_layout(height=700 if show_indicators else 500, 
                         xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # زر تحميل البيانات
        csv = hist.to_csv().encode('utf-8')
        st.download_button("⬇️ تحميل البيانات كـ CSV", csv, f"{ticker}_data.csv", "text/csv")
        
        # ====================== الشات الذكي ======================
        st.subheader("💬 اسأل Gemini عن السهم (بالعربية)")
        user_query = st.text_area("اكتب سؤالك أو طلب التحليل هنا:", 
                                 placeholder="حلل السهم فنياً... ما توقعاتك للشهر القادم؟ قارن أرامكو مع أبل...")
        
        if st.button("احصل على التحليل الذكي", type="primary"):
            if user_query:
                with st.spinner("جاري التحليل باستخدام Gemini..."):
                    prompt = f"""
                    أنت محلل أسهم محترف جداً وموضوعي. 
                    السهم: {ticker} - {info.get('longName', '')}
                    المعلومات الأساسية: {info}
                    آخر 10 أيام من البيانات: {hist.tail(10).to_string()}
                    المؤشرات الفنية الحالية: RSI={hist['RSI'].iloc[-1]:.1f} | MACD={hist['MACD_12_26_9'].iloc[-1]:.3f}
                    
                    السؤال/الطلب: {user_query}
                    
                    أجب بالعربية الفصحى بشكل واضح ومنظم:
                    - الاتجاه العام
                    - نقاط القوة والضعف
                    - المخاطر
                    - اقتراحات عملية (شراء/بيع/انتظار)
                    """
                    
                    response = model.generate_content(prompt)
                    st.markdown("### التحليل الذكي:")
                    st.write(response.text)
            else:
                st.warning("اكتب سؤالاً أولاً!")

    else:
        st.warning("لم يتم العثور على بيانات لهذا الرمز. جرب رمزاً آخر (مثل: 2222.SR أو AAPL).")
st.divider()
st.subheader("🔄 مقارنة بين سهمين")

compare_mode = st.checkbox("تفعيل وضع المقارنة")
if compare_mode:
    ticker2 = st.text_input("رمز السهم الثاني", value="AAPL", help="مثال: AAPL أو TSLA أو 1180.SR")
    compare_period = st.selectbox("فترة المقارنة", options=["3mo", "6mo", "1y", "2y"], index=2)
    # ====================== مقارنة بين سهمين ======================
if compare_mode and ticker2:
    with st.spinner(f"جاري جلب بيانات المقارنة بين {ticker} و {ticker2}..."):
        hist1, info1 = get_stock_data(ticker, compare_period)
        hist2, info2 = get_stock_data(ticker2, compare_period)
    
    if hist1 is not None and hist2 is not None:
        # توحيد التواريخ للمقارنة
        compare_df = pd.DataFrame({
            ticker: hist1['Close'],
            ticker2: hist2['Close']
        }).dropna()
        
        # رسم مقارنة
        fig_compare = go.Figure()
        fig_compare.add_trace(go.Scatter(x=compare_df.index, y=compare_df[ticker], name=ticker, line=dict(width=3)))
        fig_compare.add_trace(go.Scatter(x=compare_df.index, y=compare_df[ticker2], name=ticker2, line=dict(width=3)))
        
        fig_compare.update_layout(
            title=f"مقارنة أداء {ticker} مقابل {ticker2}",
            height=500,
            template="plotly_dark",
            xaxis_title="التاريخ",
            yaxis_title="سعر الإغلاق"
        )
        st.plotly_chart(fig_compare, use_container_width=True)
        
        # تحليل المقارنة بـ Gemini
        if st.button("🔍 احصل على تحليل مقارن بـ Gemini", type="primary"):
            with st.spinner("جاري تحليل المقارنة..."):
                try:
                    prompt_compare = f"""
                    أنت محلل أسهم محترف. قارن بين السهمين التاليين باللغة العربية:

                    السهم الأول: {ticker} - {info1.get('longName', '')}
                    السهم الثاني: {ticker2} - {info2.get('longName', '')}

                    بيانات الأداء التاريخي (آخر 10 أيام):
                    {compare_df.tail(10).to_string()}

                    أعطِ مقارنة واضحة تشمل:
                    - الأداء النسبي
                    - التقلب (Volatility)
                    - نقاط القوة والضعف لكل سهم
                    - أي سهم أفضل حالياً ولماذا
                    - توصية استثمارية
                    """

                    response = model.generate_content(prompt_compare)
                    st.markdown("### 📊 تحليل المقارنة الذكي")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"خطأ في تحليل المقارنة: {e}")
                    # 📈 بوت تحليل الأسهم الذكي - Stock AI Analyst

**واجهة ويب تفاعلية عربية** تجمع بين **بيانات البورصة الحية** و**الذكاء الاصطناعي** لتحليل الأسهم السعودية والعالمية.

![Stock Analysis Dashboard](https://via.placeholder.com/800x400/0A2540/00FFAA?text=Stock+AI+Analyst+Dashboard)  
*(استبدل برابط صورة شاشة حقيقية بعد التشغيل)*

---

## ✨ المميزات الرئيسية

- جلب بيانات حية من yfinance (دعم كامل لأسهم **تداول** مثل 2222.SR و1180.SR)
- رسوم بيانية احترافية تفاعلية (شموع + Bollinger Bands + Moving Averages)
- مؤشرات فنية متقدمة باستخدام **pandas_ta** (RSI, MACD, Bollinger Bands)
- **شات ذكي باللغة العربية** مدعوم بـ Google Gemini (Flash + Pro)
- **مقارنة بين سهمين** مع رسم وتحليل ذكي
- تحميل البيانات كملف CSV
- واجهة سريعة ومتجاوبة مبنية بـ **Streamlit**

---

## 🛠️ التقنيات المستخدمة

| التقنية              | الاستخدام                          |
|----------------------|------------------------------------|
| **Streamlit**        | واجهة الويب التفاعلية            |
| **yfinance**         | جلب البيانات الحية                |
| **pandas_ta**        | حساب المؤشرات الفنية              |
| **Google Gemini**    | التحليل الذكي والردود بالعربية   |
| **Plotly**           | رسوم بيانية عالية الجودة          |
| **Pandas**           | معالجة البيانات                    |
