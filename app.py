"""
📈 محلل الأسهم المصرية بالذكاء الاصطناعي
Egyptian Stock Analyst with AI
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas_ta as ta
from datetime import datetime
import requests
from typing import Dict, List, Optional
import time

# ==================== إعداد الصفحة ====================
st.set_page_config(
    page_title="محلل الأسهم المصري - AI Analyst 📈",
    page_icon="🇪🇬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== تهيئة الجلسة ====================
def init_session_state():
    """تهيئة متغيرات الجلسة"""
    if 'favorite_stocks' not in st.session_state:
        st.session_state.favorite_stocks = []
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()

init_session_state()

# ==================== قائمة الأسهم المصرية ====================
EGYPTIAN_STOCKS = {
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
    "SKPC.CA": "سيدبك",
    "PHDC.CA": "بالم هيلز للتعمير",
}

# ==================== دوال جلب البيانات ====================
@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_data(ticker: str, period: str = "6mo") -> Optional[pd.DataFrame]:
    """جلب بيانات السهم من Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if df.empty:
            return None
        
        # إضافة المؤشرات الفنية
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['Volume_SMA'] = ta.sma(df['Volume'], length=20)
        
        # MACD
        macd = ta.macd(df['Close'])
        if macd is not None:
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_Signal'] = macd['MACDs_12_26_9']
        
        return df
    except Exception as e:
        st.error(f"خطأ في جلب بيانات {ticker}: {str(e)}")
        return None

@st.cache_data(ttl=300)
def get_market_summary() -> Dict:
    """الحصول على ملخص السوق"""
    results = []
    for ticker in EGYPTIAN_STOCKS.keys():
        try:
            df = fetch_stock_data(ticker, "5d")
            if df is not None and len(df) >= 2:
                current = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                results.append({
                    'ticker': ticker,
                    'name': EGYPTIAN_STOCKS[ticker],
                    'price': current,
                    'change': change
                })
            time.sleep(0.5)  # تجنب الحظر
        except:
            continue
    
    if results:
        df_results = pd.DataFrame(results)
        return {
            'avg_change': df_results['change'].mean(),
            'gainers': df_results.nlargest(3, 'change'),
            'losers': df_results.nsmallest(3, 'change'),
            'advance_decline': (df_results['change'] > 0).sum() / len(df_results) * 100
        }
    return {}

