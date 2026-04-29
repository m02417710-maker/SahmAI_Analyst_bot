
import streamlit as st
from pathlib import Path
import tempfile
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai
import pandas_ta as ta
from datetime import datetime
import io
import requests
from typing import Dict, List, Tuple, Optional

# ====================== 1. إعداد الكاش والمكتبات ======================
# حل مشكلة الكاش بطريقة احترافية
CACHE_DIR = Path(tempfile.gettempdir()) / "stock_analyst_cache"
CACHE_DIR.mkdir(exist_ok=True)

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="Stock AI Analyst - مصر 📈", 
    page_icon="🇪🇬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== 2. إعداد Gemini ======================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ يرجى إضافة GEMINI_API_KEY في .streamlit/secrets.toml")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# ====================== 3. قائمة الأسهم المصرية المحدثة ======================
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
    "ESRS.CA": "الشرقية للدخان - إيسترن كومباني",
    "SKPC.CA": "سيدبك",
    "PHDC.CA": "بالم هيلز للتعمير",
}

# ====================== 4. دوال مساعدة محسنة ======================
def init_session_state():
    """تهيئة متغيرات الجلسة"""
    if 'favorite_stocks' not in st.session_state:
        st.session_state.favorite_stocks = []
    if 'last_analysis' not in st.session_state:
        st.session_state.last_analysis = {}
    if 'analysis_cache' not in st.session_state:
        st.session_state.analysis_cache = {}
    if 'last_ticker' not in st.session_state:
        st.session_state.last_ticker = None

