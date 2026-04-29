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
import base64
import asyncio
import threading
from queue import Queue
import json

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
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ يرجى إضافة GEMINI_API_KEY في .streamlit/secrets.toml")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# ====================== 3. إعداد تليجرام ======================
class TelegramBot:
    """كلاس للتعامل مع بوت تليجرام"""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
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
            st.error(f"خطأ في إرسال رسالة تليجرام: {e}")
            return False
    
    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        """إرسال صورة إلى تليجرام"""
        if not self.bot_token or not self.chat_id:
            return False
        
        try:
            url = f"{self.base_url}/sendPhoto"
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': self.chat_id, 'caption': caption}
                response = requests.post(url, files=files, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            st.error(f"خطأ في إرسال صورة تليجرام: {e}")
            return False
    
    def send_document(self, document_path: str, caption: str = "") -> bool:
        """إرسال ملف إلى تليجرام"""
        if not self.bot_token or not self.chat_id:
            return False
        
        try:
            url = f"{self.base_url}/sendDocument"
            with open(document_path, 'rb') as doc:
                files = {'document': doc}
                data = {'chat_id': self.chat_id, 'caption': caption}
                response = requests.post(url, files=files, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            st.error(f"خطأ في إرسال ملف تليجرام: {e}")
            return False
    
    def send_analysis_report(self, ticker: str, analysis: str, metrics: Dict) -> bool:
        """إرسال تقرير تحليل كامل"""
        message = f"""
📊 <b>تقرير تحليل سهم {ticker}</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>🏢 الشركة:</b> {egyptian_stocks.get(ticker, 'N/A')}

<b>📈 المؤشرات الرئيسية:</b>
• السعر الحالي: {metrics.get('current_price', 'N/A')} ج.م
• التغير اليومي: {metrics.get('change_pct', 'N/A')}%
• RSI: {metrics.get('rsi', 'N/A')}
• المتوسط المتحرك 20: {metrics.get('sma_20', 'N/A')}

<b>🎯 التوصية:</b>
{analysis[:500]}

🔗 <a href="https://stock-analyst-egypt.streamlit.app">تطبيق المحلل المالي</a>
        """
        return self.send_message(message)
    
    def send_alert(self, ticker: str, alert_type: str, message: str) -> bool:
        """إرسال تنبيه فوري"""
        emoji = "🔴" if alert_type == "danger" else "🟢" if alert_type == "success" else "⚠️"
        alert_msg = f"""
{emoji} <b>تنبيه فوري - {ticker}</b>

{message}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return self.send_message(alert_msg)

# ====================== 4. كلاس إدارة المحفظة ======================
class Portfolio:
    """إدارة محفظة استثمارية"""
    def __init__(self):
        if 'portfolio' not in st.session_state:
            st.session_state.portfolio = {'holdings': {}, 'cash': 100000, 'transactions': []}
    
    def add_position(self, ticker: str, shares: float, price: float):
        """إضافة مركز جديد"""
        if ticker in st.session_state.portfolio['holdings']:
            old_shares = st.session_state.portfolio['holdings'][ticker]['shares']
            old_avg = st.session_state.portfolio['holdings'][ticker]['avg_price']
            new_shares = old_shares + shares
            new_avg = (old_shares * old_avg + shares * price) / new_shares
            st.session_state.portfolio['holdings'][ticker]['shares'] = new_shares
            st.session_state.portfolio['holdings'][ticker]['avg_price'] = new_avg
        else:
            st.session_state.portfolio['holdings'][ticker] = {
                'shares': shares, 
                'avg_price': price
            }
        
        st.session_state.portfolio['cash'] -= shares * price
        st.session_state.portfolio['transactions'].append({
            'date': datetime.now(),
            'ticker': ticker,
            'type': 'BUY',
            'shares': shares,
            'price': price,
            'value': shares * price
        })
    
    def remove_position(self, ticker: str, shares: float, price: float):
        """بيع أسهم من مركز"""
        if ticker in st.session_state.portfolio['holdings']:
            current_shares = st.session_state.portfolio['holdings'][ticker]['shares']
            if shares >= current_shares:
                del st.session_state.portfolio['holdings'][ticker]
            else:
                st.session_state.portfolio['holdings'][ticker]['shares'] -= shares
            
            st.session_state.portfolio['cash'] += shares * price
            st.session_state.portfolio['transactions'].append({
                'date': datetime.now(),
                'ticker': ticker,
                'type': 'SELL',
                'shares': shares,
                'price': price,
                'value': shares * price
            })
    
    def calculate_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """حساب القيمة الحالية للمحفظة"""
        total = st.session_state.portfolio['cash']
        for ticker, holding in st.session_state.portfolio['holdings'].items():
            if ticker in current_prices:
                total += holding['shares'] * current_prices[ticker]
        return total
    
    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> pd.DataFrame:
        """الحصول على ملخص المحفظة"""
        summary = []
        for ticker, holding in st.session_state.portfolio['holdings'].items():
            current_price = current_prices.get(ticker, holding['avg_price'])
            current_value = holding['shares'] * current_price
            cost_basis = holding['shares'] * holding['avg_price']
            pnl = current_value - cost_basis
            pnl_pct = (pnl / cost_basis) * 100 if cost_basis > 0 else 0
            
            summary.append({
                'السهم': ticker,
                'الكمية': holding['shares'],
                'متوسط السعر': holding['avg_price'],
                'السعر الحالي': current_price,
                'القيمة الحالية': current_value,
                'ربح/خسارة': pnl,
                'نسبة الربح/الخسارة': pnl_pct
            })
        
        return pd.DataFrame(summary)

# ====================== 5. دوال مساعدة محسنة ======================
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
    if 'price_alerts' not in st.session_state:
        st.session_state.price_alerts = {}
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True
    if 'telegram_alerts_enabled' not in st.session_state:
        st.session_state.telegram_alerts_enabled = False
    if 'last_alert_time' not in st.session_state:
        st.session_state.last_alert_time = {}

def check_alerts_with_telegram(df: pd.DataFrame, ticker: str, telegram_bot: TelegramBot) -> List[str]:
    """فحص التنبيهات المخصصة وإرسالها إلى تليجرام"""
    alerts = []
    if df.empty or len(df) < 2:
        return alerts
    
    last_price = df['Close'].iloc[-1]
    last_rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 50
    current_time = datetime.now()
    
    # التحقق من عدم إرسال نفس التنبيه خلال آخر ساعة
    alert_key = f"{ticker}_last_alert"
    last_alert = st.session_state.last_alert_time.get(alert_key)
    if last_alert and (current_time - last_alert).seconds < 3600:
        return alerts
    
    # تنبيهات مخصصة من ملف الإعدادات
    if ticker in st.session_state.price_alerts:
        for alert_price in st.session_state.price_alerts[ticker]:
            if abs(last_price - alert_price) / alert_price < 0.01:  # 1% threshold
                alert_msg = f"⚠️ السهم {ticker} وصل للسعر المستهدف {alert_price:.2f}\nالسعر الحالي: {last_price:.2f}"
                alerts.append(alert_msg)
                if st.session_state.telegram_alerts_enabled:
                    telegram_bot.send_alert(ticker, "warning", alert_msg)
                st.session_state.last_alert_time[alert_key] = current_time
    
    # تنبيهات RSI
    if last_rsi > 80:
        alert_msg = f"🔴 تنبيه: {ticker} في منطقة ذروة شراء خطيرة!\nRSI: {last_rsi:.1f}\nالسعر: {last_price:.2f}"
        alerts.append(alert_msg)
        if st.session_state.telegram_alerts_enabled:
            telegram_bot.send_alert(ticker, "danger", alert_msg)
        st.session_state.last_alert_time[alert_key] = current_time
    elif last_rsi < 20:
        alert_msg = f"🟢 تنبيه: {ticker} في منطقة ذروة بيع - فرصة شراء!\nRSI: {last_rsi:.1f}\nالسعر: {last_price:.2f}"
        alerts.append(alert_msg)
        if st.session_state.telegram_alerts_enabled:
            telegram_bot.send_alert(ticker, "success", alert_msg)
        st.session_state.last_alert_time[alert_key] = current_time
    
    # تنبيهات المتوسطات المتحركة
    if 'SMA_20' in df.columns and len(df) > 20:
        sma_20 = df['SMA_20'].iloc[-1]
        if last_price > sma_20 * 1.05:
            alert_msg = f"📈 {ticker} اخترق المتوسط المتحرك لأعلى بنسبة 5%\nالسعر: {last_price:.2f}\nالمتوسط: {sma_20:.2f}"
            alerts.append(alert_msg)
            if st.session_state.telegram_alerts_enabled:
                telegram_bot.send_alert(ticker, "success", alert_msg)
            st.session_state.last_alert_time[alert_key] = current_time
        elif last_price < sma_20 * 0.95:
            alert_msg = f"📉 {ticker} كسر المتوسط المتحرك لأسفل بنسبة 5%\nالسعر: {last_price:.2f}\nالمتوسط: {sma_20:.2f}"
            alerts.append(alert_msg)
            if st.session_state.telegram_alerts_enabled:
                telegram_bot.send_alert(ticker, "danger", alert_msg)
            st.session_state.last_alert_time[alert_key] = current_time
    
    return alerts

def calculate_risk_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """حساب مقاييس المخاطرة المتقدمة"""
    if df.empty or len(df) < 2:
        return {}
    
    returns = df['Close'].pct_change().dropna()
    
    metrics = {
        'Sharpe Ratio': (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0,
        'Sortino Ratio': (returns.mean() / returns[returns < 0].std()) * np.sqrt(252) if len(returns[returns < 0]) > 0 and returns[returns < 0].std() > 0 else 0,
        'Max Drawdown': (df['Close'] / df['Close'].cummax() - 1).min() * 100,
        'Volatility': returns.std() * np.sqrt(252) * 100,
        'VaR (95%)': returns.quantile(0.05) * 100,
        'CVaR (95%)': returns[returns <= returns.quantile(0.05)].mean() * 100 if len(returns[returns <= returns.quantile(0.05)]) > 0 else 0
    }
    
    return metrics

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
    if len(df) >= 5:
        price_change = ((last_price - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
        if price_change > 5:
            signals.append(f"🚀 ارتفاع حاد خلال 5 أيام ({price_change:.1f}%)")
        elif price_change < -5:
            signals.append(f"📉 انخفاض حاد خلال 5 أيام ({price_change:.1f}%)")
    
    return signals

@st.cache_data(ttl=300, show_spinner=False)
def get_egyptian_stock_with_retry(ticker: str, period: str = "1y", max_retries: int = 3):
    """جلب بيانات السهم مع إعادة المحاولة"""
    for attempt in range(max_retries):
        try:
            df, info, ticker_result = get_egyptian_stock(ticker, period)
            if df is not None and not df.empty:
                return df, info, ticker_result
            time.sleep(1)
        except Exception as e:
            if attempt == max_retries - 1:
                st.warning(f"فشل جلب {ticker} بعد {max_retries} محاولات: {e}")
            else:
                time.sleep(2)
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

def get_enhanced_ai_analysis(df: pd.DataFrame, ticker: str, portfolio_context: str = "") -> str:
    """تحليل معمق مع سياق المحفظة"""
    if df.empty or len(df) < 20:
        return "⚠️ بيانات غير كافية للتحليل"
    
    last_price = df['Close'].iloc[-1]
    last_rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 50
    
    green_days = (df['Close'] > df['Open']).tail(20).sum() if len(df) >= 20 else 0
    avg_volume = df['Volume_SMA'].iloc[-1] if 'Volume_SMA' in df.columns and not pd.isna(df['Volume_SMA'].iloc[-1]) else df['Volume'].mean()
    
    macd_signal = "إيجابي"
    if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
        macd_signal = "إيجابي" if df['MACD'].iloc[-1] > df['MACD_Signal'].iloc[-1] else "سلبي"
    
    trend = "صاعد" if df['Close'].iloc[-1] > df['SMA_20'].iloc[-1] else "هابط"
    
    prompt = f"""
    تحليل متقدم للسهم {ticker} في البورصة المصرية:
    
    📊 البيانات الفنية (آخر 20 يوم):
    - السعر الحالي: {last_price:.2f}
    - أعلى سعر: {df['High'].tail(20).max():.2f}
    - أدنى سعر: {df['Low'].tail(20).min():.2f}
    - المتوسط المتحرك 20: {df['SMA_20'].iloc[-1]:.2f if 'SMA_20' in df.columns else 'N/A'}
    - RSI الحالي: {last_rsi:.1f}
    
    📈 نماذج الشموع اليابانية:
    - عدد الأيام الخضراء: {green_days}/20
    - حجم التداول الأخير: {df['Volume'].iloc[-1]:,.0f}
    - متوسط الحجم: {avg_volume:,.0f}
    
    🎯 نماذج فنية تم اكتشافها:
    - {'صالبة صاعدة' if trend == 'صاعد' else 'صالبة هابطة'}
    - مؤشر MACD {macd_signal}
    
    {portfolio_context}
    
    المطلوب:
    1. تحليل الاتجاه الأسبوعي والشهري
    2. تحديد نقاط الدعم والمقاومة الرئيسية
    3. تحليل RSI وتقييم حالة السوق
    4. توصية محددة مع نقاط الدخول والخروج
    5. نسبة المخاطرة/العائد المتوقعة
    6. توصية واضحة (شراء/بيع/انتظار)
    
    الرد بشكل احترافي ومختصر مع أرقام محددة وباللغة العربية.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ خطأ في التحليل: {str(e)}"

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
        template="plotly_dark" if st.session_state.dark_mode else "plotly_white",
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
        template="plotly_dark" if st.session_state.dark_mode else "plotly_white",
        xaxis_title="التاريخ",
        yaxis_title="الأداء (%)",
        hovermode='x unified'
    )
    
    return fig

def export_to_excel(df: pd.DataFrame, ticker: str) -> bytes:
    """تصدير البيانات إلى Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'{ticker}_Data', index=True)
        
        technical_cols = [col for col in ['Close', 'SMA_20', 'EMA_9', 'RSI', 'Volume'] if col in df.columns]
        if technical_cols:
            technical_df = df[technical_cols].tail(20)
            technical_df.to_excel(writer, sheet_name='Technical_Indicators', index=True)
    
    return output.getvalue()

# ====================== 6. الواجهة الرئيسية ======================
def main():
    # تهيئة الجلسة والمحفظة
    init_session_state()
    portfolio = Portfolio()
    
    # إعداد بوت تليجرام
    telegram_bot = TelegramBot()
    
    # إعداد الوضع المظلم
    dark_mode = st.sidebar.toggle("🌙 الوضع المظلم", value=st.session_state.dark_mode)
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()
    
    if not st.session_state.dark_mode:
        st.markdown("""
            <style>
            .stApp { background-color: #ffffff; }
            </style>
        """, unsafe_allow_html=True)
    
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
        
        # عرض حالة الاتصال
        if telegram_bot.bot_token and telegram_bot.chat_id:
            st.success("✅ بوت تليجرام متصل")
            
            # تفعيل التنبيهات
            telegram_alerts = st.toggle("🔔 تفعيل التنبيهات التلقائية", value=st.session_state.telegram_alerts_enabled)
            if telegram_alerts != st.session_state.telegram_alerts_enabled:
                st.session_state.telegram_alerts_enabled = telegram_alerts
                if telegram_alerts:
                    telegram_bot.send_message("✅ تم تفعيل التنبيهات التلقائية من تطبيق محلل الأسهم المصري")
                    st.success("تم تفعيل التنبيهات")
            
            # زر إرسال تقرير فوري
            if st.button("📊 إرسال تقرير السوق الآن"):
                with st.spinner("جاري إعداد التقرير..."):
                    # جلب أداء السوق
                    results = []
                    for ticker in list(egyptian_stocks.keys())[:10]:
                        df, _, _ = get_egyptian_stock(ticker, "5d")
                        if df is not None and not df.empty and len(df) >= 2:
                            change = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                            results.append({
                                "ticker": ticker,
                                "change": change,
                                "price": df['Close'].iloc[-1]
                            })
                    
                    # ترتيب النتائج
                    results.sort(key=lambda x: x['change'], reverse=True)
                    
                    # إعداد الرسالة
                    message = "📊 <b>تقرير سريع للسوق المصري</b>\n\n"
                    message += "<b>🚀 أعلى 5 صاعدين:</b>\n"
                    for r in results[:5]:
                        message += f"• {r['ticker']}: {r['change']:+.2f}% ({r['price']:.2f})\n"
                    
                    message += "\n<b>📉 أعلى 5 هابطين:</b>\n"
                    for r in results[-5:]:
                        message += f"• {r['ticker']}: {r['change']:+.2f}% ({r['price']:.2f})\n"
                    
                    telegram_bot.send_message(message)
                    st.success("تم إرسال التقرير إلى تليجرام")
        else:
            st.warning("⚠️ لم يتم إعداد بوت تليجرام")
            st.info("لإعداد البوت:
1. أضف TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID في secrets.toml
2. تواصل مع @BotFather لإنشاء بوت جديد")
            
            # نموذج لإدخال بيانات البوت يدوياً
            with st.expander("🔧 إعداد البوت يدوياً"):
                bot_token = st.text_input("توكن البوت", type="password", key="manual_bot_token")
                chat_id = st.text_input("Chat ID", key="manual_chat_id")
                if st.button("💾 حفظ الإعدادات"):
                    if bot_token and chat_id:
                        # حفظ مؤقت للإعدادات
                        st.session_state.temp_bot_token = bot_token
                        st.session_state.temp_chat_id = chat_id
                       
