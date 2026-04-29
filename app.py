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
import time
from fpdf import FPDF

# ====================== 1. إعداد الكاش والمكتبات ======================
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
# ملاحظة: أضف GEMINI_API_KEY في .streamlit/secrets.toml
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ يرجى إضافة GEMINI_API_KEY في .streamlit/secrets.toml")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# ====================== 3. إعداد تليجرام ======================
class TelegramBot:
    """كلاس للتعامل مع بوت تليجرام"""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        # استخدم التوكن من secrets أو من المدخلات
        self.bot_token = bot_token or st.secrets.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or st.secrets.get("TELEGRAM_CHAT_ID", "")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """إرسال رسالة نصية إلى تليجرام"""
        if not self.bot_token or not self.chat_id:
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"خطأ في إرسال رسالة تليجرام: {e}")
            return False
    
    def send_alert(self, ticker: str, alert_type: str, message: str) -> bool:
        """إرسال تنبيه فوري"""
        emoji = "🔴" if alert_type == "danger" else "🟢" if alert_type == "success" else "⚠️"
        alert_msg = f"""
{emoji} <b>تنبيه فوري - {ticker}</b>

{message}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return self.send_message(alert_msg)

# ====================== 4. قائمة الأسهم المصرية ======================
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

# ====================== 5. دوال مساعدة ======================
def init_session_state():
    """تهيئة متغيرات الجلسة"""
    if 'favorite_stocks' not in st.session_state:
        st.session_state.favorite_stocks = []
    if 'last_analysis' not in st.session_state:
        st.session_state.last_analysis = {}
    if 'analysis_cache' not in st.session_state:
        st.session_state.analysis_cache = {}
    if 'price_alerts' not in st.session_state:
        st.session_state.price_alerts = {}
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True
    if 'telegram_alerts_enabled' not in st.session_state:
        st.session_state.telegram_alerts_enabled = False
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = {'holdings': {}, 'cash': 100000, 'transactions': []}

@st.cache_data(ttl=300)
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

def get_technical_summary(df: pd.DataFrame) -> List[str]:
    """تلخيص المؤشرات الفنية"""
    if df.empty or len(df) < 20:
        return ["⚠️ بيانات غير كافية للتحليل"]
    
    last_rsi = df['RSI'].iloc[-1]
    last_price = df['Close'].iloc[-1]
    sma_20 = df['SMA_20'].iloc[-1] if not pd.isna(df['SMA_20'].iloc[-1]) else last_price
    
    signals = []
    
    if last_rsi > 70:
        signals.append("⚠️ ذروة شراء (RSI > 70)")
    elif last_rsi < 30:
        signals.append("✅ ذروة بيع (RSI < 30)")
    else:
        signals.append("⚖️ منطقة محايدة")
    
    if last_price > sma_20:
        signals.append("📈 السعر أعلى من المتوسط 20 (اتجاه صاعد)")
    else:
        signals.append("📉 السعر أقل من المتوسط 20 (اتجاه هابط)")
    
    if len(df) >= 5:
        price_change = ((last_price - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
        if price_change > 5:
            signals.append(f"🚀 ارتفاع حاد خلال 5 أيام ({price_change:.1f}%)")
        elif price_change < -5:
            signals.append(f"📉 انخفاض حاد خلال 5 أيام ({price_change:.1f}%)")
    
    return signals

def create_advanced_chart(df: pd.DataFrame, ticker: str):
    """إنشاء رسم بياني متقدم"""
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05,
        row_heights=[0.5, 0.2, 0.15, 0.15],
        subplot_titles=(f"السعر - {ticker}", "RSI", "MACD", "حجم التداول")
    )
    
    # السعر مع Candlestick
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
    
    fig.update_layout(
        height=800,
        template="plotly_dark" if st.session_state.dark_mode else "plotly_white",
        title_text=f"تحليل فني متقدم - {ticker}",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_xaxes(rangeslider_visible=False)
    
    return fig

def compare_stocks(ticker1: str, ticker2: str, period: str = "1y"):
    """مقارنة بين سهمين"""
    df1, _, _ = get_egyptian_stock(ticker1, period)
    df2, _, _ = get_egyptian_stock(ticker2, period)
    
    if df1 is None or df2 is None:
        return None
    
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
        template="plotly_dark" if st.session_state.dark_mode else "plotly_white",
        xaxis_title="التاريخ",
        yaxis_title="الأداء (%)",
        hovermode='x unified'
    )
    
    return fig

def check_alerts(df: pd.DataFrame, ticker: str, telegram_bot: TelegramBot) -> List[str]:
    """فحص التنبيهات وإرسالها لتليجرام"""
    alerts = []
    if df.empty or len(df) < 2:
        return alerts
    
    last_price = df['Close'].iloc[-1]
    last_rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 50
    
    # تنبيهات الأسعار
    if ticker in st.session_state.price_alerts:
        for alert_price in st.session_state.price_alerts[ticker]:
            if abs(last_price - alert_price) / alert_price < 0.01:
                alert_msg = f"⚠️ السهم {ticker} وصل للسعر المستهدف {alert_price:.2f}"
                alerts.append(alert_msg)
                if st.session_state.telegram_alerts_enabled:
                    telegram_bot.send_alert(ticker, "warning", alert_msg)
    
    # تنبيهات RSI
    if last_rsi > 80:
        alert_msg = f"🔴 {ticker} في منطقة ذروة شراء خطيرة! RSI: {last_rsi:.1f}"
        alerts.append(alert_msg)
        if st.session_state.telegram_alerts_enabled:
            telegram_bot.send_alert(ticker, "danger", alert_msg)
    elif last_rsi < 20:
        alert_msg = f"🟢 {ticker} في منطقة ذروة بيع - فرصة شراء! RSI: {last_rsi:.1f}"
        alerts.append(alert_msg)
        if st.session_state.telegram_alerts_enabled:
            telegram_bot.send_alert(ticker, "success", alert_msg)
    
    return alerts

# ====================== 6. الواجهة الرئيسية ======================
def main():
    # تهيئة الجلسة
    init_session_state()
    
    # إعداد بوت تليجرام
    telegram_bot = TelegramBot()
    
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
        
        # إعدادات تليجرام
        st.subheader("🤖 إعدادات تليجرام")
        
        # التحقق من وجود توكن
        if telegram_bot.bot_token and telegram_bot.chat_id:
            st.success("✅ بوت تليجرام متصل")
            st.session_state.telegram_alerts_enabled = st.toggle("🔔 تفعيل التنبيهات", value=st.session_state.telegram_alerts_enabled)
        else:
            st.warning("⚠️ لم يتم إعداد بوت تليجرام")
            st.info("لإعداد البوت، أضف في ملف secrets.toml:\n"
                   "TELEGRAM_BOT_TOKEN = 'your_token'\n"
                   "TELEGRAM_CHAT_ID = 'your_chat_id'")
        
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
            st.info("لا توجد أسهم مفضلة")
        
        st.divider()
        
        # المحفظة
        st.subheader("💰 محفظتي")
        st.metric("الرصيد", f"{st.session_state.portfolio['cash']:,.2f} ج.م")
        st.metric("المراكز", len(st.session_state.portfolio['holdings']))
        
        st.divider()
        st.caption("⚠️ بيانات تجريبية | للأغراض التعليمية")
    
    # الصفحات
    page = st.radio(
        "📑 اختر القسم",
        ["🔍 تحليل سهم", "📊 أداء الأسهم", "📰 تحليل السوق", "📈 مقارنة أسهم", "⚙️ الإعدادات"],
        horizontal=True
    )
    
    # ====================== صفحة تحليل سهم ======================
    if page == "🔍 تحليل سهم":
        st.header("🔍 تحليل سهم فردي")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            selected = st.selectbox(
                "اختر السهم",
                options=list(egyptian_stocks.keys()),
                format_func=lambda x: f"{x} — {egyptian_stocks[x]}"
            )
        
        with col2:
            period = st.selectbox("الفترة", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)
        
        # إضافة للمفضلة
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(f"⭐ إضافة للمفضلة"):
                if selected not in st.session_state.favorite_stocks:
                    st.session_state.favorite_stocks.append(selected)
                    st.success(f"تمت الإضافة")
        
        with col2:
            alert_price = st.number_input("سعر التنبيه", min_value=0.01, step=0.01, key="alert_price")
            if st.button("➕ تنبيه"):
                if selected not in st.session_state.price_alerts:
                    st.session_state.price_alerts[selected] = []
                if alert_price > 0:
                    st.session_state.price_alerts[selected].append(alert_price)
                    st.success(f"تم إضافة تنبيه عند {alert_price}")
        
        with col3:
            if st.button("🔄 تحديث"):
                st.cache_data.clear()
                st.rerun()
        
        # جلب البيانات
        with st.spinner("جاري تحليل السهم..."):
            hist, info, ticker = get_egyptian_stock(selected, period)
        
        if hist is not None and not hist.empty:
            # المقاييس الأساسية
            curr_price = info.get('currentPrice') or hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else curr_price
            change_pct = ((curr_price - prev_price) / prev_price) * 100 if prev_price else 0
            last_rsi = hist['RSI'].iloc[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💰 السعر", f"{curr_price:.2f} ج.م", f"{change_pct:.2f}%")
            col2.metric("📊 RSI", f"{last_rsi:.1f}")
            col3.metric("🏢 الشركة", egyptian_stocks.get(ticker, ticker)[:20])
            col4.metric("📅 التحديث", datetime.now().strftime("%H:%M:%S"))
            
            # فحص التنبيهات
            alerts = check_alerts(hist, ticker, telegram_bot)
            for alert in alerts:
                st.warning(alert)
            
            # الملخص الفني
            signals = get_technical_summary(hist)
            st.info("📊 **الملخص:** " + " | ".join(signals))
            
            # الرسم البياني
            fig = create_advanced_chart(hist, ticker)
            st.plotly_chart(fig, use_container_width=True)
            
            # نقاط الدعم والمقاومة
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 مقاومة")
                for i, price in enumerate(hist['High'].tail(50).nlargest(3), 1):
                    st.write(f"R{i}: {price:.2f}")
            
            with col2:
                st.subheader("📉 دعم")
                for i, price in enumerate(hist['Low'].tail(50).nsmallest(3), 1):
                    st.write(f"S{i}: {price:.2f}")
            
            # تحليل Gemini
            if st.button("🤖 تحليل ذكي", type="primary"):
                with st.spinner("جاري التحليل..."):
                    prompt = f"""
                    حلل السهم {ticker} في البورصة المصرية:
                    السعر: {curr_price:.2f}, RSI: {last_rsi:.1f}
                    التغير: {change_pct:.2f}%
                    قدم توصية مختصرة بالعربية.
                    """
                    try:
                        response = model.generate_content(prompt)
                        st.success(response.text)
                    except Exception as e:
                        st.error(f"خطأ: {e}")
        
        else:
            st.error("❌ تعذر جلب البيانات")
    
    # ====================== صفحة أداء الأسهم ======================
    elif page == "📊 أداء الأسهم":
        st.header("📊 أداء الأسهم المصرية")
        
        with st.spinner("جاري التحليل..."):
            results = []
            for ticker in egyptian_stocks.keys():
                try:
                    df = yf.Ticker(ticker).history(period="5d")
                    if not df.empty and len(df) >= 2:
                        change = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                        results.append({
                            "السهم": ticker,
                            "الاسم": egyptian_stocks[ticker],
                            "التغير": round(change, 2),
                            "السعر": round(df['Close'].iloc[-1], 2)
                        })
                except:
                    pass
            
            if results:
                df_perf = pd.DataFrame(results)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("📈 متوسط التغير", f"{df_perf['التغير'].mean():.2f}%")
                col2.metric("🚀 أعلى صعود", f"{df_perf['التغير'].max():.2f}%")
                col3.metric("📉 أعلى هبوط", f"{df_perf['التغير'].min():.2f}%")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🚀 الصاعدين")
                    st.dataframe(df_perf.nlargest(10, "التغير"), hide_index=True)
                with col2:
                    st.subheader("🔻 الهابطة")
                    st.dataframe(df_perf.nsmallest(10, "التغير"), hide_index=True)
                
                # رسم بياني
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df_perf['الاسم'][:15],
                    y=df_perf['التغير'][:15],
                    marker_color=['green' if x > 0 else 'red' for x in df_perf['التغير'][:15]]
                ))
                fig.update_layout(title="أداء الأسهم", template="plotly_dark" if st.session_state.dark_mode else "plotly_white")
                st.plotly_chart(fig, use_container_width=True)
    
    # ====================== صفحة تحليل السوق ======================
    elif page == "📰 تحليل السوق":
        st.header("📰 تحليل البورصة المصرية")
        
        if st.button("📊 تحليل السوق الآن", type="primary"):
            with st.spinner("جاري التحليل..."):
                prompt = """
                قدم تحليل للبورصة المصرية اليوم:
                - أداء المؤشرات
                - القطاعات النشطة
                - التوقعات
                الرد بالعربية
                """
                try:
                    response = model.generate_content(prompt)
                    st.success(response.text)
                except Exception as e:
                    st.error(f"خطأ: {e}")
    
    # ====================== صفحة مقارنة ======================
    elif page == "📈 مقارنة أسهم":
        st.header("📈 مقارنة الأسهم")
        
        col1, col2 = st.columns(2)
        with col1:
            stock1 = st.selectbox("السهم الأول", list(egyptian_stocks.keys()), key="comp1")
        with col2:
            stock2 = st.selectbox("السهم الثاني", list(egyptian_stocks.keys()), index=1, key="comp2")
        
        period = st.selectbox("الفترة", ["1mo", "3mo", "6mo", "1y"])
        
        if st.button("مقارنة"):
            fig = compare_stocks(stock1, stock2, period)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
    
    # ====================== صفحة الإعدادات ======================
    elif page == "⚙️ الإعدادات":
        st.header("⚙️ إعدادات التطبيق")
        
        st.subheader("🎨 المظهر")
        dark = st.toggle("الوضع المظلم", value=st.session_state.dark_mode)
        if dark != st.session_state.dark_mode:
            st.session_state.dark_mode = dark
            st.rerun()
        
        st.subheader("🤖 إعدادات تليجرام")
        st.info("""
        لإعداد بوت تليجرام:
        
        1. قم بإنشاء ملف `.streamlit/secrets.toml`
        2. أضف فيه:
