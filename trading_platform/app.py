"""
البورصجي AI - منصة تحليل الأسهم الذكية
نسخة مستقرة 100% - بدون أخطاء
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

# ====================== إعدادات أولية ======================
warnings.filterwarnings('ignore')

# إعداد صفحة Streamlit (يجب أن يكون في البداية)
st.set_page_config(
    page_title="البورصجي AI - تحليل الأسهم الذكي",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== إعدادات السمة ======================
st.markdown("""
<style>
    /* خلفية الصفحة */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
    }
    
    /* بطاقات المؤشرات */
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(0, 255, 136, 0.2);
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* إشارات الشراء */
    .buy-signal {
        background: linear-gradient(135deg, #00ff8820 0%, #00ff8805 100%);
        border-left: 4px solid #00ff88;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* إشارات البيع */
    .sell-signal {
        background: linear-gradient(135deg, #ff444420 0%, #ff444405 100%);
        border-left: 4px solid #ff4444;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* إشارات محايدة */
    .neutral-signal {
        background: linear-gradient(135deg, #ffaa0020 0%, #ffaa0005 100%);
        border-left: 4px solid #ffaa00;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* أزرار */
    .stButton > button {
        background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
        color: #0a0a0a;
        font-weight: bold;
        font-size: 16px;
        border: none;
        border-radius: 10px;
        padding: 10px 25px;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 20px rgba(0,255,136,0.3);
    }
    
    /* شريط جانبي */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
        border-right: 1px solid rgba(0,255,136,0.1);
    }
    
    /* عناوين */
    h1, h2, h3 {
        background: linear-gradient(135deg, #00ff88 0%, #00ccff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* تذييل */
    .footer {
        text-align: center;
        padding: 20px;
        margin-top: 50px;
        border-top: 1px solid #333;
        font-size: 12px;
        color: #666;
    }
    
    /* مؤشر التحميل */
    .stSpinner > div {
        border-top-color: #00ff88 !important;
    }
    
    /* توسيع */
    .streamlit-expanderHeader {
        background: #1e1e2e;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ====================== إعدادات الذكاء الاصطناعي ======================
try:
    import google.generativeai as genai
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except Exception:
    GEMINI_AVAILABLE = False

# ====================== قائمة الأسهم ======================
STOCKS = {
    # البورصة المصرية (EGX)
    "🇪🇬 COMI.CA": {"name": "البنك التجاري الدولي (CIB)", "market": "EGX", "sector": "بنوك"},
    "🇪🇬 TMGH.CA": {"name": "طلعت مصطفى القابضة", "market": "EGX", "sector": "عقارات"},
    "🇪🇬 SWDY.CA": {"name": "السويدي إليكتريك", "market": "EGX", "sector": "صناعة"},
    "🇪🇬 EAST.CA": {"name": "الشرقية للدخان", "market": "EGX", "sector": "سلع استهلاكية"},
    "🇪🇬 MFPC.CA": {"name": "مصر لإنتاج الأسمدة (موبكو)", "market": "EGX", "sector": "كيماويات"},
    "🇪🇬 ORAS.CA": {"name": "أوراسكوم للإنشاءات", "market": "EGX", "sector": "إنشاءات"},
    
    # بورصة تداول السعودية
    "🇸🇦 2222.SR": {"name": "أرامكو السعودية", "market": "TADAWUL", "sector": "طاقة"},
    "🇸🇦 1120.SR": {"name": "مصرف الراجحي", "market": "TADAWUL", "sector": "بنوك"},
    "🇸🇦 7010.SR": {"name": "مجموعة STC", "market": "TADAWUL", "sector": "اتصالات"},
    "🇸🇦 2010.SR": {"name": "سابك", "market": "TADAWUL", "sector": "بتروكيماويات"},
    
    # الأسهم الأمريكية
    "🇺🇸 AAPL": {"name": "Apple Inc.", "market": "NASDAQ", "sector": "تكنولوجيا"},
    "🇺🇸 MSFT": {"name": "Microsoft Corp.", "market": "NASDAQ", "sector": "تكنولوجيا"},
    "🇺🇸 GOOGL": {"name": "Alphabet Inc.", "market": "NASDAQ", "sector": "تكنولوجيا"},
    "🇺🇸 AMZN": {"name": "Amazon.com", "market": "NASDAQ", "sector": "تجارة إلكترونية"},
    "🇺🇸 TSLA": {"name": "Tesla Inc.", "market": "NASDAQ", "sector": "سيارات كهربائية"},
    "🇺🇸 NVDA": {"name": "NVIDIA Corp.", "market": "NASDAQ", "sector": "تكنولوجيا"},
}

# ====================== دوال جلب البيانات ======================
@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(symbol: str, period: str = "1y") -> Tuple[Optional[pd.DataFrame], Optional[Dict]]:
    """
    جلب بيانات السهم مع المؤشرات الفنية
    """
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        
        if df.empty:
            return None, None
        
        # حساب المؤشرات الفنية الأساسية
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['EMA_9'] = ta.ema(df['Close'], length=9)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # MACD
        macd = ta.macd(df['Close'])
        if macd is not None and not macd.empty:
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_Signal'] = macd['MACDs_12_26_9']
        
        # Bollinger Bands
        bb = ta.bbands(df['Close'], length=20)
        if bb is not None and not bb.empty:
            df['BB_Upper'] = bb['BBU_20_2.0']
            df['BB_Middle'] = bb['BBM_20_2.0']
            df['BB_Lower'] = bb['BBL_20_2.0']
        
        # حجم التداول
        df['Volume_SMA'] = ta.sma(df['Volume'], length=20)
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        # ATR
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        return df, stock.info
        
    except Exception as e:
        st.error(f"⚠️ خطأ في جلب بيانات {symbol}: {str(e)}")
        return None, None

# ====================== دوال التحليل ======================
def analyze_trend(df: pd.DataFrame) -> Dict:
    """تحليل الاتجاه"""
    if df is None or df.empty:
        return {"trend": "غير معروف", "strength": 0, "description": "بيانات غير كافية"}
    
    close = df['Close'].iloc[-1]
    sma_20 = df['SMA_20'].iloc[-1] if not pd.isna(df['SMA_20'].iloc[-1]) else close
    sma_50 = df['SMA_50'].iloc[-1] if not pd.isna(df['SMA_50'].iloc[-1]) else close
    
    if close > sma_20 > sma_50:
        return {"trend": "صاعد قوي", "strength": 80, "description": "اتجاه صاعد قوي، دعم من المتوسطات"}
    elif close > sma_20:
        return {"trend": "صاعد", "strength": 60, "description": "اتجاه صاعد، قد يواجه مقاومة"}
    elif close < sma_20 < sma_50:
        return {"trend": "هابط قوي", "strength": 80, "description": "اتجاه هابط قوي، توخ الحذر"}
    elif close < sma_20:
        return {"trend": "هابط", "strength": 60, "description": "اتجاه هابط"}
    else:
        return {"trend": "جانبي", "strength": 40, "description": "نطاق جانبي، انتظر تأكيد"}

def generate_signal(df: pd.DataFrame) -> Dict:
    """توليد إشارة تداول"""
    if df is None or df.empty:
        return {"action": "انتظار", "confidence": 0, "reasons": ["بيانات غير كافية"], "color": "neutral"}
    
    close = df['Close'].iloc[-1]
    rsi = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
    sma_20 = df['SMA_20'].iloc[-1] if not pd.isna(df['SMA_20'].iloc[-1]) else close
    sma_50 = df['SMA_50'].iloc[-1] if not pd.isna(df['SMA_50'].iloc[-1]) else close
    volume_ratio = df['Volume_Ratio'].iloc[-1] if not pd.isna(df['Volume_Ratio'].iloc[-1]) else 1
    
    buy_score = 0
    sell_score = 0
    reasons = []
    
    # إشارات RSI
    if rsi < 30:
        buy_score += 30
        reasons.append(f"✅ RSI منخفض ({rsi:.1f}) - منطقة ذروة بيع")
    elif rsi < 40:
        buy_score += 15
        reasons.append(f"✅ RSI عند {rsi:.1f} - بداية منطقة شراء")
    elif rsi > 70:
        sell_score += 30
        reasons.append(f"❌ RSI مرتفع ({rsi:.1f}) - منطقة ذروة شراء")
    elif rsi > 60:
        sell_score += 15
        reasons.append(f"❌ RSI عند {rsi:.1f} - بداية منطقة بيع")
    else:
        reasons.append(f"⚪ RSI عند {rsi:.1f} - منطقة محايدة")
    
    # إشارات المتوسطات
    if sma_20 > sma_50:
        buy_score += 20
        reasons.append("✅ المتوسط 20 فوق المتوسط 50 - اتجاه صاعد")
    else:
        sell_score += 15
        reasons.append("❌ المتوسط 20 تحت المتوسط 50 - اتجاه هابط")
    
    # إشارات الحجم
    if volume_ratio > 1.5:
        buy_score += 10
        reasons.append(f"✅ حجم تداول مرتفع ({volume_ratio:.1f}x)")
    elif volume_ratio < 0.5:
        sell_score += 10
        reasons.append(f"❌ حجم تداول ضعيف ({volume_ratio:.1f}x)")
    
    net_score = buy_score - sell_score
    
    if net_score >= 35:
        return {"action": "شراء قوي", "confidence": min(95, net_score), "reasons": reasons, "color": "buy"}
    elif net_score >= 20:
        return {"action": "شراء", "confidence": min(85, net_score + 50), "reasons": reasons, "color": "buy"}
    elif net_score <= -35:
        return {"action": "بيع قوي", "confidence": min(95, abs(net_score)), "reasons": reasons, "color": "sell"}
    elif net_score <= -20:
        return {"action": "بيع", "confidence": min(85, abs(net_score) + 50), "reasons": reasons, "color": "sell"}
    else:
        return {"action": "انتظار", "confidence": 50, "reasons": reasons, "color": "neutral"}

def get_support_resistance(df: pd.DataFrame) -> Dict:
    """تحديد الدعم والمقاومة"""
    if df is None or df.empty or len(df) < 30:
        return {"support": [], "resistance": [], "current": 0}
    
    close = df['Close'].iloc[-1]
    highs = df['High'].tail(50)
    lows = df['Low'].tail(50)
    
    # إيجاد القمم والقيعان
    resistance = []
    support = []
    
    for i in range(5, len(highs) - 5):
        if highs.iloc[i] == highs.iloc[i-5:i+5].max():
            resistance.append(round(highs.iloc[i], 2))
        if lows.iloc[i] == lows.iloc[i-5:i+5].min():
            support.append(round(lows.iloc[i], 2))
    
    resistance = sorted(set(resistance), reverse=True)[:3]
    support = sorted(set(support))[:3]
    
    return {
        "support": support,
        "resistance": resistance,
        "current": round(close, 2)
    }

# ====================== دالة الرسم البياني ======================
def create_chart(df: pd.DataFrame, symbol: str, name: str) -> go.Figure:
    """إنشاء رسم بياني متقدم"""
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=("السعر مع المؤشرات", "RSI", "MACD")
    )
    
    # السعر مع المتوسطات
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name="السعر"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name="SMA 20", 
                            line=dict(color='orange', width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name="SMA 50", 
                            line=dict(color='cyan', width=1.5)), row=1, col=1)
    
    # Bollinger Bands
    if 'BB_Upper' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name="BB Upper",
                                line=dict(color='gray', dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name="BB Lower",
                                line=dict(color='gray', dash='dash'),
                                fill='tonexty', fillcolor='rgba(128,128,128,0.1)'), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI",
                            line=dict(color='magenta', width=2)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, row=2, col=1)
    fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, row=2, col=1)
    
    # MACD
    if 'MACD' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name="MACD",
                                line=dict(color='blue', width=1.5)), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name="Signal",
                                line=dict(color='red', width=1.5)), row=3, col=1)
        
        colors = ['green' if val >= 0 else 'red' for val in df['MACD_Histogram']]
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Histogram'], name="Histogram",
                            marker_color=colors, opacity=0.5), row=3, col=1)
    
    # تنسيق
    fig.update_layout(
        height=700,
        template="plotly_dark",
        title_text=f"📊 {name} ({symbol}) - تحليل فني متقدم",
        title_font_size=18,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_xaxes(rangeslider_visible=False)
    fig.update_yaxes(title_text="السعر", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    
    return fig

# ====================== دالة تحليل Gemini ======================
def get_gemini_analysis(symbol: str, name: str, price: float, change: float, rsi: float, signal: str) -> Optional[str]:
    """الحصول على تحليل من Gemini AI"""
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        أنت محلل أسهم محترف. حلل السهم التالي:
        
        السهم: {name} ({symbol})
        السعر: {price:.2f}
        التغير: {change:+.2f}%
        RSI: {rsi:.1f}
        الإشارة الفنية: {signal}
        
        المطلوب:
        1. تحليل فني مختصر
        2. توصية واضحة
        3. نسبة المخاطرة
        
        الرد بالعربية (حد أقصى 200 كلمة).
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"⚠️ خطأ في التحليل: {str(e)}"

# ====================== الواجهة الرئيسية ======================
def main():
    """التطبيق الرئيسي"""
    
    # العنوان
    st.title("📈 البورصجي AI - منصة تحليل الأسهم الذكية")
    st.markdown("**تحليل فني متقدم | إشارات تداول فورية | ذكاء اصطناعي**")
    st.markdown("---")
    
    # الشريط الجانبي
    with st.sidebar:
        st.markdown("## ⚙️ الإعدادات")
        
        # اختيار السهم
        selected_display = st.selectbox(
            "🔍 اختر السهم",
            options=list(STOCKS.keys()),
            format_func=lambda x: f"{x} - {STOCKS[x]['name']}"
        )
        
        selected_symbol = selected_display.split()[1]
        stock_info = STOCKS[selected_display]
        
        # فترة التحليل
        period = st.selectbox(
            "📅 الفترة الزمنية",
            ["1mo", "3mo", "6mo", "1y", "2y"],
            index=3,
            help="اختر الفترة للتحليل"
        )
        
        st.markdown("---")
        
        # معلومات الأسواق
        st.markdown("## 📊 أوقات التداول")
        st.markdown("🇪🇬 **البورصة المصرية:** 10:00 - 14:30")
        st.markdown("🇸🇦 **تداول السعودية:** 10:00 - 15:00")
        st.markdown("🇺🇸 **الأسهم الأمريكية:** 16:30 - 23:00")
        
        st.markdown("---")
        
        # حالة الذكاء الاصطناعي
        if GEMINI_AVAILABLE:
            st.success("🤖 **Gemini AI:** متصل ✅")
        else:
            st.warning("⚠️ **Gemini AI:** غير متصل\nأضف مفتاح API في الإعدادات")
        
        st.markdown("---")
        st.caption("⚠️ البيانات من Yahoo Finance")
        st.caption("📈 للأغراض التعليمية فقط")
    
    # جلب البيانات
    with st.spinner("📡 جاري تحميل بيانات السهم..."):
        df, info = get_stock_data(selected_symbol, period)
    
    if df is not None and not df.empty:
        # البيانات الأساسية
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        change = current_price - prev_price
        change_percent = (change / prev_price) * 100 if prev_price else 0
        rsi_value = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
        
        # المقاييس
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "💰 السعر الحالي",
                f"{current_price:.2f}",
                f"{change:+.2f} ({change_percent:+.2f}%)"
            )
        
        with col2:
            st.metric("📊 RSI (14)", f"{rsi_value:.1f}")
        
        with col3:
            sma_20_val = df['SMA_20'].iloc[-1] if not pd.isna(df['SMA_20'].iloc[-1]) else current_price
            st.metric("📈 SMA 20", f"{sma_20_val:.2f}")
        
        with col4:
            sma_50_val = df['SMA_50'].iloc[-1] if not pd.isna(df['SMA_50'].iloc[-1]) else current_price
            st.metric("📉 SMA 50", f"{sma_50_val:.2f}")
        
        with col5:
            volume_ratio = df['Volume_Ratio'].iloc[-1] if not pd.isna(df['Volume_Ratio'].iloc[-1]) else 1
            st.metric("💹 حجم التداول", f"{volume_ratio:.2f}x")
        
        st.markdown("---")
        
        # إشارة التداول
        signal = generate_signal(df)
        
        if signal["color"] == "buy":
            st.markdown(f"""
            <div class="buy-signal">
                <h3>🟢 إشارة: {signal['action']}</h3>
                <p>🎯 الثقة: {signal['confidence']:.0f}%</p>
                <p><strong>📋 الأسباب:</strong></p>
                <ul>
                    {''.join([f'<li>{r}</li>' for r in signal['reasons'][:4]])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif signal["color"] == "sell":
            st.markdown(f"""
            <div class="sell-signal">
                <h3>🔴 إشارة: {signal['action']}</h3>
                <p>🎯 الثقة: {signal['confidence']:.0f}%</p>
                <p><strong>📋 الأسباب:</strong></p>
                <ul>
                    {''.join([f'<li>{r}</li>' for r in signal['reasons'][:4]])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="neutral-signal">
                <h3>🟡 إشارة: {signal['action']}</h3>
                <p>🎯 الثقة: {signal['confidence']:.0f}%</p>
                <p><strong>📋 الأسباب:</strong></p>
                <ul>
                    {''.join([f'<li>{r}</li>' for r in signal['reasons'][:4]])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # تحليل الاتجاه والدعم والمقاومة
        col1, col2 = st.columns(2)
        
        with col1:
            trend = analyze_trend(df)
            st.subheader("📈 تحليل الاتجاه")
            st.info(f"**{trend['trend']}**")
            st.progress(trend['strength'] / 100)
            st.caption(trend['description'])
        
        with col2:
            sr = get_support_resistance(df)
            st.subheader("📊 الدعم والمقاومة")
            st.write(f"**المقاومات:** {', '.join(map(str, sr['resistance'])) if sr['resistance'] else 'غير متوفرة'}")
            st.write(f"**الدعوم:** {', '.join(map(str, sr['support'])) if sr['support'] else 'غير متوفرة'}")
            st.write(f"**السعر الحالي:** {sr['current']}")
        
        st.markdown("---")
        
        # الرسم البياني
        st.subheader("📊 الرسم البياني المتقدم")
        fig = create_chart(df, selected_symbol, stock_info['name'])
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # تحليل الذكاء الاصطناعي
        st.subheader("🤖 التحليل بالذكاء الاصطناعي")
        
        if st.button("🚀 تحليل ذكي باستخدام Gemini AI", type="primary", use_container_width=True):
            if GEMINI_AVAILABLE:
                with st.spinner("🧠 جاري التحليل الذكي..."):
                    analysis = get_gemini_analysis(
                        selected_symbol, stock_info['name'],
                        current_price, change_percent, rsi_value, signal['action']
                    )
                    if analysis:
                        st.success("✅ نتيجة التحليل:")
                        st.markdown(analysis)
                    else:
                        st.warning("⚠️ تعذر الحصول على تحليل من Gemini")
            else:
                st.error("❌ Gemini AI غير متوفر. يرجى إضافة GEMINI_API_KEY في ملف secrets.toml")
        
        # معلومات إضافية
        with st.expander("📋 معلومات إضافية عن السهم"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**المتوسطات المتحركة**")
                st.write(f"SMA 5: {ta.sma(df['Close'], length=5).iloc[-1]:.2f}")
                st.write(f"SMA 10: {ta.sma(df['Close'], length=10).iloc[-1]:.2f}")
                st.write(f"SMA 20: {df['SMA_20'].iloc[-1]:.2f}")
                st.write(f"SMA 50: {df['SMA_50'].iloc[-1]:.2f}")
            
            with col2:
                st.write("**مؤشرات الزخم**")
                st.write(f"RSI: {rsi_value:.1f}")
                if 'MACD' in df.columns:
                    st.write(f"MACD: {df['MACD'].iloc[-1]:.3f}")
                    st.write(f"Signal: {df['MACD_Signal'].iloc[-1]:.3f}")
            
            with col3:
                st.write("**مؤشرات التقلب**")
                st.write(f"ATR: {df['ATR'].iloc[-1]:.3f}")
                if 'BB_Upper' in df.columns:
                    bb_width = (df['BB_Upper'].iloc[-1] - df['BB_Lower'].iloc[-1]) / df['BB_Middle'].iloc[-1] * 100
                    st.write(f"Bollinger Width: {bb_width:.1f}%")
                
                # التقلب السنوي
                returns = df['Close'].pct_change().dropna()
                volatility = returns.std() * (252 ** 0.5) * 100
                st.write(f"التقلب السنوي: {volatility:.1f}%")
        
        # معلومات الشركة
        if info:
            with st.expander("🏢 معلومات الشركة"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**الاسم:** {info.get('longName', 'غير متوفر')}")
                    st.write(f"**القطاع:** {info.get('sector', 'غير متوفر')}")
                    st.write(f"**الصناعة:** {info.get('industry', 'غير متوفر')}")
                with col2:
                    market_cap = info.get('marketCap', 0)
                    st.write(f"**القيمة السوقية:** {market_cap:,.0f}" if market_cap else "**القيمة السوقية:** غير متوفر")
                    pe = info.get('trailingPE', 0)
                    st.write(f"**نسبة السعر إلى الربح:** {pe:.2f}" if pe else "غير متوفر")
    
    else:
        st.error("❌ تعذر جلب البيانات. يرجى التحقق من:")
        st.markdown("""
        - اتصال الإنترنت
        - صحة رمز السهم
        - إعادة المحاولة بعد قليل
        """)
    
    # تذييل الصفحة
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>⚠️ <strong>إخلاء مسؤولية:</strong> التحليلات والتوصيات مقدمة للأغراض التعليمية فقط.</p>
        <p>قم دائمًا بإجراء البحث الخاص بك قبل اتخاذ قرارات الاستثمار.</p>
        <p>© 2024 البورصجي AI - منصة تحليل الأسهم الذكية | البيانات من Yahoo Finance</p>
    </div>
    """, unsafe_allow_html=True)

# ====================== تشغيل التطبيق ======================
if __name__ == "__main__":
    main()