def get_technical_summary(df: pd.DataFrame) -> List[str]:
    """تلخيص المؤشرات الفنية"""
    if df.empty or len(df) < 20:
        return ["⚠️ بيانات غير كافية للتحليل"]
    
    last_rsi = df['RSI'].iloc[-1]
    last_price = df['Close'].iloc[-1]
    sma_20 = df['SMA_20'].iloc[-1] if not pd.isna(df['SMA_20'].iloc[-1]) else last_price
    
    signals = []
    
    # إشارات RSI
    if last_rsi > 70:
        signals.append("⚠️ ذروة شراء (RSI > 70)")
    elif last_rsi < 30:
        signals.append("✅ ذروة بيع (RSI < 30)")
    else:
        signals.append("⚖️ منطقة محايدة")
    
    # السعر مقابل المتوسط المتحرك
    if last_price > sma_20:
        signals.append("📈 السعر أعلى من المتوسط 20 (اتجاه صاعد)")
    else:
        signals.append("📉 السعر أقل من المتوسط 20 (اتجاه هابط)")
    
    # تحليل التذبذب
    price_change = ((last_price - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100 if len(df) >= 5 else 0
    if price_change > 5:
        signals.append(f"🚀 ارتفاع حاد خلال 5 أيام ({price_change:.1f}%)")
    elif price_change < -5:
        signals.append(f"📉 انخفاض حاد خلال 5 أيام ({price_change:.1f}%)")
    
    return signals

@st.cache_data(ttl=300)
def get_egx30():
    """جلب بيانات مؤشر EGX30"""
    try:
        egx30 = yf.Ticker("^EGX30")
        hist = egx30.history(period="5d")
        if not hist.empty and len(hist) >= 2:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            change = ((current - prev) / prev) * 100
            return current, change
    except Exception as e:
        st.sidebar.warning(f"خطأ في جلب EGX30: {e}")
    return None, None

@st.cache_data(ttl=180)
def get_egyptian_stock(ticker: str, period: str = "1y"):
    """جلب بيانات السهم مع المؤشرات الفنية"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if df.empty:
            return None, None, ticker
        
        # إضافة المؤشرات الفنية
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['EMA_9'] = ta.ema(df['Close'], length=9)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # إضافة مؤشر MACD
        macd = ta.macd(df['Close'])
        if macd is not None:
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_Signal'] = macd['MACDs_12_26_9']
        
        # إضافة Bollinger Bands
        bb = ta.bbands(df['Close'], length=20)
        if bb is not None:
            df['BB_upper'] = bb['BBU_20_2.0']
            df['BB_middle'] = bb['BBM_20_2.0']
            df['BB_lower'] = bb['BBL_20_2.0']
        
        # متوسط حجم التداول
        df['Volume_SMA'] = ta.sma(df['Volume'], length=20)
        
        return df, stock.info, ticker
    except Exception as e:
        st.error(f"خطأ في جلب بيانات {ticker}: {str(e)}")
        return None, None, ticker

def create_advanced_chart(df: pd.DataFrame, ticker: str):
    """إنشاء رسم بياني متقدم مع مؤشرات متعددة"""
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05,
        row_heights=[0.5, 0.2, 0.15, 0.15],
        subplot_titles=(f"السعر - {ticker}", "RSI", "MACD", "حجم التداول")
    )
    
    # السعر مع Bollinger Bands
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name="السعر"
    ), row=1, col=1)
    
    # Bollinger Bands
    if 'BB_upper' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_upper'], name="BB Upper",
            line=dict(color='gray', dash='dash'), opacity=0.5
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_lower'], name="BB Lower",
            line=dict(color='gray', dash='dash'), opacity=0.5,
            fill='tonexty', fillcolor='rgba(128, 128, 128, 0.1)'
        ), row=1, col=1)
    
    # المتوسطات المتحركة
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA_20'], name="SMA 20",
        line=dict(color='orange', width=1.5)
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['EMA_9'], name="EMA 9",
        line=dict(color='cyan', width=1.5)
    ), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(
        x=df.index, y=df['RSI'], name="RSI",
        line=dict(color='magenta', width=2)
    ), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, row=2, col=1)
    fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, row=2, col=1)
    
    # MACD
    if 'MACD' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MACD'], name="MACD",
            line=dict(color='blue', width=1.5)
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MACD_Signal'], name="Signal",
            line=dict(color='red', width=1.5)
        ), row=3, col=1)
    
    # حجم التداول
    colors = ['red' if close < open else 'green' 
              for close, open in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], name="Volume",
        marker_color=colors, opacity=0.5
    ), row=4, col=1)
    
    # خط متوسط الحجم
    if 'Volume_SMA' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Volume_SMA'], name="Avg Volume",
            line=dict(color='yellow', width=1.5, dash='dot')
        ), row=4, col=1)
    
    # تحديث التنسيق
    fig.update_layout(
        height=800,
        template="plotly_dark",
        title_text=f"تحليل فني متقدم - {ticker}",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_xaxes(rangeslider_visible=False)
    fig.update_yaxes(title_text="السعر", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    fig.update_yaxes(title_text="Volume", row=4, col=1)
    
    return fig

def compare_stocks(ticker1: str, ticker2: str, period: str = "1y"):
    """مقارنة بين سهمين"""
    df1, _, _ = get_egyptian_stock(ticker1, period)
    df2, _, _ = get_egyptian_stock(ticker2, period)
    
    if df1 is None or df2 is None:
        return None
    
    # تطبيع الأداء (نقطة البداية = 100)
    norm1 = (df1['Close'] / df1['Close'].iloc[0]) * 100
    norm2 = (df2['Close'] / df2['Close'].iloc[0]) * 100
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=norm1.index, y=norm1,
        name=f"{ticker1} - {egyptian_stocks.get(ticker1, '')}",
        line=dict(width=3)
    ))
    fig.add_trace(go.Scatter(
        x=norm2.index, y=norm2,
        name=f"{ticker2} - {egyptian_stocks.get(ticker2, '')}",
        line=dict(width=3, dash='dash')
    ))
    
    fig.update_layout(
        title="مقارنة الأداء (100 = بداية الفترة)",
        template="plotly_dark",
        xaxis_title="التاريخ",
        yaxis_title="الأداء (%)",
        hovermode='x unified'
    )
    
    return fig

def export_to_excel(df: pd.DataFrame, ticker: str):
    """تصدير البيانات إلى Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'{ticker}_Data', index=True)
        
        # إضافة ورقة للمؤشرات الفنية
        technical_df = df[['Close', 'SMA_20', 'EMA_9', 'RSI', 'Volume']].tail(20)
        technical_df.to_excel(writer, sheet_name='Technical_Indicators', index=True)
    
    return output.getvalue()

# ====================== 5. الواجهة الرئيسية ======================
def main():
    # تهيئة الجلسة
    init_session_state()
    
    # الشريط الجانبي
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/thumb/2/2a/Egyptian_Exchange_logo.png/200px-Egyptian_Exchange_logo.png", 
                 use_container_width=True)
        
        st.markdown("## 🏦 البورصة المصرية")
        
        # عرض مؤشر EGX30
        egx30, egx30_change = get_egx30()
        if egx30:
            st.metric("📊 EGX30", f"{egx30:.2f}", f"{egx30_change:.2f}%")
        
        st.divider()
        
        # قائمة المفضلة
        st.subheader("⭐ أسهمي المفضلة")
        if st.session_state.favorite_stocks:
            for fav in st.session_state.favorite_stocks:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {fav}")
                with col2:
                    if st.button("❌", key=f"remove_{fav}"):
                        st.session_state.favorite_stocks.remove(fav)
                        st.rerun()
        else:
            st.info("لا توجد أسهم مفضلة. أضف من صفحة التحليل")
        
        st.divider()
        st.caption("⚠️ البيانات من Yahoo Finance")
        st.caption("🤖 التحليل بـ Google Gemini")
        st.caption("📈 للأغراض التعليمية فقط")
    
    # الصفحات
    page = st.radio(
        "📑 اختر القسم",
        ["🔍 تحليل سهم واحد", "📊 أداء الأسهم (صعود/هبوط)", "📰 أخبار وتحليل عام", "📈 مقارنة الأسهم"],
        horizontal=True
    )
    
    # ====================== صفحة 1: تحليل سهم واحد ======================
    if page == "🔍 تحليل سهم واحد":
        st.header("🔍 تحليل سهم فردي متقدم")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            selected = st.selectbox(
                "اختر السهم",
                options=list(egyptian_stocks.keys()),
                format_func=lambda x: f"{x} — {egyptian_stocks[x]}"
            )
        
        with col2:
            period = st.selectbox("الفترة", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)
        
        with col3:
            if st.button("🔄 تحديث", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        # إضافة للمفضلة
        if st.button(f"⭐ إضافة {selected} للمفضلة"):
            if selected not in st.session_state.favorite_stocks:
                st.session_state.favorite_stocks.append(selected)
                st.success(f"تمت إضافة {selected} للمفضلة")
        
        # جلب البيانات
        with st.spinner("جاري تحليل السهم..."):
            hist, info, ticker = get_egyptian_stock(selected, period)
        
        if hist is not None and not hist.empty:
            # المقاييس الأساسية
            curr_price = info.get('currentPrice') or hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else curr_price
            change_pct = ((curr_price - prev_price) / prev_price) * 100 if prev_price else 0
            last_rsi = hist['RSI'].iloc[-1]
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("💰 السعر الحالي", f"{curr_price:.2f} ج.م", f"{change_pct:.2f}%")
            col2.metric("📊 RSI (14)", f"{last_rsi:.1f}")
            col3.metric("🏢 الشركة", egyptian_stocks.get(ticker, ticker)[:20])
            col4.metric("📅 آخر تحديث", datetime.now().strftime("%H:%M:%S"))
            col5.metric("📈 أعلى/أدنى سنة", f"{info.get('fiftyTwoWeekHigh', 'N/A'):.0f}/{info.get('fiftyTwoWeekLow', 'N/A'):.0f}")
            
            # الملخص الفني
            signals = get_technical_summary(hist)
            st.info("📊 **الملخص الفني:** " + " | ".join(signals))
            
            # الرسم البياني المتقدم
            fig = create_advanced_chart(hist, ticker)
            st.plotly_chart(fig, use_container_width=True)
            
            # نقاط الدعم والمقاومة
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 نقاط المقاومة")
                recent_highs = hist['High'].tail(50).nlargest(3)
                for i, price in enumerate(recent_highs, 1):
                    st.write(f"R{i}: {price:.2f} ج.م")
            
            with col2:
                st.subheader("📉 نقاط الدعم")
                recent_lows = hist['Low'].tail(50).nsmallest(3)
                for i, price in enumerate(recent_lows, 1):
                    st.write(f"S{i}: {price:.2f} ج.م")
            
            # أزرار التحليل
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🤖 تحليل ذكي مفصل", type="primary", use_container_width=True):
                    with st.spinner("جاري التحليل باستخدام الذكاء الاصطناعي..."):
                        cache_key = f"{selected}_{datetime.now().strftime('%Y%m%d%H')}"
                        
                        if cache_key in st.session_state.analysis_cache:
                            analysis = st.session_state.analysis_cache[cache_key]
                        else:
                            prompt = f"""أنت محلل أسهم مصري محترف. حلل السهم {ticker} ({egyptian_stocks.get(ticker)}) 
                            
                            البيانات الفنية:
                            - السعر الحالي: {curr_price:.2f} جنيه
                            - RSI: {last_rsi:.1f}
                            - المتوسط المتحرك 20: {hist['SMA_20'].iloc[-1]:.2f}
                            - المتوسط الأسي 9: {hist['EMA_9'].iloc[-1]:.2f}
                            - التغير اليومي: {change_pct:.2f}%
                            
                            المطلوب:
                            1. تحليل الاتجاه العام
                            2. نقاط الدعم والمقاومة الرئيسية
                            3. تحليل RSI وحالة السوق
                            4. توصية واضحة (شراء/بيع/انتظار)
                            5. نسبة المخاطرة للصفقة
                            
                            الرد بالعربية بشكل احترافي ومختصر."""
                            
                            try:
                                response = model.generate_content(prompt)
                                analysis = response.text
                                st.session_state.analysis_cache[cache_key] = analysis
                                st.session_state.last_analysis[selected] = analysis
                            except Exception as e:
                                analysis = f"خطأ في التحليل: {str(e)}"
                        
                        st.markdown("### 📝 نتيجة التحليل")
                        st.success(analysis)
            
            with col2:
                if st.button("📊 تصدير البيانات", use_container_width=True):
                    excel_data = export_to_excel(hist, ticker)
                    st.download_button(
                        label="⬇️ تحميل Excel",
                        data=excel_data,
                        file_name=f"{ticker}_analysis.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_excel"
                    )
            
            with col3:
                if st.button("🔄 تحليل جديد", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
        
        else:
            st.error("❌ تعذر جلب البيانات. تأكد من صحة الرمز أو حاول تحديث الصفحة")
            st.info("💡 نصائح: \n1. تأكد من اتصال الإنترنت\n2. جرب رمز آخر مثل COMI.CA\n3. اضغط زر التحديث")
    
    # ====================== صفحة 2: أداء الأسهم ======================
    elif page == "📊 أداء الأسهم (صعود/هبوط)":
        st.header("📊 أداء الأسهم المصرية")
        
        if st.button("🔄 تحديث قائمة الأداء", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        with st.spinner("جاري تحليل أداء السوق..."):
            results = []
            progress_bar = st.progress(0)
            
            for idx, ticker in enumerate(egyptian_stocks.keys()):
                try:
                    df = yf.Ticker(ticker).history(period="5d")
                    if not df.empty and len(df) >= 2:
                        change = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                        results.append({
                            "الرمز": ticker,
                            "الاسم": egyptian_stocks[ticker],
                            "التغير %": round(change, 2),
                            "السعر": round(df['Close'].iloc[-1], 2),
                            "الحجم": int(df['Volume'].iloc[-1]) if not pd.isna(df['Volume'].iloc[-1]) else 0
                        })
                except Exception as e:
                    st.warning(f"خطأ في {ticker}: {e}")
                
                progress_bar.progress((idx + 1) / len(egyptian_stocks.keys()))
            
            progress_bar.empty()
        
        if results:
            df_perf = pd.DataFrame(results)
            
            # إحصائيات سريعة
            col1, col2, col3 = st.columns(3)
            col1.metric("📈 متوسط التغير", f"{df_perf['التغير %'].mean():.2f}%")
            col2.metric("🚀 أعلى صعود", f"{df_perf['التغير %'].max():.2f}%")
            col3.metric("📉 أعلى هبوط", f"{df_perf['التغير %'].min():.2f}%")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🚀 أقوى الأسهم صعوداً")
                gainers = df_perf.nlargest(8, "التغير %")
                st.dataframe(gainers, use_container_width=True, hide_index=True)
            
            with col2:
                st.subheader("🔻 أقوى الأسهم هبوطاً")
                losers = df_perf.nsmallest(8, "التغير %")
                st.dataframe(losers, use_container_width=True, hide_index=True)
            
            # رسم بياني للأداء
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_perf['الاسم'][:15],
                y=df_perf['التغير %'][:15],
                marker_color=['green' if x > 0 else 'red' for x in df_perf['التغير %'][:15]],
                text=df_perf['التغير %'][:15],
                textposition='auto'
            ))
            fig.update_layout(
                title="أداء أبرز 15 سهماً",
                template="plotly_dark",
                xaxis_title="السهم",
                yaxis_title="التغير (%)"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # تحليل عام بالسوق
            if st.button("📈 تحليل عام للسوق المصري", type="primary"):
                with st.spinner("جاري تحليل السوق..."):
                    prompt = f"""قم بتحليل عام للبورصة المصرية اليوم بناءً على البيانات التالية:
                    
                    متوسط تغير الأسهم: {df_perf['التغير %'].mean():.2f}%
                    أقوى الصاعدين: {gainers.head(3).to_dict('records')}
                    أقوى الهابطة: {losers.head(3).to_dict('records')}
                    
                    قدم تحليلاً شاملاً عن:
                    - اتجاه السوق العام
                    - القطاعات الأكثر نشاطاً
                    - توقعات قصيرة المدى
                    """
                    
                    try:
                        response = model.generate_content(prompt)
                        st.markdown("### 📊 تحليل السوق")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"خطأ: {e}")
        else:
            st.warning("لم يتم جلب بيانات كافية للتحليل")
    
    # ====================== صفحة 3: أخبار وتحليل عام ======================
    elif page == "📰 أخبار وتحليل عام":
        st.header("📰 أخبار وتحليل البورصة المصرية")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 📌 آخر مستجدات السوق المصري")
        with col2:
            if st.button("🔄 تحديث", use_container_width=True):
                st.rerun()
        
        # تحليل السوق
        prompt_analysis = """
        قدم تحليلاً شاملاً للبورصة المصرية (EGX) اليوم مع التركيز على:
        
        1. أداء مؤشر EGX30 وآخر المستويات
        2. القطاعات الأكثر تأثيراً (بنوك، عقارات، اتصالات)
        3. تأثير سعر الصرف وأسعار الفائدة
        4. أهم الصفقات والأخبار الاقتصادية
        5. توقعات الأداء للأسبوع القادم
        
        الرد بالعربية بشكل مهني وواضح.
        """
        
        with st.spinner("جاري تحليل السوق والأخبار..."):
            try:
                response = model.generate_content(prompt_analysis)
                st.markdown("### 📈 التحليل الفني والأساسي")
                st.info(response.text)
            except Exception as e:
                st.error(f"خطأ في التحليل: {e}")
        
        st.divider()
        
        # توصيات سريعة
        st.subheader("🎯 توصيات سريعة")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**✅ منطقة شراء (RSI منخفض)**")
            with st.spinner("جارٍ التحليل..."):
                low_rsi_stocks = []
                for ticker in list(egyptian_stocks.keys())[:10]:
                    df, _, _ = get_egyptian_stock(ticker, "1mo")
                    if df is not None and not df.empty and len(df) > 14:
                        rsi = df['RSI'].iloc[-1]
                        if rsi < 35:
                            low_rsi_stocks.append(f"{ticker} (RSI: {rsi:.1f})")
                if low_rsi_stocks:
                    for stock in low_rsi_stocks[:5]:
                        st.write(f"• {stock}")
                else:
                    st.write("لا توجد أسهم في منطقة ذروة بيع حالياً")
        
        with col2:
            st.markdown("**⚠️ منطقة بيع (RSI مرتفع)**")
            high_rsi_stocks = []
            for ticker in list(egyptian_stocks.keys())[:10]:
                df, _, _ = get_egyptian_stock(ticker, "1mo")
                if df is not None and not df.empty and len(df) > 14:
                    rsi = df['RSI'].iloc[-1]
                    if rsi > 65:
                        high_rsi_stocks.append(f"{ticker} (RSI: {rsi:.1f})")
            if high_rsi_stocks:
                for stock in high_rsi_stocks[:5]:
                    st.write(f"• {stock}")
            else:
                st.write("لا توجد أسهم في منطقة ذروة شراء حالياً")
        
        with col3:
            st.markdown("**📊 متابعة خاصة**")
            st.write("• تحركات الدولار")
            st.write("• قرارات البنك المركزي")
            st.write("• تطورات صندوق النقد")
    
    # ====================== صفحة 4: مقارنة الأسهم ======================
    elif page == "📈 مقارنة الأسهم":
        st.header("📈 مقارنة أداء الأسهم")
        
        col1, col2 = st.columns(2)
        with col1:
            stock1 = st.selectbox(
                "اختر السهم الأول",
                options=list(egyptian_stocks.keys()),
                format_func=lambda x: f"{x} — {egyptian_stocks[x]}",
                key="compare1"
            )
        
        with col2:
            stock2 = st.selectbox(
                "اختر السهم الثاني",
                options=list(egyptian_stocks.keys()),
                format_func=lambda x: f"{x} — {egyptian_stocks[x]}",
                index=1,
                key="compare2"
            )
        
        period_comp = st.selectbox(
            "فترة المقارنة",
            ["1mo", "3mo", "6mo", "1y"],
            index=2
        )
        
        if st.button("📊 عرض المقارنة", type="primary"):
            with st.spinner("جاري تحليل ومقارنة الأسهم..."):
                # رسم بياني للمقارنة
                fig_comp = compare_stocks(stock1, stock2, period_comp)
                if fig_comp:
                    st.plotly_chart(fig_comp, use_container_width=True)
                    
                    # إحصائيات المقارنة
                    df1, _, _ = get_egyptian_stock(stock1, period_comp)
                    df2, _, _ = get_egyptian_stock(stock2, period_comp)
                    
                    if df1 is not None and df2 is not None:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            return1 = ((df1['Close'].iloc[-1] - df1['Close'].iloc[0]) / df1['Close'].iloc[0]) * 100
                            return2 = ((df2['Close'].iloc[-1] - df2['Close'].iloc[0]) / df2['Close'].iloc[0]) * 100
                            st.metric(f"عائد {stock1}", f"{return1:.1f}%")
                            st.metric(f"عائد {stock2}", f"{return2:.1f}%")
                        
                        with col2:
                            volatility1 = df1['Close'].pct_change().std() * 100
                            volatility2 = df2['Close'].pct_change().std() * 100
                            st.metric(f"تذبذب {stock1}", f"{volatility1:.2f}%")
                            st.metric(f"تذبذب {stock2}", f"{volatility2:.2f}%")
                        
                        with col3:
                            st.metric("🏆 الفائز", stock1 if return1 > return2 else stock2)
                            
                            # تحليل Gemini للمقارنة
                            if st.button("🤖 تحليل المقارنة"):
                                prompt_comp = f"""
                                قارن بين السهمين التاليين:
                                {stock1} ({egyptian_stocks[stock1]}) - عائد: {return1:.1f}% - تذبذب: {volatility1:.2f}%
                                {stock2} ({egyptian_stocks[stock2]}) - عائد: {return2:.1f}% - تذبذب: {volatility2:.2f}%
                                
                                أيهما أفضل للاستثمار حالياً؟ مع ذكر الأسباب.
                                """
                                try:
                                    resp = model.generate_content(prompt_comp)
                                    st.write("### 📊 تحليل المقارنة")
                                    st.write(resp.text)
                                except Exception as e:
                                    st.error(f"خطأ: {e}")

# ====================== 6. تشغيل التطبيق ======================
if __name__ == "__main__":
    main()