# ==================== دوال الرسم البياني ====================
def create_price_chart(df: pd.DataFrame, ticker: str):
    """إنشاء رسم بياني للسعر مع المؤشرات"""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f"📈 سعر {ticker}", "📊 RSI", "📉 MACD")
    )
    
    # السعر والمتوسطات
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Close'],
        name="سعر الإغلاق",
        line=dict(color='#00ff87', width=2)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA_20'],
        name="SMA 20",
        line=dict(color='orange', width=1.5, dash='dash')
    ), row=1, col=1)
    
    if 'SMA_50' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['SMA_50'],
            name="SMA 50",
            line=dict(color='purple', width=1.5, dash='dot')
        ), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(
        x=df.index, y=df['RSI'],
        name="RSI",
        line=dict(color='#ff006e', width=2)
    ), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    # MACD
    if 'MACD' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MACD'],
            name="MACD",
            line=dict(color='#00b4ff', width=1.5)
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MACD_Signal'],
            name="Signal",
            line=dict(color='#ffb703', width=1.5)
        ), row=3, col=1)
    
    fig.update_layout(
        height=700,
        template="plotly_dark" if st.session_state.dark_mode else "plotly_white",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_xaxes(title_text="التاريخ", row=3, col=1)
    fig.update_yaxes(title_text="السعر", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    
    return fig

def create_volume_chart(df: pd.DataFrame):
    """إنشاء رسم بياني لحجم التداول"""
    colors = ['#00ff87' if close >= open else '#ff006e' 
              for close, open in zip(df['Close'], df['Open'])]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'],
        name="حجم التداول",
        marker_color=colors,
        opacity=0.7
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Volume_SMA'],
        name="متوسط الحجم",
        line=dict(color='yellow', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title="📊 حجم التداول",
        xaxis_title="التاريخ",
        yaxis_title="الكمية",
        template="plotly_dark" if st.session_state.dark_mode else "plotly_white",
        height=400
    )
    
    return fig

# ==================== دوال التحليل ====================
def analyze_stock(df: pd.DataFrame, ticker: str) -> Dict:
    """تحليل السهم وإعطاء توصيات"""
    if df is None or df.empty:
        return {'signal': 'error', 'message': 'لا توجد بيانات كافية'}
    
    last_price = df['Close'].iloc[-1]
    last_rsi = df['RSI'].iloc[-1]
    sma_20 = df['SMA_20'].iloc[-1]
    sma_50 = df['SMA_50'].iloc[-1] if 'SMA_50' in df.columns else last_price
    
    # تحليل RSI
    rsi_signal = "محايد"
    if last_rsi > 70:
        rsi_signal = "ذروة شراء - خطر"
    elif last_rsi < 30:
        rsi_signal = "ذروة بيع - فرصة"
    
    # تحليل المتوسطات
    ma_signal = "محايد"
    if last_price > sma_20 and last_price > sma_50:
        ma_signal = "اتجاه صاعد قوي"
    elif last_price > sma_20:
        ma_signal = "اتجاه صاعد ضعيف"
    elif last_price < sma_20 and last_price < sma_50:
        ma_signal = "اتجاه هابط"
    
    # تحليل MACD
    macd_signal = "محايد"
    if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
        if df['MACD'].iloc[-1] > df['MACD_Signal'].iloc[-1]:
            macd_signal = "إيجابي - إشارة شراء"
        else:
            macd_signal = "سلبي - إشارة بيع"
    
    # التوصية النهائية
    if last_rsi < 30 and last_price > sma_20:
        recommendation = "🟢 شراء"
        confidence = "مرتفعة"
    elif last_rsi > 70 and last_price < sma_20:
        recommendation = "🔴 بيع"
        confidence = "مرتفعة"
    elif last_rsi < 40 and last_price > sma_20:
        recommendation = "🟡 تراكم"
        confidence = "متوسطة"
    elif last_rsi > 60 and last_price < sma_20:
        recommendation = "🟠 تصريف"
        confidence = "متوسطة"
    else:
        recommendation = "⚪ انتظار"
        confidence = "منخفضة"
    
    return {
        'signal': recommendation,
        'confidence': confidence,
        'rsi': last_rsi,
        'rsi_signal': rsi_signal,
        'ma_signal': ma_signal,
        'macd_signal': macd_signal,
        'current_price': last_price,
        'sma_20': sma_20,
        'sma_50': sma_50
    }

# ==================== الواجهة الرئيسية ====================
def main():
    # شريط جانبي
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/thumb/2/2a/Egyptian_Exchange_logo.png/200px-Egyptian_Exchange_logo.png", 
                 use_container_width=True)
        
        st.markdown("# 🏦 بورصة مصر")
        st.markdown("---")
        
        # وضع العرض
        st.session_state.dark_mode = st.toggle("🌙 الوضع المظلم", value=st.session_state.dark_mode)
        
        st.markdown("---")
        
        # ملخص السوق
        st.markdown("### 📊 ملخص السوق")
        with st.spinner("جاري تحديث البيانات..."):
            market_summary = get_market_summary()
        
        if market_summary:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📈 متوسط التغير", f"{market_summary.get('avg_change', 0):+.2f}%")
            with col2:
                st.metric("📊 نسبة الصاعدين", f"{market_summary.get('advance_decline', 0):.0f}%")
        
        st.markdown("---")
        
        # اختيار السهم
        selected_ticker = st.selectbox(
            "🔍 اختر السهم",
            options=list(EGYPTIAN_STOCKS.keys()),
            format_func=lambda x: f"{x} - {EGYPTIAN_STOCKS[x]}"
        )
        
        # فترة التحليل
        period = st.selectbox(
            "📅 الفترة الزمنية",
            ["1mo", "3mo", "6mo", "1y"],
            index=2
        )
        
        st.markdown("---")
        
        # أسهم مفضلة
        st.markdown("### ⭐ أسهمي المفضلة")
        if selected_ticker not in st.session_state.favorite_stocks:
            if st.button(f"➕ إضافة {selected_ticker}"):
                st.session_state.favorite_stocks.append(selected_ticker)
                st.rerun()
        
        for fav in st.session_state.favorite_stocks:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"• {fav}")
            with col2:
                if st.button("❌", key=fav):
                    st.session_state.favorite_stocks.remove(fav)
                    st.rerun()
        
        st.markdown("---")
        st.caption("📊 البيانات من Yahoo Finance")
        st.caption("⚠️ للأغراض التعليمية فقط")
    
    # المحتوى الرئيسي
    st.title("📈 محلل الأسهم المصري بالذكاء الاصطناعي")
    st.markdown(f"### 🎯 تحليل سهم {selected_ticker} - {EGYPTIAN_STOCKS[selected_ticker]}")
    st.markdown(f"🕒 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("---")
    
    # جلب البيانات
    with st.spinner("جاري تحليل السهم..."):
        df = fetch_stock_data(selected_ticker, period)
    
    if df is not None and not df.empty:
        # تحليل السهم
        analysis = analyze_stock(df, selected_ticker)
        
        # بطاقات المعلومات السريعة
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 السعر الحالي",
                f"{analysis['current_price']:.2f} ج.م",
                delta=f"{((analysis['current_price'] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100):+.2f}%" if len(df) > 1 else None
            )
        
        with col2:
            st.metric(
                "📊 RSI",
                f"{analysis['rsi']:.1f}",
                delta=analysis['rsi_signal']
            )
        
        with col3:
            st.metric(
                "📈 SMA 20",
                f"{analysis['sma_20']:.2f}"
            )
        
        with col4:
            st.metric(
                "🎯 التوصية",
                analysis['signal'],
                delta=analysis['confidence']
            )
        
        st.markdown("---")
        
        # تفاصيل التحليل
        with st.expander("📋 تفاصيل التحليل الفني", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📊 مؤشر القوة النسبية (RSI)**")
                st.write(f"القيمة: {analysis['rsi']:.1f}")
                st.write(f"التفسير: {analysis['rsi_signal']}")
                
                # شريط تقدم RSI
                rsi_percent = analysis['rsi'] / 100
                st.progress(rsi_percent)
            
            with col2:
                st.markdown("**📈 المتوسطات المتحركة**")
                st.write(f"SMA 20: {analysis['sma_20']:.2f}")
                st.write(f"SMA 50: {analysis['sma_50']:.2f}")
                st.write(f"التحليل: {analysis['ma_signal']}")
            
            with col3:
                st.markdown("**🎯 المؤشرات الأخرى**")
                st.write(f"MACD: {analysis['macd_signal']}")
                st.write(f"ثقة التوصية: {analysis['confidence']}")
        
        # الرسم البياني للسعر
        st.markdown("### 📈 الرسم البياني")
        price_chart = create_price_chart(df, selected_ticker)
        st.plotly_chart(price_chart, use_container_width=True)
        
        # الرسم البياني لحجم التداول
        volume_chart = create_volume_chart(df)
        st.plotly_chart(volume_chart, use_container_width=True)
        
        # نقاط الدعم والمقاومة
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 نقاط المقاومة")
            recent_highs = df['High'].tail(50).nlargest(3)
            for i, price in enumerate(recent_highs, 1):
                st.write(f"**R{i}:** {price:.2f} ج.م")
        
        with col2:
            st.markdown("### 📉 نقاط الدعم")
            recent_lows = df['Low'].tail(50).nsmallest(3)
            for i, price in enumerate(recent_lows, 1):
                st.write(f"**S{i}:** {price:.2f} ج.م")
        
        # جدول البيانات
        with st.expander("📊 عرض البيانات التفصيلية"):
            display_df = df.tail(20).copy()
            display_df.index = display_df.index.strftime('%Y-%m-%d')
            st.dataframe(display_df, use_container_width=True)
        
        # تحركات الأسهم المشابهة
        st.markdown("---")
        st.markdown("### 🔄 تحركات السوق اليوم")
        
        if market_summary:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🚀 أقوى الصاعدين**")
                gainers = market_summary.get('gainers', pd.DataFrame())
                if not gainers.empty:
                    for _, row in gainers.iterrows():
                        st.write(f"• {row['ticker']}: {row['change']:+.2f}% ({row['price']:.2f})")
            
            with col2:
                st.markdown("**📉 أقوى الهابطة**")
                losers = market_summary.get('losers', pd.DataFrame())
                if not losers.empty:
                    for _, row in losers.iterrows():
                        st.write(f"• {row['ticker']}: {row['change']:+.2f}% ({row['price']:.2f})")
        
    else:
        st.error("❌ لا يمكن جلب البيانات. يرجى التحقق من الاتصال بالإنترنت أو المحاولة مرة أخرى.")
        st.info("💡 نصائح:\n• تأكد من اتصال الإنترنت\n• جرب تحديث الصفحة (F5)\n• اختر سهماً آخر مثل COMI.CA")

# ==================== تشغيل التطبيق ====================
if __name__ == "__main__":
    main()
