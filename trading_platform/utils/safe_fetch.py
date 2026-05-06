"""
ملف: utils/safe_fetch.py
المسار: /trading_platform/utils/safe_fetch.py
الوظيفة: صمام أمان لمنع انهيار التطبيق
"""

import streamlit as st
import functools
import time
from typing import Any, Callable
from loguru import logger

# ====================== ديكوراتير الحماية ======================
def safe_fetch(max_retries: int = 3, delay: float = 1.0, fallback_value: Any = None):
    """
    ديكوراتير لحماية الدوال من الانهيار
    يعيد المحاولة تلقائياً ويعرض رسائل ودية للمستخدم
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    logger.error(f"خطأ في {func.__name__}: {e}")
                    
                    if attempt < max_retries - 1:
                        # عرض رسالة للمستخدم
                        st.warning(f"⚠️ جاري إعادة المحاولة ({attempt + 1}/{max_retries})...")
                        time.sleep(delay)
                    else:
                        # فشل كل المحاولات
                        st.error(f"⚠️ عذراً، لا يمكن جلب البيانات حالياً. سيتم استخدام بيانات مؤقتة.")
                        return fallback_value
            
            return fallback_value
        return wrapper
    return decorator

# ====================== ديكوراتير للتخزين المؤقت ======================
def cached(ttl: int = 300):
    """تخزين النتائج في الكاش لتقليل الطلبات"""
    cache = {}
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()
            
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl:
                    return result
            
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result
        return wrapper
    return decorator

# ====================== ديكوراتير لقياس الأداء ======================
def measure_performance(func: Callable) -> Callable:
    """قياس وقت تنفيذ الدالة"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(f"⚡ {func.__name__} استغرق {elapsed:.2f}ms")
        return result
    return wrapper

# ====================== مثال للاستخدام ======================
@safe_fetch(max_retries=3, fallback_value={"price": 0, "change": 0})
def get_stock_price(symbol: str) -> dict:
    """جلب سعر السهم بشكل آمن"""
    import yfinance as yf
    stock = yf.Ticker(symbol)
    info = stock.info
    
    return {
        "symbol": symbol,
        "price": info.get('regularMarketPrice', 0),
        "change": info.get('regularMarketChange', 0)
    }

# ====================== معالج الأخطاء العام ======================
class GracefulErrorHandler:
    """معالج أخطاء ودود للمستخدم"""
    
    @staticmethod
    def show_user_friendly_error(error: Exception, context: str = ""):
        """عرض رسالة خطأ مفهومة للمستخدم"""
        
        error_messages = {
            "ConnectionError": "⚠️ **مشكلة في الاتصال**\nيرجى التحقق من اتصالك بالإنترنت",
            "TimeoutError": "⏰ **انتهت مهلة الاتصال**\nالخادم بطيء حالياً، حاول مرة أخرى",
            "KeyError": "🔑 **مشكلة في البيانات**\nقد يكون رمز السهم غير صحيح",
            "ValueError": "📊 **بيانات غير متوقعة**\nجاري استخدام بيانات احتياطية",
        }
        
        error_type = type(error).__name__
        message = error_messages.get(error_type, f"⚠️ **حدث خطأ**: {str(error)}")
        
        if context:
            message = f"**في {context}:**\n{message}"
        
        st.error(message)
        
        # تسجيل الخطأ للتطوير
        logger.error(f"{context}: {error}")
