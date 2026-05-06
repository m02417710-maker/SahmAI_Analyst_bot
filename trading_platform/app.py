"""
ملف: app.py
المسار: /trading_platform/app.py
الوظيفة: التطبيق الرئيسي لمنصة تحليل الأسهم - البورصجي AI
النسخة: 4.0.0
آخر تحديث: 2024
"""

# ====================== استيرادات المكتبات الأساسية ======================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas_ta as ta
from datetime import datetime, timedelta
import warnings
import json
import os
import sys
from typing import Dict, List, Optional, Tuple
import asyncio
import aiohttp
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import time

# تجاهل التحذيرات المزعجة
warnings.filterwarnings('ignore')

# ====================== إعدادات الصفحة ======================
st.set_page_config(
    page_title="البورصجي AI - منصة تحليل الأسهم الذكية",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== إعدادات السمة ======================
st.markdown("""
<style>
    /* التنسيق العام */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
    }
    
    /* بطاقات المؤشرات */
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(0, 255, 136, 0.1);
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: #00ff88;
    }
    
    /* إشارات التداول */
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
    .neutral-signal {
        background: linear-gradient(135deg, #ffaa0020 0%, #ffaa0005 100%);
        border-left: 4px solid #ffaa00;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* الأزرار */
    .stButton > button {
        background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
        color: #0a0a0a;
        font-weight: bold;
        border: none;
        border-radius: 10px;
        padding: 10px 25px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 20px rgba(0,255,136,0.3);
    }
    
    /* شريط جانبي */
    .css-1d391kg {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
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
    
    /* عناوين */
    h1, h2, h3 {
        background: linear-gradient(135deg, #00ff88 0%, #00ccff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* مؤشر التحميل */
    .stSpinner > div {
        border-top-color: #00ff88 !important;
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
        st.warning("⚠️ لم يتم إعداد مفتاح Gemini API. سيتم استخدام التحليل الأساسي فقط.")
except Exception as e:
    GEMINI_AVAILABLE = False
    st.warning(f"⚠️ خطأ في تهيئة Gemini: {e}")

# ====================== قائمة الأسهم المدعومة ======================
STOCKS = {
    # البورصة المصرية (EGX)
    "🇪🇬 COMI.CA": {"name": "البنك التجاري الدولي (CIB)", "market": "EGX", "sector": "بنوك"},
    "🇪🇬 TMGH.CA": {"name": "طلعت مصطفى القابضة", "market": "EGX", "sector": "عقارات"},
    "🇪🇬 SWDY.CA": {"name": "السويدي إليكتريك", "market": "EGX", "sector": "صناعة"},
    "🇪🇬 EAST.CA": {"name": "الشرقية للدخان", "market": "EGX", "sector": "سلع استهلاكية"},
    "🇪🇬 MFPC.CA": {"name": "مصر لإنتاج الأسمدة (موبكو)", "market": "EGX", "sector": "كيماويات"},
    "🇪🇬 ORAS.CA": {"name": "أوراسكوم للإنشاءات", "market": "EGX", "sector": "إنشاءات"},
    "🇪🇬 JUFO.CA": {"name": "جي بي أوتو", "market": "EGX", "sector": "سيارات"},
    "🇪🇬 ABUK.CA": {"name": "أبو قير للأسمدة", "market": "EGX", "sector": "كيماويات"},
    "🇪🇬 HRHO.CA": {"name": "البنك الهولندي", "market": "EGX", "sector": "بنوك"},
    
    # بورصة تداول السعودية (Tadawul)
    "🇸🇦 2222.SR": {"name": "أرامكو السعودية", "market": "TADAWUL", "sector": "طاقة"},
    "🇸🇦 1120.SR": {"name": "مصرف الراجحي", "market": "TADAWUL", "sector": "بنوك"},
    "🇸🇦 7010.SR": {"name": "مجموعة STC", "market": "TADAWUL", "sector": "اتصالات"},
    "🇸🇦 2010.SR": {"name": "سابك", "market": "TADAWUL", "sector": "بتروكيماويات"},
    "🇸🇦 1211.SR": {"name": "معادن", "market": "TADAWUL", "sector": "تعدين"},
    
    # الأسهم الأمريكية (NASDAQ/NYSE)
    "🇺🇸 AAPL": {"name": "Apple Inc.", "market": "NASDAQ", "sector": "تكنولوجيا"},
    "🇺🇸 MSFT": {"name": "Microsoft Corp.", "market": "NASDAQ", "sector": "تكنولوجيا"},
    "🇺🇸 GOOGL": {"name": "Alphabet Inc.", "market": "NASDAQ", "sector": "تكنولوجيا"},
    "🇺🇸 AMZN": {"name": "Amazon.com", "market": "NASDAQ", "sector": "تجارة إلكترونية"},
    "🇺🇸 TSLA": {"name": "Tesla Inc.", "market": "NASDAQ", "sector": "سيارات كهربائية"},
    "🇺🇸 NVDA": {"name": "NVIDIA Corp.", "market": "NASDAQ", "sector": "تكنولوجيا"},
    "🇺🇸 META": {"name": "Meta Platforms", "market": "NASDAQ", "sector": "تكنولوجيا"},
    "🇺🇸 NFLX": {"name": "Netflix Inc.", "market": "NASDAQ", "sector": "ترفيه"},
    "🇺🇸 JPM": {"name": "JPMorgan Chase", "market": "NYSE", "sector": "بنوك"},
    "🇺🇸 JNJ": {"name": "Johnson & Johnson", "market": "NYSE", "sector": "صحة"},
}

# ====================== دوال جلب البيانات المحسنة ======================
@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(symbol: str, period: str = "1y") -> Tuple[pd.DataFrame, Dict]:
    """
    جلب بيانات السهم مع المؤشرات الفنية
    محسن بذاكرة تخزين مؤقت ودقة عالية
    """
    try:
        # جلب البيانات من Yahoo Finance
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        
        if df.empty:
            return None, None
        
        # حساب المؤشرات الفنية المتقدمة
        # المتوسطات المتحركة
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['EMA_9'] = ta.ema(df['Close'], length=9)
        df['EMA_21'] = ta.ema(df['Close'], length=21)
        
        # مؤشر RSI
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # MACD
        macd = ta.macd(df['Close'])
        if macd is not None:
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_Signal'] = macd['MACDs_12_26_9']
            df['MACD_Histogram'] = macd['MACDh_12_26_9']
        
        # Bollinger Bands
        bb = ta.bbands(df['Close'], length=20, std=2)
        if bb is not None:
            df['BB_Upper'] = bb['BBU_20_2.0']
            df['BB_Middle'] = bb['BBM_20_2.0']
            df['BB_Lower'] = bb['BBL_20_2.0']
        
        # مؤشرات إضافية
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        df['Volume_SMA'] = ta.sma(df['Volume'], length=20)
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        # Stochastic Oscillator
        stoch = ta.stoch(df['High'], df['Low'], df['Close'])
        if stoch is not None:
            df['Stoch_K'] = stoch['STOCHk_14_3_3']
            df['Stoch_D'] = stoch['STOCHd_14_3_3']
        
        return df, stock.info
        
    except Exception as e:
        st.error(f"⚠️ خطأ في جلب بيانات {symbol}: {str(e)}")
        return None, None

# ====================== دوال التحليل والتوصيات ======================
def analyze_trend(df: pd.DataFrame) -> Dict:
    """تحليل الاتجاه العام للسهم"""
    if df is None or df.empty:
        return {"trend": "غير معروف", "strength": 0, "description": "بيانات غير كافية"}
    
    close = df['Close']
    sma_20 = df['SMA_20'].iloc[-1] if not pd.isna(df['SMA_20'].iloc[-1]) else close.iloc[-1]
    sma_50 = df['SMA_50'].iloc[-1] if not pd.isna(df['SMA_50'].iloc[-1]) else close.iloc[-1]
    
    # تحديد الاتجاه
    if close.iloc[-1] > sma_20 > sma_50:
        trend = "صاعد قوي"
        strength = 80
        description = "السهم في اتجاه صاعد قوي مع دعم من المتوسطات المتحركة"
    elif close.iloc[-1] > sma_20:
        trend = "صاعد"
        strength = 60
        description = "السهم في اتجاه صاعد، لكن قد يواجه مقاومة"
    elif close.iloc[-1] < sma_20 < sma_50:
        trend = "هابط قوي"
        strength = 80
        description = "السهم في اتجاه هابط قوي، توخ الحذر"
    elif close.iloc[-1] < sma_20:
        trend = "هابط"
        strength = 60
        description = "السهم في اتجاه هابط"
    else:
        trend = "جانبي"
        strength = 40
        description = "السهم في نطاق جانبي، انتظر تأكيد الاتجاه"
    
    return {"trend": trend, "strength": strength, "description": description}

def analyze_support_resistance(df: pd.DataFrame) -> Dict:
    """تحديد مستويات الدعم والمقاومة"""
    if df is None or df.empty or len(df) < 50:
        return {"support": [], "resistance": [], "current": 0}
    
    close = df['Close'].iloc[-1]
    highs = df['High'].tail(50)
    lows = df['Low'].tail(50)
    
    # مستويات المقاومة (قمم محلية)
    resistance = []
    for i in range(5, len(highs) - 5):
        if highs.iloc[i] == highs.iloc[i-5:i+5].max():
            resistance.append(round(highs.iloc[i], 2))
    
    # مستويات الدعم (قيعان محلية)
    support = []
    for i in range(5, len(lows) - 5):
        if lows.iloc[i] == lows.iloc[i-5:i+5].min():
            support.append(round(lows.iloc[i], 2))
    
    # ترتيب وتنقية المستويات
    resistance = sorted(set(resistance), reverse=True)[:3]
    support = sorted(set(support))[:3]
    
    # أقرب دعم ومقاومة
    nearest_resistance = min([r for r in resistance if r > close], default=close * 1.05)
    nearest_support = max([s for s in support if s < close], default=close * 0.95)
    
    return {
        "support": support,
        "resistance": resistance,
        "current": round(close, 2),
        "nearest_support": round(nearest_support, 2),
        "nearest_resistance": round(nearest_resistance, 2)
    }

def generate_trading_signal(df: pd.DataFrame) -> Dict:
    """توليد إشارة تداول متكاملة"""
    if df is None or df.empty:
        return {"action": "انتظار", "confidence": 0, "reasons": [], "color": "neutral"}
    
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
    
    # إشارات المتوسطات المتحركة
    if sma_20 > sma_50:
        buy_score += 20
        reasons.append("✅ المتوسط 20 فوق المتوسط 50 - اتجاه صاعد")
    else:
        sell_score += 15
        reasons.append("❌ المتوسط 20 تحت المتوسط 50 - اتجاه هابط")
    
    # إشارات حجم التداول
    if volume_ratio > 1.5:
        buy_score += 15
        reasons.append(f"✅ حجم تداول مرتفع ({volume_ratio:.1f}x المتوسط)")
    elif volume_ratio < 0.5:
        sell_score += 10
        reasons.append(f"❌ حجم تداول ضعيف ({volume_ratio:.1f}x المتوسط)")
    
    # تحديد الإشارة النهائية
    net_score = buy_score - sell_score
    
    if net_score >= 40:
        action = "شراء قوي"
        color = "buy"
        confidence = min(95, net_score)
    elif net_score >= 20:
        action = "شراء"
        color = "buy"
        confidence = min(85, net_score + 40)
    elif net_score <= -40:
        action = "بيع قوي"
        color = "sell"
        confidence = min(95, abs(net_score))
    elif net_score <= -20:
        action = "بيع"
        color = "sell"
        confidence = min(85, abs(net_score) + 40)
    else:
        action = "انتظار"
        color = "neutral"
        confidence = 50
    
    return {
        "action": action,
        "confidence": confidence,
        "reasons": reasons[:5],
        "color": color,
        "buy_score": buy_score,
        "sell_score": sell_score
    }

# ====================== دالة تحليل Gemini ======================
def get_gemini_analysis(symbol: str, stock_data: Dict, indicators: Dict, signal: Dict) -> Optional[str]:
    """الحصول على تحليل متقدم من Gemini AI"""
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        أنت محلل أسهم محترف في البورصجية AI. قم بتحليل السهم التالي:
        
        {stock_data.get('name', symbol)} ({symbol})
        
        البيانات الفنية:
        - السعر الحالي: {stock_data.get('price', 'N/A')}
        - التغير اليومي: {stock_data.get('change', 'N/A')} ({stock_data.get('change_percent', 'N/A')}%)
        - RSI: {indicators.get('rsi', 'N/A')}
        - الاتجاه: {indicators.get('trend', 'N/A')}
        
        الإشارة الفنية: {signal.get('action', 'N/A')} (ثقة: {signal.get('confidence', 'N/A')}%)
        
        المطلوب:
        1. تحليل فني مختصر
        2. نقاط الدعم والمقاومة الرئيسية
        3. توصية واضحة للمستثمر
        4. نسبة المخاطرة المتوقعة
        
        الرد باللغة العربية بشكل احترافي ومختصر (لا يزيد عن 300 كلمة).
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        st.error(f"⚠️ خطأ في تحليل Gemini: {e}")
        return None

# ====================== دالة الرسم البياني المتقدم ======================
def create_advanced_chart(df: pd.DataFrame, symbol: str, name: str) -> go.Figure:
    """إنشاء رسم بياني متقدم مع جميع المؤشرات"""
    
    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.4, 0.15, 0.15, 0.15, 0.15],
        subplot_titles=("السعر مع المتوسطات و Bollinger", "RSI", "MACD", "Stochastic", "حجم التداول")
    )
    
    # 1. السعر مع المتوسطات و Bollinger Bands
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name="السعر"
    ), row=1, col=1)
    
    # المتوسطات المتحركة
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name="SMA 20", 
                            line=dict(color='orange', width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name="SMA 50", 
                            line=dict(color='cyan', width=1.5)), row=1, col=1)
    
    # Bollinger Bands
    if 'BB_Upper' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name="BB Upper",
                                line=dict(color='gray', dash='dash'), opacity=0.5), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name="BB Lower",
                                line=dict(color='gray', dash='dash'), opacity=0.5,
                                fill='tonexty', fillcolor='rgba(128,128,128,0.1)'), row=1, col=1)
    
    # 2. RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI",
                            line=dict(color='magenta', width=2)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, row=2, col=1)
    fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, row=2, col=1)
    
    # 3. MACD
    if 'MACD' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name="MACD",
                                line=dict(color='blue', width=1.5)), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name="Signal",
                                line=dict(color='red', width=1.5)), row=3, col=1)
        
        # أعمدة MACD Histogram
        colors = ['green' if val >= 0 else 'red' for val in df['MACD_Histogram']]
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Histogram'], name="Histogram",
                            marker_color=colors, opacity=0.5), row=3, col=1)
    
    # 4. Stochastic
    if 'Stoch_K' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['Stoch_K'], name="Stoch %K",
                                line=dict(color='blue', width=1.5)), row=4, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Stoch_D'], name="Stoch %D",
                                line=dict(color='orange', width=1.5)), row=4, col=1)
        fig.add_hline(y=80, line_dash="dash", line_color="red", row=4, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="green", row=4, col=1)
    
    # 5. حجم التداول
    colors = ['red' if close < open else 'green' 
              for close, open in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume",
                        marker_color=colors, opacity=0.6), row=5, col=1)
    
    # خط متوسط الحجم
    if 'Volume_SMA' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['Volume_SMA'], name="Avg Volume",
                                line=dict(color='yellow', width=1.5, dash='dot')), row=5, col=1)
    
    # تنسيق الرسم البياني
    fig.update_layout(
        height=900,
        template="plotly_dark",
        title_text=f"📊 {name} ({symbol}) - تحليل فني متقدم",
        title_font_size=20,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )
    
    fig.update_xaxes(rangeslider_visible=False)
    fig.update_yaxes(title_text="السعر", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    fig.update_yaxes(title_text="Stochastic", row=4, col=1, range=[0, 100])
    fig.update_yaxes(title_text="Volume", row=5, col=1)
    
    return fig

# ====================== الواجهة الرئيسية ======================
def main():
    """التطبيق الرئيسي"""
    
    # العنوان الرئيسي
    st.title("📈 البورصجي AI - منصة تحليل الأسهم الذكية")
    st.markdown("**تحليل فني متقدم + ذكاء اصطناعي + توصيات فورية**")
    st.markdown("---")
    
    # الشريط الجانبي
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/thumb/2/2a/Egyptian_Exchange_logo.png/200px-Egyptian_Exchange_logo.png", 
                 use_column_width=True)
        
        st.markdown("## ⚙️ الإعدادات")
        
        # اختيار السهم
        selected_display = st.selectbox(
            "🔍 اختر السهم",
            options=list(STOCKS.keys()),
            format_func=lambda x: f"{x} - {STOCKS[x]['name']}"
        )
        
        selected_symbol = selected_display.split(" - ")[0].split(" ")[1]
        stock_info = STOCKS[selected_display.split(" - ")[0].split(" ")[1]]
        
        # فترة التحليل
        period = st.selectbox(
            "📅 الفترة الزمنية",
            ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=3,
            help="اختر الفترة الزمنية للتحليل"
        )
        
        st.markdown("---")
        
        # معلومات السوق
        st.markdown("## 📊 معلومات السوق")
        st.markdown(f"**🇪🇬 البورصة المصرية:** 10:00 - 14:30")
        st.markdown(f"**🇸🇦 تداول السعودية:** 10:00 - 15:00")
        st.markdown(f"**🇺🇸 الأسهم الأمريكية:** 16:30 - 23:00")
        
        st.markdown("---")
        
        # حالة الذكاء الاصطناعي
        if GEMINI_AVAILABLE:
            st.success("🤖 Gemini AI: متصل")
        else:
            st.warning("⚠️ Gemini AI: غير متصل")
        
        st.markdown("---")
        st.caption("⚠️ البيانات من Yahoo Finance")
        st.caption("📈 للأغراض التعليمية فقط")
    
    # ====================== جلب البيانات ======================
    with st.spinner("📡 جاري تحميل بيانات السهم..."):
        df, info = get_stock_data(selected_symbol, period)
    
    if df is not None and not df.empty:
        # ====================== البيانات الأساسية ======================
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        change = current_price - prev_price
        change_percent = (change / prev_price) * 100 if prev_price else 0
        
        # ====================== التحليل الفني ======================
        trend_analysis = analyze_trend(df)
        sr_levels = analyze_support_resistance(df)
        trading_signal = generate_trading_signal(df)
        
        # ====================== عرض المقاييس ======================
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "💰 السعر الحالي", 
                f"{current_price:.2f}",
                f"{change:+.2f} ({change_percent:+.2f}%)"
            )
        
        with col2:
            rsi_val = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
            st.metric("📊 RSI (14)", f"{rsi_val:.1f}")
        
        with col3:
            st.metric("📈 المتوسط 20", f"{df['SMA_20'].iloc[-1]:.2f}")
        
        with col4:
            st.metric("📉 المتوسط 50", f"{df['SMA_50'].iloc[-1]:.2f}")
        
        with col5:
            volume_ratio = df['Volume_Ratio'].iloc[-1] if not pd.isna(df['Volume_Ratio'].iloc[-1]) else 1
            st.metric("💹 حجم التداول", f"{volume_ratio:.2f}x")
        
        st.markdown("---")
        
        # ====================== إشارة التداول ======================
        st.subheader("🎯 إشارة التداول")
        
        if trading_signal["color"] == "buy":
            st.markdown(f"""
            <div class="buy-signal">
                <h3>🟢 {trading_signal['action']}</h3>
                <p><strong>قوة الإشارة:</strong> {trading_signal['confidence']}%</p>
                <p><strong>الأسباب:</strong></p>
                <ul>
                    {''.join([f'<li>{reason}</li>' for reason in trading_signal['reasons']])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif trading_signal["color"] == "sell":
            st.markdown(f"""
            <div class="sell-signal">
                <h3>🔴 {trading_signal['action']}</h3>
                <p><strong>قوة الإشارة:</strong> {trading_signal['confidence']}%</p>
                <p><strong>الأسباب:</strong></p>
                <ul>
                    {''.join([f'<li>{reason}</li>' for reason in trading_signal['reasons']])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="neutral-signal">
                <h3>🟡 {trading_signal['action']}</h3>
                <p><strong>الأسباب:</strong></p>
                <ul>
                    {''.join([f'<li>{reason}</li>' for reason in trading_signal['reasons']])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # ====================== تحليل الاتجاه والدعم والمقاومة ======================
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 تحليل الاتجاه")
            st.info(f"**{trend_analysis['trend']}**")
            st.progress(trend_analysis['strength'] / 100)
            st.caption(trend_analysis['description'])
        
        with col2:
            st.subheader("📊 الدعم والمقاومة")
            st.write(f"**المقاومات:** {', '.join(map(str, sr_levels['resistance']))}")
            st.write(f"**الدعوم:** {', '.join(map(str, sr_levels['support']))}")
            st.write(f"**أقرب مقاومة:** {sr_levels['nearest_resistance']}")
            st.write(f"**أقرب دعم:** {sr_levels['nearest_support']}")
        
        st.markdown("---")
        
        # ====================== الرسم البياني المتقدم ======================
        st.subheader("📊 الرسم البياني المتقدم")
        fig = create_advanced_chart(df, selected_symbol, stock_info['name'])
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # ====================== التحليل بالذكاء الاصطناعي ======================
        st.subheader("🤖 التحليل بالذكاء الاصطناعي")
        
        if st.button("🚀 تحليل ذكي باستخدام Gemini AI", type="primary", use_container_width=True):
            if GEMINI_AVAILABLE:
                with st.spinner("🧠 جاري التحليل الذكي..."):
                    stock_data = {
                        "name": stock_info['name'],
                        "price": current_price,
                        "change": change,
                        "change_percent": change_percent
                    }
                    indicators = {
                        "rsi": rsi_val,
                        "trend": trend_analysis['trend']
                    }
                    signal = {
                        "action": trading_signal['action'],
                        "confidence": trading_signal['confidence']
                    }
                    
                    analysis = get_gemini_analysis(selected_symbol, stock_data, indicators, signal)
                    if analysis:
                        st.success("✅ تحليل الذكاء الاصطناعي:")
                        st.markdown(analysis)
                    else:
                        st.warning("⚠️ تعذر الحصول على تحليل من Gemini")
            else:
                st.error("❌ Gemini AI غير متوفر. يرجى إضافة مفتاح API في الإعدادات.")
        
        # ====================== مؤشرات إضافية ======================
        with st.expander("📋 المؤشرات الفنية التفصيلية"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**المتوسطات المتحركة**")
                st.write(f"SMA 5: {ta.sma(df['Close'], length=5).iloc[-1]:.2f}")
                st.write(f"SMA 10: {ta.sma(df['Close'], length=10).iloc[-1]:.2f}")
                st.write(f"SMA 20: {df['SMA_20'].iloc[-1]:.2f}")
                st.write(f"SMA 50: {df['SMA_50'].iloc[-1]:.2f}")
                st.write(f"EMA 9: {df['EMA_9'].iloc[-1]:.2f}")
                st.write(f"EMA 21: {df['EMA_21'].iloc[-1]:.2f}")
            
            with col2:
                st.write("**مؤشرات الزخم**")
                st.write(f"RSI: {rsi_val:.1f}")
                if 'Stoch_K' in df.columns:
                    st.write(f"Stochastic %K: {df['Stoch_K'].iloc[-1]:.1f}")
                    st.write(f"Stochastic %D: {df['Stoch_D'].iloc[-1]:.1f}")
                if 'MACD' in df.columns:
                    st.write(f"MACD: {df['MACD'].iloc[-1]:.3f}")
                    st.write(f"Signal: {df['MACD_Signal'].iloc[-1]:.3f}")
            
            with col3:
                st.write("**مؤشرات التقلب والحجم**")
                st.write(f"ATR: {df['ATR'].iloc[-1]:.3f}")
                st.write(f"Bollinger Width: {((df['BB_Upper'].iloc[-1] - df['BB_Lower'].iloc[-1]) / df['BB_Middle'].iloc[-1] * 100):.1f}%")
                st.write(f"Volume Ratio: {volume_ratio:.2f}x")
                
                # حساب التقلب السنوي
                returns = df['Close'].pct_change().dropna()
                volatility = returns.std() * (252 ** 0.5) * 100
                st.write(f"التقلب السنوي: {volatility:.1f}%")
        
        # ====================== معلومات الشركة ======================
        with st.expander("🏢 معلومات الشركة"):
            if info:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**الاسم:** {info.get('longName', 'غير متوفر')}")
                    st.write(f"**القطاع:** {info.get('sector', 'غير متوفر')}")
                    st.write(f"**الصناعة:** {info.get('industry', 'غير متوفر')}")
                with col2:
                    st.write(f"**القيمة السوقية:** {info.get('marketCap', 'غير متوفر'):,}")
                    st.write(f"**نسبة السعر إلى الربح:** {info.get('trailingPE', 'غير متوفر')}")
                    st.write(f"**عائد التوزيعات:** {info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else "غير متوفر")
            else:
                st.warning("معلومات الشركة غير متاحة حالياً")
    
    else:
        st.error("❌ تعذر جلب البيانات. يرجى التحقق من اتصال الإنترنت وصحة رمز السهم.")
        st.info("💡 **نصائح:**\n- تأكد من صحة رمز السهم\n- حاول تحديث الصفحة\n- تحقق من اتصال الشبكة")
    
    # ====================== تذييل الصفحة ======================
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>⚠️ <strong>إخلاء مسؤولية:</strong> التحليلات والتوصيات مقدمة للأغراض التعليمية فقط. </p>
        <p>قم دائمًا بإجراء البحث الخاص بك قبل اتخاذ قرارات الاستثمار.</p>
        <p>© 2024 البورصجي AI - منصة تحليل الأسهم الذكية | البيانات من Yahoo Finance</p>
        <p>🤖 مدعوم بـ Google Gemini AI</p>
    </div>
    """, unsafe_allow_html=True)

# ====================== تشغيل التطبيق ======================
if __name__ == "__main__":
    main()
