pip install streamlit yfinance pandas plotly google-generativeai pandas_ta
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai
import pandas_ta as ta

# ====================== إعداد الصفحة ======================
st.set_page_config(
    page_title="Stock AI Analyst 📈",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 بوت تحليل الأسهم الذكي")
st.markdown("**واجهة عربية تفاعلية | yfinance + Google Gemini + pandas_ta**")

# ====================== إعداد Gemini ======================
try:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ يرجى إضافة GEMINI_API_KEY في ملف .streamlit/secrets.toml")
        st.stop()

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    model_name = st.sidebar.selectbox(
        "اختر نموذج Gemini",
        options=["gemini-1.5-flash", "gemini-1.5-pro"],
        index=0,
        help="Pro أقوى وأدق لكن أبطأ"
    )
    model = genai.GenerativeModel(model_name)

except Exception as e:
    st.error(f"❌ خطأ في تهيئة Gemini: {e}")
    st.stop()

# ====================== دوال المساعدة ======================
@st.cache_data(ttl=300)
def get_stock_data(ticker: str, period: str = "1y"):
    """جلب بيانات السهم"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        info = stock.info
        if hist.empty:
            st.warning(f"⚠️ لم يتم العثور على بيانات للسهم: {ticker}")
            return None, None
        return hist, info
    except Exception as e:
        st.error(f"❌ خطأ في جلب بيانات {ticker}: {str(e)}")
        return None, None


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """إضافة المؤشرات الفنية باستخدام pandas_ta"""
    try:
        df = df.copy()
        
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        df = pd.concat([df, macd], axis=1)
        
        bb = ta.bbands(df['Close'], length=20)
        df = pd.concat([df, bb], axis=1)
        
        return df
    except Exception as e:
        st.warning(f"⚠️ تعذر حساب بعض المؤشرات الفنية: {e}")
        return df


# ====================== الشريط الجانبي (Sidebar) ======================
with st.sidebar:
    st.header("⚙️ إعدادات التحليل")
    
    ticker = st.text_input("رمز السهم الأول", value="2222.SR", 
                          help="مثال: 2222.SR لأرامكو، 1180.SR، AAPL، TSLA")
    
    period = st.selectbox("الفترة الزمنية", 
                         options=["1mo", "3mo", "6mo", "1y", "2y", "5y"], 
                         index=3)
    
    show_indicators = st.checkbox("إظهار المؤشرات الفنية (RSI + MACD + Bollinger)", value=True)
    
    st.divider()
    st.subheader("🔄 مقارنة بين سهمين")
    compare_mode = st.checkbox("تفعيل وضع المقارنة")
    
    if compare_mode:
        ticker2 = st.text_input("رمز السهم الثاني", value="AAPL")
        compare_period = st.selectbox("فترة المقارنة", 
                                     options=["3mo", "6mo", "1y", "2y"], 
                                     index=2)

# ====================== الجزء الرئيسي ======================
if ticker:
    with st.spinner(f"جاري جلب بيانات {ticker}..."):
        hist, info = get_stock_data(ticker, period)
    
    if hist is not None and not hist.empty:
        hist = add_technical_indicators(hist)
        
        # عرض المؤشرات الأساسية
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            st.metric("السعر الحالي", f"{price:.2f}" if price else "غير متوفر")
        
        with col2:
            change = info.get('regularMarketChangePercent', 0)
            st.metric("التغيير اليومي", f"{change:.2f}%", delta=f"{change:.2f}%" if change else None)
        
        with col3:
            cap = info.get('marketCap', 0)
            st.metric("القيمة السوقية", f"{cap/1e9:.1f}B" if cap else "غير متوفر")
        
        with col4:
            pe = info.get('trailingPE') or info.get('forwardPE')
            st.metric("نسبة P/E", f"{pe:.2f}" if pe else "غير متوفر")

        # ==================== الرسم البياني ====================
        rows = 3 if show_indicators else 1
        row_heights = [0.55, 0.225, 0.225] if show_indicators else [1]
        
        fig = make_subplots(
            rows=rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=row_heights,
            subplot_titles=("سعر السهم", "MACD", "RSI") if show_indicators else None
        )

        # Candlestick + Bollinger
        fig.add_trace(go.Candlestick(
            x=hist.index, open=hist['Open'], high=hist['High'],
            low=hist['Low'], close=hist['Close'], name="Candlestick"
        ), row=1, col=1)

        if 'BBU_20_2.0' in hist.columns:
            fig.add_trace(go.Scatter(x=hist.index, y=hist['BBU_20_2.0'], 
                                   name="Upper BB", line=dict(color='gray', dash='dash')), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist['BBL_20_2.0'], 
                                   name="Lower BB", line=dict(color='gray', dash='dash')), row=1, col=1)

        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_20'], 
                               name="SMA 20", line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], 
                               name="SMA 50", line=dict(color='blue')), row=1, col=1)

        if show_indicators:
            # MACD
            fig.add_trace(go.Scatter(x=hist.index, y=hist.get('MACD_12_26_9'), 
                                   name="MACD", line=dict(color='green')), row=2, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist.get('MACDs_12_26_9'), 
                                   name="Signal", line=dict(color='red')), row=2, col=1)
            
            # RSI
            fig.add_trace(go.Scatter(x=hist.index, y=hist.get('RSI'), 
                                   name="RSI", line=dict(color='purple')), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

        fig.update_layout(
            height=700 if show_indicators else 500,
            xaxis_rangeslider_visible=False,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # تحميل البيانات
        st.download_button(
            label="⬇️ تحميل البيانات كـ CSV",
            data=hist.to_csv().encode('utf-8'),
            file_name=f"{ticker}_{period}.csv",
            mime="text/csv"
        )

        # ====================== الشات الذكي ======================
        st.subheader("💬 التحليل الذكي مع Gemini")
        user_query = st.text_area(
            "اكتب سؤالك أو طلب التحليل:",
            placeholder="حلل السهم فنياً... ما رأيك في أرامكو حالياً؟",
            height=100
        )

        if st.button("🚀 احصل على التحليل", type="primary"):
            if user_query.strip():
                with st.spinner("جاري التحليل باستخدام Gemini..."):
                    try:
                        prompt = f"""
                        أنت محلل أسهم محترف. 
                        السهم: {ticker} - {info.get('longName', 'غير معروف')}
                        آخر 10 أيام: {hist.tail(10)[['Close', 'Volume', 'RSI']].to_string()}
                        RSI الحالي: {hist['RSI'].iloc[-1]:.2f if 'RSI' in hist else 'N/A'}
                        
                        الطلب: {user_query}
                        
                        أجب بالعربية بشكل واضح ومنظم مع توصية استثمارية.
                        """
                        response = model.generate_content(prompt)
                        st.markdown("### 📝 التحليل:")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"❌ خطأ أثناء التحليل: {str(e)}")
            else:
                st.warning("يرجى كتابة سؤال أولاً.")

        # ====================== مقارنة بين سهمين ======================
        if compare_mode and 'ticker2' in locals() and ticker2:
            st.subheader(f"🔄 مقارنة: {ticker} مقابل {ticker2}")
            
            with st.spinner(f"جاري جلب بيانات {ticker2}..."):
                hist2, info2 = get_stock_data(ticker2, compare_period)
            
            if hist2 is not None and not hist2.empty:
                compare_df = pd.DataFrame({
                    ticker: hist['Close'],
                    ticker2: hist2['Close']
                }).dropna()

                fig_compare = go.Figure()
                fig_compare.add_trace(go.Scatter(x=compare_df.index, y=compare_df[ticker], 
                                               name=ticker, line=dict(width=3)))
                fig_compare.add_trace(go.Scatter(x=compare_df.index, y=compare_df[ticker2], 
                                               name=ticker2, line=dict(width=3)))
                
                fig_compare.update_layout(
                    title=f"مقارنة أداء {ticker} و {ticker2}",
                    height=500,
                    template="plotly_dark",
                    xaxis_title="التاريخ",
                    yaxis_title="سعر الإغلاق"
                )
                st.plotly_chart(fig_compare, use_container_width=True)

                if st.button("🔍 تحليل مقارن بـ Gemini", type="primary"):
                    with st.spinner("جاري التحليل المقارن..."):
                        try:
                            prompt = f"""
                            قارن بين السهمين {ticker} و {ticker2} باللغة العربية.
                            قدم تحليلاً واضحاً يشمل الأداء النسبي، نقاط القوة والضعف، والتوصية النهائية.
                            """
                            response = model.generate_content(prompt)
                            st.markdown("### 📊 التحليل المقارن:")
                            st.write(response.text)
                        except Exception as e:
                            st.error(f"❌ خطأ في التحليل المقارن: {str(e)}")
            else:
                st.warning(f"تعذر جلب بيانات السهم الثاني: {ticker2}")

    else:
        st.info("أدخل رمز السهم للبدء في التحليل (مثال: 2222.SR أو AAPL)")
