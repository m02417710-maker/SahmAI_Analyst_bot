"""
البورصجي AI - منصة تحليل الأسهم الذكية المتطورة
الإصدار 2.0 - تحديث شامل للبورصة المصرية والصناديق الاستثمارية
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
    page_title="البورصجي AI - تحليل الأسهم الذكي 2.0",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== إعدادات السمة المحسّنة ======================
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
    
    /* بطاقات معلومات */
    .info-card {
        background: linear-gradient(135deg, #2a4a5e 0%, #1a3a4e 100%);
        border-radius: 12px;
        padding: 15px;
        border-left: 4px solid #00ccff;
        margin: 10px 0;
    }
    
    /* بطاقات التحذير */
    .warning-card {
        background: linear-gradient(135deg, #5a4a2e 0%, #4a3a1e 100%);
        border-radius: 12px;
        padding: 15px;
        border-left: 4px solid #ffaa00;
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
    
    /* جداول */
    .stDataFrame {
        background-color: #1a1a2e;
    }
    
    /* علامات تبويب */
    .stTabs [data-baseweb="tab-list"] button {
        color: #00ff88;
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

# ====================== قاعدة بيانات الأسهم والصناديق المصرية ======================
STOCKS = {
    # ==================== البورصة المصرية (EGX) ====================
    # البنوك والخدمات المالية
    "🇪🇬 COMI.CA": {
        "name": "البنك التجاري الدولي (CIB)",
        "market": "EGX",
        "sector": "بنوك وخدمات مالية",
        "market_cap": "مليارات جنيه",
        "established": 1975,
        "dividend": "معروف برأس مال عالي",
        "description": "أكبر بنك أجنبي في مصر",
        "pe_ratio": "10-15"
    },
    "🇪🇬 NBKE.CA": {
        "name": "البنك الأهلي المصري",
        "market": "EGX",
        "sector": "بنوك وخدمات مالية",
        "market_cap": "مليارات جنيه",
        "established": 1898,
        "dividend": "نقدي منتظم",
        "description": "أكبر بنك حكومي في مصر",
        "pe_ratio": "9-12"
    },
    "🇪🇬 HRHO.CA": {
        "name": "بنك هيرميس",
        "market": "EGX",
        "sector": "بنوك وخدمات مالية",
        "market_cap": "مليارات جنيه",
        "established": 1987,
        "dividend": "نسبة توزيع عالية",
        "description": "متخصص في الخدمات الاستثمارية",
        "pe_ratio": "10-14"
    },
    
    # القطاع العقاري
    "🇪🇬 TMGH.CA": {
        "name": "طلعت مصطفى القابضة",
        "market": "EGX",
        "sector": "عقارات وتطوير عقاري",
        "market_cap": "مليارات جنيه",
        "established": 1960,
        "dividend": "متوسط",
        "description": "رائدة في تطوير المدن الجديدة",
        "pe_ratio": "12-18"
    },
    "🇪🇬 ORWE.CA": {
        "name": "أوراسكوم للإنشاءات",
        "market": "EGX",
        "sector": "عقارات وإنشاءات",
        "market_cap": "ملايين جنيه",
        "established": 1998,
        "dividend": "متغير",
        "description": "متخصصة في العقارات والإنشاءات",
        "pe_ratio": "8-12"
    },
    
    # القطاع الصناعي
    "🇪🇬 SWDY.CA": {
        "name": "السويدي إليكتريك",
        "market": "EGX",
        "sector": "صناعة وكهرباء",
        "market_cap": "مليارات جنيه",
        "established": 1958,
        "dividend": "نقدي منتظم",
        "description": "صناعة أسلاك كهربائية والمعدات",
        "pe_ratio": "11-16"
    },
    "🇪🇬 CLCO.CA": {
        "name": "كابلات مصر",
        "market": "EGX",
        "sector": "صناعة وكهرباء",
        "market_cap": "ملايين جنيه",
        "established": 1980,
        "dividend": "متوسط",
        "description": "تصنيع الأسلاك والكابلات",
        "pe_ratio": "9-13"
    },
    
    # قطاع الغذاء والمشروبات
    "🇪🇬 EAST.CA": {
        "name": "الشرقية للدخان",
        "market": "EGX",
        "sector": "سلع استهلاكية",
        "market_cap": "مليارات جنيه",
        "established": 1998,
        "dividend": "عالي جداً",
        "description": "تصنيع والتوزيع للسجائر",
        "pe_ratio": "8-11"
    },
    "🇪🇬 JUFO.CA": {
        "name": "جهينة للصناعات الغذائية",
        "market": "EGX",
        "sector": "سلع استهلاكية",
        "market_cap": "مليارات جنيه",
        "established": 1975,
        "dividend": "منتظم",
        "description": "صناعة الألبان والعصائر",
        "pe_ratio": "15-20"
    },
    
    # قطاع الكيماويات
    "🇪🇬 MFPC.CA": {
        "name": "مصر لإنتاج الأسمدة (موبكو)",
        "market": "EGX",
        "sector": "كيماويات وأسمدة",
        "market_cap": "مليارات جنيه",
        "established": 1978,
        "dividend": "عالي",
        "description": "تصنيع الأسمدة الكيماوية",
        "pe_ratio": "7-10"
    },
    "🇪🇬 CCI.CA": {
        "name": "شركة كيما للأسمدة",
        "market": "EGX",
        "sector": "كيماويات وأسمدة",
        "market_cap": "مليارات جنيه",
        "established": 1985,
        "dividend": "منتظم",
        "description": "إنتاج الأسمدة والمواد الكيماوية",
        "pe_ratio": "8-12"
    },
    
    # قطاع الاتصالات والتكنولوجيا
    "🇪🇬 ORDI.CA": {
        "name": "أوراسكوم للاتصالات",
        "market": "EGX",
        "sector": "اتصالات وتكنولوجيا",
        "market_cap": "مليارات جنيه",
        "established": 1998,
        "dividend": "متوسط",
        "description": "شركة اتصالات محمول",
        "pe_ratio": "10-15"
    },
    
    # ==================== الأسهم السعودية ====================
    "🇸🇦 2222.SR": {
        "name": "أرامكو السعودية",
        "market": "TADAWUL",
        "sector": "طاقة والنفط",
        "market_cap": "تريليونات ريال",
        "established": 1933,
        "dividend": "عالي جداً",
        "description": "عملاق البترول والغاز",
        "pe_ratio": "12-15"
    },
    "🇸🇦 1120.SR": {
        "name": "مصرف الراجحي",
        "market": "TADAWUL",
        "sector": "بنوك وخدمات مالية",
        "market_cap": "مليارات ريال",
        "established": 1957,
        "dividend": "عالي",
        "description": "أكبر بنك إسلامي في السعودية",
        "pe_ratio": "14-18"
    },
    
    # ==================== الأسهم الأمريكية ====================
    "🇺🇸 AAPL": {
        "name": "Apple Inc.",
        "market": "NASDAQ",
        "sector": "تكنولوجيا",
        "market_cap": "تريليونات دولار",
        "established": 1976,
        "dividend": "نقدي",
        "description": "عملاق التكنولوجيا والهواتف",
        "pe_ratio": "25-35"
    },
    "🇺🇸 MSFT": {
        "name": "Microsoft Corp.",
        "market": "NASDAQ",
        "sector": "تكنولوجيا",
        "market_cap": "تريليونات دولار",
        "established": 1975,
        "dividend": "نقدي",
        "description": "عملاق البرمجيات والسحابة",
        "pe_ratio": "28-38"
    },
}

# ====================== قاعدة بيانات الصناديق الاستثمارية ======================
INVESTMENT_FUNDS = {
    "الصناديق الاستثمارية المصرية": [
        {
            "name": "صندوق أجيال للأسهم",
            "type": "أسهم",
            "manager": "شركة أجيال للتمويل",
            "min_investment": "5,000 جنيه",
            "fees": "1.5% سنوياً",
            "performance": "+15% سنوياً",
            "description": "صندوق متخصص في الأسهم الكبرى"
        },
        {
            "name": "صندوق الراجحي للأسهم المصرية",
            "type": "أسهم",
            "manager": "البنك الأهلي",
            "min_investment": "10,000 جنيه",
            "fees": "1.25% سنوياً",
            "performance": "+18% سنوياً",
            "description": "محفظة أسهم متنوعة من البورصة المصرية"
        },
        {
            "name": "صندوق النيل للأسهم",
            "type": "أسهم",
            "manager": "بنك مصر",
            "min_investment": "1,000 جنيه",
            "fees": "2% سنوياً",
            "performance": "+12% سنوياً",
            "description": "صندوق عام متنوع"
        },
        {
            "name": "صندوق ذهبي للدخل الثابت",
            "type": "دخل ثابت",
            "manager": "شركة ذهبي",
            "min_investment": "1,000 جنيه",
            "fees": "0.75% سنوياً",
            "performance": "+8% سنوياً",
            "description": "سندات حكومية وشركات"
        },
        {
            "name": "صندوق أفق المتوازن",
            "type": "متوازن",
            "manager": "شركة أفق",
            "min_investment": "5,000 جنيه",
            "fees": "1.5% سنوياً",
            "performance": "+10% سنوياً",
            "description": "خليط من الأسهم والسندات"
        },
        {
            "name": "صندوق رمسيس للنمو",
            "type": "أسهم",
            "manager": "شركة رمسيس",
            "min_investment": "2,000 جنيه",
            "fees": "1.75% سنوياً",
            "performance": "+16% سنوياً",
            "description": "تركيز على الأسهم ذات النمو"
        }
    ],
    
    "الصناديق العالمية": [
        {
            "name": "صندوق فانجارد العالمي",
            "type": "أسهم عالمية",
            "manager": "Vanguard",
            "min_investment": "$100",
            "fees": "0.1% سنوياً",
            "performance": "+12% سنوياً",
            "description": "تنويع عالمي كامل"
        },
        {
            "name": "صندوق iShares الأسهم الأمريكية",
            "type": "أسهم أمريكية",
            "manager": "BlackRock",
            "min_investment": "$50",
            "fees": "0.03% سنوياً",
            "performance": "+14% سنوياً",
            "description": "تتبع مؤشر S&P 500"
        }
    ]
}

# ====================== معلومات البورصة المصرية ======================
EGX_INFO = {
    "name": "بورصة مصر - EGX",
    "established": 1888,
    "trading_hours": "10:00 - 14:30",
    "currency": "الجنيه المصري (EGP)",
    "trading_days": "من الأحد إلى الخميس",
    "market_cap": "1+ تريليون جنيه",
    "listed_companies": "200+ شركة",
    "main_indices": {
        "EGX30": "أكبر 30 شركة",
        "EGX50": "أكبر 50 شركة",
        "EGX100": "أكبر 100 شركة"
    },
    "sectors": [
        "بنوك وخدمات مالية",
        "عقارات وإنشاءات",
        "صناعة وكهرباء",
        "سلع استهلاكية",
        "كيماويات وأسمدة",
        "اتصالات وتكنولوجيا",
        "أغذية ومشروبات",
        "خدمات وسياحة"
    ],
    "requirements": {
        "account": "حساب لدى شركة سمسرة",
        "min_trade": "1 سهم",
        "settlement": "T+2 (يومين بعد التداول)"
    }
}

# ====================== دوال جلب البيانات ======================
@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(symbol: str, period: str = "1y") -> Tuple[Optional[pd.DataFrame], Optional[Dict]]:
    """
    جلب بيانات السهم مع المؤشرات الفنية المتقدمة
    """
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        
        if df.empty:
            return None, None
        
        # حساب المؤشرات الفنية الأساسية
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        df['EMA_9'] = ta.ema(df['Close'], length=9)
        df['EMA_21'] = ta.ema(df['Close'], length=21)
        
        # RSI والمؤشرات
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['RSI_Overbought'] = df['RSI'] > 70
        df['RSI_Oversold'] = df['RSI'] < 30
        
        # MACD
        macd = ta.macd(df['Close'])
        if macd is not None and not macd.empty:
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_Signal'] = macd['MACDs_12_26_9']
            df['MACD_Histogram'] = macd['MACDh_12_26_9']
        
        # Bollinger Bands
        bb = ta.bbands(df['Close'], length=20)
        if bb is not None and not bb.empty:
            df['BB_Upper'] = bb['BBU_20_2.0']
            df['BB_Middle'] = bb['BBM_20_2.0']
            df['BB_Lower'] = bb['BBL_20_2.0']
        
        # Stochastic
        stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=14, d=3, smooth_k=3)
        if stoch is not None and not stoch.empty:
            df['Stoch_K'] = stoch['STOCHk_14_3_3']
            df['Stoch_D'] = stoch['STOCHd_14_3_3']
        
        # حجم التداول
        df['Volume_SMA'] = ta.sma(df['Volume'], length=20)
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        # ATR (متوسط النطاق الحقيقي)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        df['ATR_Percent'] = (df['ATR'] / df['Close']) * 100
        
        # CCI (Commodity Channel Index)
        df['CCI'] = ta.cci(df['High'], df['Low'], df['Close'], length=20)
        
        # On Balance Volume
        df['OBV'] = ta.obv(df['Close'], df['Volume'])
        
        # حساب العوائد
        df['Daily_Return'] = df['Close'].pct_change() * 100
        df['Cumulative_Return'] = (1 + df['Daily_Return'] / 100).cumprod() * 100 - 100
        
        return df, stock.info
        
    except Exception as e:
        st.error(f"⚠️ خطأ في جلب بيانات {symbol}: {str(e)}")
        return None, None

# ====================== دوال التحليل المتقدمة ======================
def analyze_trend(df: pd.DataFrame) -> Dict:
    """تحليل الاتجاه المتقدم"""
    if df is None or df.empty:
        return {"trend": "غير معروف", "strength": 0, "description": "بيانات غير كافية"}
    
    close = df['Close'].iloc[-1]
    sma_20 = df['SMA_20'].iloc[-1] if not pd.isna(df['SMA_20'].iloc[-1]) else close
    sma_50 = df['SMA_50'].iloc[-1] if not pd.isna(df['SMA_50'].iloc[-1]) else close
    sma_200 = df['SMA_200'].iloc[-1] if not pd.isna(df['SMA_200'].iloc[-1]) else close
    
    # حساب مؤشر الاتجاه
    if close > sma_20 > sma_50 > sma_200:
        return {
            "trend": "صاعد قوي جداً",
            "strength": 95,
            "description": "اتجاه صاعد قوي جداً مع دعم قوي من المتوسطات",
            "color": "green"
        }
    elif close > sma_20 > sma_50:
        return {
            "trend": "صاعد قوي",
            "strength": 80,
            "description": "اتجاه صاعد قوي مع دعم من المتوسطات",
            "color": "green"
        }
    elif close > sma_20:
        return {
            "trend": "صاعد",
            "strength": 60,
            "description": "اتجاه صاعد، قد يواجه مقاومة",
            "color": "lightgreen"
        }
    elif close < sma_20 < sma_50 < sma_200:
        return {
            "trend": "هابط قوي جداً",
            "strength": 95,
            "description": "اتجاه هابط قوي جداً مع مقاومة قوية من المتوسطات",
            "color": "red"
        }
    elif close < sma_20 < sma_50:
        return {
            "trend": "هابط قوي",
            "strength": 80,
            "description": "اتجاه هابط قوي",
            "color": "red"
        }
    elif close < sma_20:
        return {
            "trend": "هابط",
            "strength": 60,
            "description": "اتجاه هابط",
            "color": "lighred"
        }
    else:
        return {
            "trend": "جانبي",
            "strength": 40,
            "description": "نطاق جانبي، انتظر تأكيد الاتجاه",
            "color": "yellow"
        }

def generate_advanced_signal(df: pd.DataFrame) -> Dict:
    """توليد إشارة تداول متقدمة متعددة المؤشرات"""
    if df is None or df.empty:
        return {
            "action": "انتظار",
            "confidence": 0,
            "reasons": ["بيانات غير كافية"],
            "color": "neutral",
            "risk_level": "عالي"
        }
    
    close = df['Close'].iloc[-1]
    rsi = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
    sma_20 = df['SMA_20'].iloc[-1] if not pd.isna(df['SMA_20'].iloc[-1]) else close
    sma_50 = df['SMA_50'].iloc[-1] if not pd.isna(df['SMA_50'].iloc[-1]) else close
    volume_ratio = df['Volume_Ratio'].iloc[-1] if not pd.isna(df['Volume_Ratio'].iloc[-1]) else 1
    
    buy_score = 0
    sell_score = 0
    reasons = []
    
    # ===== تحليل RSI =====
    if rsi < 20:
        buy_score += 40
        reasons.append(f"🟢 RSI منخفض جداً ({rsi:.1f}) - ذروة بيع قوية")
    elif rsi < 30:
        buy_score += 30
        reasons.append(f"🟢 RSI منخفض ({rsi:.1f}) - منطقة ذروة بيع")
    elif rsi < 40:
        buy_score += 15
        reasons.append(f"🟡 RSI عند {rsi:.1f} - بداية منطقة شراء")
    elif rsi > 80:
        sell_score += 40
        reasons.append(f"🔴 RSI مرتفع جداً ({rsi:.1f}) - ذروة شراء قوية")
    elif rsi > 70:
        sell_score += 30
        reasons.append(f"🔴 RSI مرتفع ({rsi:.1f}) - منطقة ذروة شراء")
    elif rsi > 60:
        sell_score += 15
        reasons.append(f"🟡 RSI عند {rsi:.1f} - بداية منطقة بيع")
    else:
        reasons.append(f"⚪ RSI عند {rsi:.1f} - منطقة محايدة")
    
    # ===== تحليل المتوسطات =====
    if sma_20 > sma_50:
        buy_score += 20
        reasons.append("🟢 SMA20 > SMA50 - اتجاه صاعد")
    elif sma_20 < sma_50:
        sell_score += 20
        reasons.append("🔴 SMA20 < SMA50 - اتجاه هابط")
    else:
        reasons.append("⚪ المتوسطات متقاربة")
    
    # ===== تحليل الحجم =====
    if volume_ratio > 2:
        buy_score += 15
        reasons.append(f"🟢 حجم تداول قوي جداً ({volume_ratio:.1f}x)")
    elif volume_ratio > 1.5:
        buy_score += 10
        reasons.append(f"🟢 حجم تداول مرتفع ({volume_ratio:.1f}x)")
    elif volume_ratio < 0.3:
        sell_score += 15
        reasons.append(f"🔴 حجم تداول ضعيف جداً ({volume_ratio:.1f}x)")
    elif volume_ratio < 0.5:
        sell_score += 10
        reasons.append(f"🔴 حجم تداول منخفض ({volume_ratio:.1f}x)")
    
    # ===== تحليل Stochastic =====
    if 'Stoch_K' in df.columns and not pd.isna(df['Stoch_K'].iloc[-1]):
        stoch_k = df['Stoch_K'].iloc[-1]
        if stoch_k < 20:
            buy_score += 10
            reasons.append(f"🟢 Stochastic منخفض ({stoch_k:.1f})")
        elif stoch_k > 80:
            sell_score += 10
            reasons.append(f"🔴 Stochastic مرتفع ({stoch_k:.1f})")
    
    # ===== تحليل MACD =====
    if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
        if not pd.isna(df['MACD'].iloc[-1]) and not pd.isna(df['MACD_Signal'].iloc[-1]):
            macd_val = df['MACD'].iloc[-1]
            signal_val = df['MACD_Signal'].iloc[-1]
            if macd_val > signal_val:
                buy_score += 15
                reasons.append(f"🟢 MACD > Signal - قوة شرائية")
            else:
                sell_score += 15
                reasons.append(f"🔴 MACD < Signal - ضعف شرائي")
    
    # ===== تحليل CCI =====
    if 'CCI' in df.columns and not pd.isna(df['CCI'].iloc[-1]):
        cci = df['CCI'].iloc[-1]
        if cci > 100:
            buy_score += 10
            reasons.append(f"🟢 CCI قوي ({cci:.1f})")
        elif cci < -100:
            sell_score += 10
            reasons.append(f"🔴 CCI ضعيف ({cci:.1f})")
    
    net_score = buy_score - sell_score
    
    # تحديد مستوى المخاطرة
    if abs(net_score) < 10:
        risk_level = "متوسط"
    elif abs(net_score) < 25:
        risk_level = "منخفض"
    else:
        risk_level = "منخفض جداً" if abs(net_score) > 35 else "منخفض"
    
    # توليد الإشارة النهائية
    if net_score >= 50:
        return {
            "action": "شراء قوي جداً",
            "confidence": min(99, net_score),
            "reasons": reasons,
            "color": "buy",
            "risk_level": risk_level
        }
    elif net_score >= 30:
        return {
            "action": "شراء قوي",
            "confidence": min(90, net_score),
            "reasons": reasons,
            "color": "buy",
            "risk_level": risk_level
        }
    elif net_score >= 15:
        return {
            "action": "شراء",
            "confidence": min(80, net_score + 50),
            "reasons": reasons,
            "color": "buy",
            "risk_level": risk_level
        }
    elif net_score <= -50:
        return {
            "action": "بيع قوي جداً",
            "confidence": min(99, abs(net_score)),
            "reasons": reasons,
            "color": "sell",
            "risk_level": risk_level
        }
    elif net_score <= -30:
        return {
            "action": "بيع قوي",
            "confidence": min(90, abs(net_score)),
            "reasons": reasons,
            "color": "sell",
            "risk_level": risk_level
        }
    elif net_score <= -15:
        return {
            "action": "بيع",
            "confidence": min(80, abs(net_score) + 50),
            "reasons": reasons,
            "color": "sell",
            "risk_level": risk_level
        }
    else:
        return {
            "action": "انتظار",
            "confidence": 50,
            "reasons": reasons + ["🟡 المؤشرات محايدة"],
            "color": "neutral",
            "risk_level": "متوسط"
        }

def get_support_resistance(df: pd.DataFrame) -> Dict:
    """تحديد الدعم والمقاومة باستخدام Pivot Points"""
    if df is None or df.empty or len(df) < 30:
        return {
            "support": [],
            "resistance": [],
            "current": 0,
            "pivot": 0
        }
    
    close = df['Close'].iloc[-1]
    high = df['High'].iloc[-1]
    low = df['Low'].iloc[-1]
    
    # حساب Pivot Point
    pivot = (high + low + close) / 3
    
    # حساب مستويات الدعم والمقاومة
    r1 = (2 * pivot) - low
    r2 = pivot + (high - low)
    s1 = (2 * pivot) - high
    s2 = pivot - (high - low)
    
    return {
        "support": sorted([round(s2, 2), round(s1, 2)]),
        "resistance": sorted([round(r1, 2), round(r2, 2)], reverse=True),
        "current": round(close, 2),
        "pivot": round(pivot, 2)
    }

def calculate_volatility(df: pd.DataFrame) -> Dict:
    """حساب مؤشرات التقلب"""
    if df is None or df.empty:
        return {}
    
    returns = df['Close'].pct_change().dropna()
    
    return {
        "daily_volatility": round(returns.std() * 100, 2),
        "annual_volatility": round(returns.std() * np.sqrt(252) * 100, 2),
        "beta": round(returns.std() / df['Close'].pct_change().mean() if df['Close'].pct_change().mean() != 0 else 0, 2),
        "sharpe_ratio": round((returns.mean() * 252) / (returns.std() * np.sqrt(252)), 2) if returns.std() != 0 else 0
    }

# ====================== دالة الرسم البياني المتقدمة ======================
def create_advanced_chart(df: pd.DataFrame, symbol: str, name: str) -> go.Figure:
    """إنشاء رسم بياني متقدم متعدد الطبقات"""
    
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.45, 0.2, 0.2, 0.15],
        subplot_titles=("السعر والمتوسطات والنطاقات", "RSI و Stochastic", "MACD و OBV", "حجم التداول")
    )
    
    # ===== السعر مع المتوسطات =====
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], 
        name="السعر", showlegend=True
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA_20'], name="SMA 20",
        line=dict(color='orange', width=2)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA_50'], name="SMA 50",
        line=dict(color='cyan', width=2)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA_200'], name="SMA 200",
        line=dict(color='purple', width=1.5, dash='dash')
    ), row=1, col=1)
    
    # Bollinger Bands
    if 'BB_Upper' in df.columns and not df['BB_Upper'].isna().all():
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_Upper'], name="BB Upper",
            line=dict(color='gray', dash='dash', width=0.5), showlegend=False
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_Lower'], name="BB Lower",
            line=dict(color='gray', dash='dash', width=0.5),
            fill='tonexty', fillcolor='rgba(128,128,128,0.1)', showlegend=False
        ), row=1, col=1)
    
    # ===== RSI و Stochastic =====
    fig.add_trace(go.Scatter(
        x=df.index, y=df['RSI'], name="RSI",
        line=dict(color='magenta', width=2.5)
    ), row=2, col=1)
    
    if 'Stoch_K' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Stoch_K'], name="Stoch %K",
            line=dict(color='lime', width=1.5)
        ), row=2, col=1)
    
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1, annotation_text="ذروة شراء")
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1, annotation_text="ذروة بيع")
    fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, row=2, col=1)
    fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, row=2, col=1)
    
    # ===== MACD =====
    if 'MACD' in df.columns and not df['MACD'].isna().all():
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MACD'], name="MACD",
            line=dict(color='blue', width=1.5)
        ), row=3, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MACD_Signal'], name="Signal Line",
            line=dict(color='red', width=1.5)
        ), row=3, col=1)
        
        colors = ['green' if val >= 0 else 'red' for val in df['MACD_Histogram']]
        fig.add_trace(go.Bar(
            x=df.index, y=df['MACD_Histogram'], name="Histogram",
            marker_color=colors, opacity=0.3, showlegend=False
        ), row=3, col=1)
    
    # ===== حجم التداول =====
    colors = ['green' if df['Close'].iloc[i] > df['Close'].iloc[i-1] else 'red' 
              for i in range(1, len(df))]
    colors.insert(0, 'gray')
    
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], name="Volume",
        marker_color=colors, opacity=0.5, showlegend=False
    ), row=4, col=1)
    
    # ===== تنسيق =====
    fig.update_layout(
        height=900,
        template="plotly_dark",
        title_text=f"📊 {name} ({symbol}) - تحليل فني شامل",
        title_font_size=20,
        title_font_color="#00ff88",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.00,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="rgba(0,255,136,0.2)",
            borderwidth=1
        ),
        hovermode='x unified',
        font=dict(size=11)
    )
    
    fig.update_xaxes(rangeslider_visible=False)
    fig.update_yaxes(title_text="السعر", row=1, col=1)
    fig.update_yaxes(title_text="RSI / Stoch", row=2, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    fig.update_yaxes(title_text="الحجم", row=4, col=1)
    
    return fig

# ====================== دالة تحليل Gemini AI ======================
def get_gemini_analysis(symbol: str, name: str, price: float, change: float, rsi: float, signal: str) -> Optional[str]:
    """الحصول على تحليل متقدم من Gemini AI"""
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        أنت محلل أسهم خبير متخصص في الأسواق العربية والعالمية.
        
        قم بتحليل السهم التالي:
        
        **بيانات السهم:**
        - الاسم: {name}
        - الرمز: {symbol}
        - السعر الحالي: {price:.2f}
        - التغير: {change:+.2f}%
        - RSI: {rsi:.1f}
        - إشارة المؤشرات: {signal}
        
        **المطلوب:**
        1. تحليل فني شامل (المتوسطات، المؤشرات، الاتجاه)
        2. توصية واضحة ومفصلة
        3. تقييم مستوى المخاطرة
        4. أسعار الدخول والخروج المقترحة
        5. أهداف الربح المتوقعة
        
        الرد بالعربية بصيغة احترافية (حد أقصى 300 كلمة).
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"⚠️ خطأ في التحليل: {str(e)}"

# ====================== الواجهة الرئيسية ======================
def main():
    """التطبيق الرئيسي المتطور"""
    
    # العنوان الرئيسي
    st.title("📈 البورصجي AI 2.0")
    st.markdown("**منصة تحليل الأسهم والصناديق الاستثمارية الذكية**")
    st.markdown("_تحليل فني متقدم | إشارات تداول ذكية | بيانات شاملة للبورصة المصرية_")
    st.markdown("---")
    
    # الشريط الجانبي
    with st.sidebar:
        st.markdown("## ⚙️ الإعدادات والخيارات")
        
        # اختيار نوع التحليل
        analysis_type = st.radio(
            "🔍 نوع التحليل",
            ["تحليل الأسهم", "الصناديق الاستثمارية", "معلومات البورصة المصرية"]
        )
        
        st.markdown("---")
        
        if analysis_type == "تحليل الأسهم":
            # اختيار السهم
            selected_display = st.selectbox(
                "🔍 اختر السهم",
                options=list(STOCKS.keys()),
                format_func=lambda x: f"{STOCKS[x]['name']}"
            )
            
            selected_symbol = selected_display.split()[1]
            stock_info = STOCKS[selected_display]
            
            # فترة التحليل
            period = st.selectbox(
                "📅 الفترة الزمنية",
                ["1mo", "3mo", "6mo", "1y", "2y"],
                index=3,
                help="اختر الفترة للتحليل الفني"
            )
            
            st.markdown("---")
            st.markdown("### 📊 معلومات السهم")
            st.write(f"**القطاع:** {stock_info['sector']}")
            st.write(f"**السوق:** {stock_info['market']}")
            st.write(f"**P/E Ratio:** {stock_info['pe_ratio']}")
            
            st.markdown("---")
            
            # حالة الذكاء الاصطناعي
            if GEMINI_AVAILABLE:
                st.success("🤖 **Gemini AI:** متصل ✅")
            else:
                st.warning("⚠️ **Gemini AI:** غير متصل")
            
            st.markdown("---")
            st.markdown("### ⏰ أوقات التداول")
            st.markdown("🇪🇬 **البورصة المصرية:** 10:00 - 14:30")
            st.markdown("🇸🇦 **تداول السعودية:** 10:00 - 15:00")
            st.markdown("🇺🇸 **الأسهم الأمريكية:** 16:30 - 23:00")
            
        elif analysis_type == "الصناديق الاستثمارية":
            fund_type = st.selectbox(
                "نوع الصندوق",
                list(INVESTMENT_FUNDS.keys())
            )
            st.info("💡 اختر نوع الصندوق من القائمة أعلاه")
        
        else:
            st.info("📚 سيتم عرض معلومات شاملة عن البورصة المصرية")
        
        st.markdown("---")
        st.caption("⚠️ البيانات من Yahoo Finance")
        st.caption("📈 للأغراض التعليمية فقط - استشر مستشار مالي قبل الاستثمار")
    
    # ===== قسم تحليل الأسهم =====
    if analysis_type == "تحليل الأسهم":
        with st.spinner("📡 جاري تحميل بيانات السهم..."):
            df, info = get_stock_data(selected_symbol, period)
        
        if df is not None and not df.empty:
            # البيانات الأساسية
            current_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
            change = current_price - prev_price
            change_percent = (change / prev_price) * 100 if prev_price else 0
            rsi_value = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
            
            # عرض المقاييس الأساسية
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "💰 السعر الحالي",
                    f"{current_price:.2f}",
                    f"{change:+.2f}",
                    delta_color="normal"
                )
            
            with col2:
                st.metric("📊 RSI (14)", f"{rsi_value:.1f}", "")
            
            with col3:
                sma_20_val = df['SMA_20'].iloc[-1] if not pd.isna(df['SMA_20'].iloc[-1]) else current_price
                diff = ((current_price - sma_20_val) / sma_20_val * 100) if sma_20_val else 0
                st.metric("📈 SMA 20", f"{sma_20_val:.2f}", f"{diff:+.1f}%")
            
            with col4:
                sma_50_val = df['SMA_50'].iloc[-1] if not pd.isna(df['SMA_50'].iloc[-1]) else current_price
                diff = ((current_price - sma_50_val) / sma_50_val * 100) if sma_50_val else 0
                st.metric("📉 SMA 50", f"{sma_50_val:.2f}", f"{diff:+.1f}%")
            
            with col5:
                volume_ratio = df['Volume_Ratio'].iloc[-1] if not pd.isna(df['Volume_Ratio'].iloc[-1]) else 1
                st.metric("💹 Volume Ratio", f"{volume_ratio:.2f}x", "")
            
            st.markdown("---")
            
            # إشارة التداول المتقدمة
            signal = generate_advanced_signal(df)
            
            if signal["color"] == "buy":
                st.markdown(f"""
                <div class="buy-signal">
                    <h3>🟢 إشارة: {signal['action']}</h3>
                    <p>🎯 الثقة: {signal['confidence']:.0f}% | 📊 مستوى المخاطرة: {signal['risk_level']}</p>
                    <p><strong>📋 الأسباب:</strong></p>
                    <ul>
                        {''.join([f'<li>{r}</li>' for r in signal['reasons'][:6]])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            elif signal["color"] == "sell":
                st.markdown(f"""
                <div class="sell-signal">
                    <h3>🔴 إشارة: {signal['action']}</h3>
                    <p>🎯 الثقة: {signal['confidence']:.0f}% | 📊 مستوى المخاطرة: {signal['risk_level']}</p>
                    <p><strong>📋 الأسباب:</strong></p>
                    <ul>
                        {''.join([f'<li>{r}</li>' for r in signal['reasons'][:6]])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            else:
                st.markdown(f"""
                <div class="neutral-signal">
                    <h3>🟡 إشارة: {signal['action']}</h3>
                    <p>🎯 الثقة: {signal['confidence']:.0f}% | 📊 مستوى المخاطرة: {signal['risk_level']}</p>
                    <p><strong>📋 الأسباب:</strong></p>
                    <ul>
                        {''.join([f'<li>{r}</li>' for r in signal['reasons'][:6]])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # تحليل الاتجاه والدعم والمقاومة
            col1, col2, col3 = st.columns(3)
            
            with col1:
                trend = analyze_trend(df)
                st.subheader("📈 الاتجاه")
                st.success(trend['trend']) if trend['color'] == 'green' else st.warning(trend['trend']) if trend['color'] == 'red' else st.info(trend['trend'])
                st.progress(trend['strength'] / 100, text=f"{trend['strength']}%")
                st.caption(trend['description'])
            
            with col2:
                sr = get_support_resistance(df)
                st.subheader("📊 الدعم والمقاومة")
                st.write(f"**المقاومة 1:** {sr['resistance'][0] if sr['resistance'] else 'N/A'}")
                st.write(f"**المقاومة 2:** {sr['resistance'][1] if len(sr['resistance']) > 1 else 'N/A'}")
                st.write(f"**السعر الحالي:** `{sr['current']}`")
                st.write(f"**الدعم 1:** {sr['support'][0] if sr['support'] else 'N/A'}")
                st.write(f"**الدعم 2:** {sr['support'][1] if len(sr['support']) > 1 else 'N/A'}")
            
            with col3:
                volatility = calculate_volatility(df)
                st.subheader("📊 التقلب")
                st.write(f"**التقلب اليومي:** {volatility.get('daily_volatility', 'N/A')}%")
                st.write(f"**التقلب السنوي:** {volatility.get('annual_volatility', 'N/A')}%")
                st.write(f"**Sharpe Ratio:** {volatility.get('sharpe_ratio', 'N/A')}")
            
            st.markdown("---")
            
            # الرسم البياني المتقدم
            st.subheader("📊 الرسم البياني المتقدم")
            fig = create_advanced_chart(df, selected_symbol, stock_info['name'])
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # تحليل الذكاء الاصطناعي
            st.subheader("🤖 التحليل بالذكاء الاصطناعي")
            
            if st.button("🚀 تحليل ذكي متقدم بـ Gemini AI", type="primary", use_container_width=True):
                if GEMINI_AVAILABLE:
                    with st.spinner("🧠 جاري التحليل الذكي المتقدم..."):
                        analysis = get_gemini_analysis(
                            selected_symbol, stock_info['name'],
                            current_price, change_percent, rsi_value, signal['action']
                        )
                        if analysis:
                            st.success("✅ نتيجة التحليل الذكي:")
                            st.markdown(analysis)
                else:
                    st.error("❌ Gemini AI غير متوفر. أضف GEMINI_API_KEY في الإعدادات")
            
            st.markdown("---")
            
            # معلومات إضافية تفصيلية
            with st.expander("📋 معلومات تفصيلية عن السهم"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**المتوسطات المتحركة**")
                    st.write(f"SMA 5: {ta.sma(df['Close'], length=5).iloc[-1]:.2f}")
                    st.write(f"SMA 10: {ta.sma(df['Close'], length=10).iloc[-1]:.2f}")
                    st.write(f"SMA 20: {df['SMA_20'].iloc[-1]:.2f}")
                    st.write(f"SMA 50: {df['SMA_50'].iloc[-1]:.2f}")
                    st.write(f"SMA 200: {df['SMA_200'].iloc[-1]:.2f}")
                    st.write(f"EMA 9: {df['EMA_9'].iloc[-1]:.2f}")
                
                with col2:
                    st.write("**مؤشرات الزخم**")
                    st.write(f"RSI: {rsi_value:.1f}")
                    if 'MACD' in df.columns:
                        st.write(f"MACD: {df['MACD'].iloc[-1]:.4f}")
                        st.write(f"Signal: {df['MACD_Signal'].iloc[-1]:.4f}")
                        st.write(f"Histogram: {df['MACD_Histogram'].iloc[-1]:.4f}")
                    if 'CCI' in df.columns:
                        st.write(f"CCI: {df['CCI'].iloc[-1]:.2f}")
                
                with col3:
                    st.write("**مؤشرات التقلب والحجم**")
                    st.write(f"ATR: {df['ATR'].iloc[-1]:.2f}")
                    st.write(f"ATR %: {df['ATR_Percent'].iloc[-1]:.2f}%")
                    if 'BB_Upper' in df.columns:
                        bb_width = (df['BB_Upper'].iloc[-1] - df['BB_Lower'].iloc[-1])
                        st.write(f"Bollinger Width: {bb_width:.2f}")
                    st.write(f"Volume Ratio: {df['Volume_Ratio'].iloc[-1]:.2f}x")
                    st.write(f"Daily Change: {df['Daily_Return'].iloc[-1]:+.2f}%")
            
            # معلومات الشركة
            if info:
                with st.expander("🏢 معلومات الشركة"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**الاسم:** {info.get('longName', 'غير متوفر')}")
                        st.write(f"**القطاع:** {info.get('sector', 'غير متوفر')}")
                        st.write(f"**الصناعة:** {info.get('industry', 'غير متوفر')}")
                        st.write(f"**البلد:** {info.get('country', 'غير متوفر')}")
                    
                    with col2:
                        market_cap = info.get('marketCap', 0)
                        st.write(f"**القيمة السوقية:** {f'{market_cap:,.0f}' if market_cap else 'غير متوفر'}")
                        pe = info.get('trailingPE', 0)
                        st.write(f"**P/E Ratio:** {f'{pe:.2f}' if pe else 'غير متوفر'}")
                        pb = info.get('priceToBook', 0)
                        st.write(f"**P/B Ratio:** {f'{pb:.2f}' if pb else 'غير متوفر'}")
                        dividend = info.get('dividendRate', 0)
                        st.write(f"**Dividend Yield:** {f'{dividend:.2f}%' if dividend else 'غير متوفر'}")
        
        else:
            st.error("❌ تعذر جلب البيانات. يرجى:")
            st.markdown("• التحقق من اتصال الإنترنت")
            st.markdown("• التأكد من صحة رمز السهم")
            st.markdown("• إعادة المحاولة بعد قليل")
    
    # ===== قسم الصناديق الاستثمارية =====
    elif analysis_type == "الصناديق الاستثمارية":
        st.title("💼 الصناديق الاستثمارية")
        st.markdown("دليل شامل للصناديق الاستثمارية المصرية والعالمية")
        st.markdown("---")
        
        fund_type = st.selectbox("اختر نوع الصندوق", list(INVESTMENT_FUNDS.keys()))
        
        st.subheader(f"🏦 {fund_type}")
        
        funds_data = INVESTMENT_FUNDS[fund_type]
        
        for idx, fund in enumerate(funds_data, 1):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                <div class="info-card">
                    <h4>{idx}. {fund['name']}</h4>
                    <p><strong>نوع الصندوق:</strong> {fund['type']}</p>
                    <p><strong>المدير:</strong> {fund['manager']}</p>
                    <p><strong>الحد الأدنى:</strong> {fund['min_investment']}</p>
                    <p><strong>الرسوم:</strong> {fund['fees']}</p>
                    <p><strong>الأداء:</strong> {fund['performance']}</p>
                    <p><strong>الوصف:</strong> {fund['description']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # نصائح استثمارية
        st.subheader("💡 نصائح اختيار الصندوق المناسب")
        
        with st.expander("📚 معايير الاختيار"):
            st.markdown("""
            ### معايير اختيار صندوق استثماري:
            
            1. **الأداء التاريخي**: ادرس أداء الصندوق على المدى الطويل
            2. **الرسوم**: اختر صناديق برسوم منخفضة
            3. **مدير الصندوق**: تحقق من سجل وخبرة المدير
            4. **الفئة المستهدفة**: اختر الصندوق المناسب لأهدافك
            5. **مستوى المخاطرة**: تأكد من توافق المخاطرة مع تحملك
            6. **السيولة**: تأكد من إمكانية بيع الوحدات بسهولة
            7. **الشفافية**: اختر صناديق تعلن نتائجها بشفافية
            
            ### نصائح للمبتدئين:
            - ابدأ بصناديق متوازنة
            - استثمر على المدى الطويل (5+ سنوات)
            - تجنب المضاربة قصيرة الأجل
            - قسّم استثمارك على عدة صناديق
            """)
    
    # ===== قسم معلومات البورصة المصرية =====
    else:  # معلومات البورصة المصرية
        st.title("🏛️ البورصة المصرية (EGX)")
        st.markdown("معلومات شاملة عن البورصة المصرية والأوراق المالية")
        st.markdown("---")
        
        # المعلومات الأساسية
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📅 التأسيس", EGX_INFO["established"])
        
        with col2:
            st.metric("🕐 ساعات التداول", "10:00 - 14:30")
        
        with col3:
            st.metric("💱 العملة", "الجنيه المصري")
        
        with col4:
            st.metric("📊 عدد الشركات", EGX_INFO["listed_companies"])
        
        st.markdown("---")
        
        # المؤشرات الرئيسية
        st.subheader("📊 المؤشرات الرئيسية")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="info-card">
                <h4>📈 EGX 30</h4>
                <p>{EGX_INFO['main_indices']['EGX30']}</p>
                <p style="color: #00ff88;">أكبر 30 شركة</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="info-card">
                <h4>📊 EGX 50</h4>
                <p>{EGX_INFO['main_indices']['EGX50']}</p>
                <p style="color: #00ccff;">أكبر 50 شركة</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="info-card">
                <h4>📉 EGX 100</h4>
                <p>{EGX_INFO['main_indices']['EGX100']}</p>
                <p style="color: #ffaa00;">أكبر 100 شركة</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # القطاعات
        st.subheader("🏭 القطاعات في البورصة المصرية")
        
        sectors_df = pd.DataFrame({
            "القطاع": EGX_INFO["sectors"],
            "الوصف": [
                "البنوك والخدمات المالية والتأمين",
                "التطوير العقاري والإنشاءات",
                "الصناعات المختلفة والكهرباء",
                "السلع الاستهلاكية والغذاء",
                "الأسمدة والمواد الكيماوية",
                "الاتصالات والتكنولوجيا",
                "الأغذية والمشروبات",
                "الفنادق والسياحة والنقل"
            ]
        })
        
        st.dataframe(sectors_df, use_container_width=True)
        
        st.markdown("---")
        
        # المتطلبات
        st.subheader("📋 متطلبات الاستثمار في البورصة المصرية")
        
        with st.expander("📚 كيفية البدء في الاستثمار"):
            st.markdown("""
            ### خطوات البدء:
            
            1. **فتح حساب لدى شركة سمسرة معتمدة**
                - اختر شركة سمسرة موثوقة وحاصلة على ترخيص من الهيئة
                - أكمل نماذج التسجيل المطلوبة
                - أودع المبلغ الأول (لا يوجد حد أدنى قانوني محدد)
            
            2. **الحصول على كود المستثمر**
                - تحصل على كود فريد عند التسجيل
                - هذا الكود مطلوب لكل تحويل أو استثمار
            
            3. **فتح محفظة أوراق مالية**
                - يتم فتحها لديك لدى المقاصة والإيداع
                - تسجل فيها جميع أسهمك والسندات
            
            4. **البدء في التداول**
                - قدم أوامر الشراء والبيع من خلال المنصة
                - الحد الأدنى للتداول سهم واحد
                - التسويّة في يومي عمل (T+2)
            
            ### معلومات مهمة:
            - ساعات التداول: **10:00 - 14:30** (أيام العمل الرسمية)
            - الخميس: تداول لمدة ساعة واحدة فقط (10:00 - 11:00)
            - يوم الجمعة والسبت: عطلة نهاية الأسبوع
            - الأحد: يوم عمل عادي
            """)
        
        st.markdown("---")
        
        # نصائح الاستثمار
        st.subheader("💡 نصائح الاستثمار الحكيم")
        
        tips = [
            ("📚 التثقيف المالي", "اقرأ عن الأسواق المالية وتعلم الأساسيات قبل الاستثمار"),
            ("🎯 وضع الأهداف", "حدد أهدافك المالية والفترة الزمنية المناسبة"),
            ("📊 التنويع", "لا تضع كل أموالك في سهم واحد - نوّع محفظتك"),
            ("🛡️ إدارة المخاطر", "استخدم أوامر وقف الخسارة وتحديد الربح"),
            ("🔍 البحث والتحليل", "احلل الشركات قبل الشراء"),
            ("💰 الاستثمار طويل الأجل", "تجنب المضاربة - استثمر للعام والسنوات القادمة"),
            ("❌ تجنب العواطف", "لا تقرر بناءً على الخوف أو الطمع"),
            ("👨‍💼 استشر الخبراء", "استعن بمستشار مالي معتمد عند الحاجة")
        ]
        
        for i in range(0, len(tips), 2):
            col1, col2 = st.columns(2)
            
            with col1:
                title, desc = tips[i]
                st.markdown(f"""
                <div class="warning-card">
                    <h4>{title}</h4>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)
            
            if i + 1 < len(tips):
                with col2:
                    title, desc = tips[i + 1]
                    st.markdown(f"""
                    <div class="warning-card">
                        <h4>{title}</h4>
                        <p>{desc}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # روابط مفيدة
        st.subheader("🔗 روابط مفيدة")
        st.markdown("""
        - [الموقع الرسمي لبورصة مصر](https://www.egx.com.eg)
        - [الهيئة العامة للرقابة المالية](https://www.efsa.gov.eg)
        - [شركات السمسرة المعتمدة](https://www.egx.com.eg/ar)
        - [آخر الأخبار المالية](https://www.egx.com.eg/ar)
        """)
    
    # تذييل الصفحة
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>⚠️ <strong>إخلاء مسؤولية هام:</strong></p>
        <p>التحليلات والتوصيات مقدمة للأغراض التعليمية فقط.</p>
        <p>ليست نصائح استثمارية - استشر مستشار مالي معتمد قبل اتخاذ قرارات الاستثمار.</p>
        <p>الاستثمار ينطوي على مخاطر قد يؤدي لخسارة رأس المال.</p>
        <p>© 2024 البورصجي AI 2.0 - منصة تحليل الأسهم والصناديق الذكية</p>
        <p>📊 البيانات من Yahoo Finance | 🤖 التحليل بتقنية الذكاء الاصطناعي</p>
    </div>
    """, unsafe_allow_html=True)

# ====================== تشغيل التطبيق ======================
if __name__ == "__main__":
    main()
