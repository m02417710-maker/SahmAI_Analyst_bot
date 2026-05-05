"""
ملف: backend/optimization/performance_optimizer.py
المسار: /trading_platform/backend/optimization/performance_optimizer.py
الوظيفة: محسن الأداء لتسريع التطبيق وتحسين الاستجابة
"""

import asyncio
import functools
import time
from typing import Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from numba import jit, cuda
from loguru import logger

class PerformanceOptimizer:
    """محسن الأداء المتقدم"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=16)
        self.cache = {}
        self.metrics = {}
        
    # ====================== تحسين الحسابات ======================
    @staticmethod
    @jit(nopython=True, parallel=True)
    def fast_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """حساب RSI بسرعة فائقة باستخدام Numba"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = np.nan
        rsi[period] = 100 - 100 / (1 + rs)
        
        for i in range(period + 1, len(prices)):
            delta = deltas[i - 1]
            if delta > 0:
                up_val = delta
                down_val = 0
            else:
                up_val = 0
                down_val = -delta
            
            up = (up * (period - 1) + up_val) / period
            down = (down * (period - 1) + down_val) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100 - 100 / (1 + rs)
        
        return rsi
    
    @staticmethod
    @jit(nopython=True)
    def fast_sma(prices: np.ndarray, period: int) -> np.ndarray:
        """حساب SMA بسرعة فائقة"""
        sma = np.zeros_like(prices)
        sma[:] = np.nan
        
        for i in range(period - 1, len(prices)):
            sma[i] = np.mean(prices[i - period + 1:i + 1])
        
        return sma
    
    @staticmethod
    def fast_correlation(x: np.ndarray, y: np.ndarray) -> float:
        """حساب معامل الارتباط بسرعة"""
        return np.corrcoef(x, y)[0, 1]
    
    # ====================== كاش ذكي متعدد المستويات ======================
    class SmartCache:
        """كاش ذكي مع خوارزمية LFU"""
        
        def __init__(self, max_size: int = 1000):
            self.max_size = max_size
            self.cache = {}
            self.frequency = {}
            self.access_time = {}
        
        def get(self, key: str) -> Any:
            if key in self.cache:
                self.frequency[key] = self.frequency.get(key, 0) + 1
                self.access_time[key] = time.time()
                return self.cache[key]
            return None
        
        def set(self, key: str, value: Any):
            if len(self.cache) >= self.max_size:
                # إزالة أقل العناصر استخداماً (LFU)
                lfu_key = min(self.frequency, key=lambda k: (self.frequency[k], self.access_time[k]))
                del self.cache[lfu_key]
                del self.frequency[lfu_key]
                del self.access_time[lfu_key]
            
            self.cache[key] = value
            self.frequency[key] = 1
            self.access_time[key] = time.time()
    
    # ====================== تحسين الطلبات المتوازية ======================
    async def parallel_batch_process(self, items: list, processor: Callable, batch_size: int = 50):
        """معالجة دفعات متوازية"""
        results = []
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
        
        tasks = []
        for batch in batches:
            batch_tasks = [processor(item) for item in batch]
            tasks.append(asyncio.gather(*batch_tasks))
        
        batch_results = await asyncio.gather(*tasks)
        for batch in batch_results:
            results.extend(batch)
        
        return results
    
    # ====================== تحسين قاعدة البيانات ======================
    class OptimizedQueryBuilder:
        """بناء استعلامات محسنة"""
        
        @staticmethod
        def build_time_range_query(table: str, symbol: str, start: datetime, end: datetime) -> str:
            return f"""
            SELECT * FROM {table}
            WHERE symbol = '{symbol}'
            AND time BETWEEN '{start.isoformat()}' AND '{end.isoformat()}'
            ORDER BY time DESC
            LIMIT 10000
            """
        
        @staticmethod
        def build_aggregate_query(table: str, symbol: str, interval: str = '1 hour') -> str:
            return f"""
            SELECT 
                time_bucket('{interval}', time) AS bucket,
                symbol,
                FIRST(price, time) as open,
                MAX(price) as high,
                MIN(price) as low,
                LAST(price, time) as close,
                SUM(volume) as volume
            FROM {table}
            WHERE symbol = '{symbol}'
            GROUP BY bucket, symbol
            ORDER BY bucket DESC
            """
    
    # ====================== تحسين الذاكرة ======================
    class MemoryOptimizer:
        """محسن استخدام الذاكرة"""
        
        @staticmethod
        def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
            """تحسين استهلاك الذاكرة لل DataFrame"""
            for col in df.select_dtypes(include=['float64']).columns:
                df[col] = df[col].astype('float32')
            
            for col in df.select_dtypes(include=['int64']).columns:
                df[col] = df[col].astype('int32')
            
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].nunique() / len(df) < 0.5:
                    df[col] = df[col].astype('category')
            
            return df
        
        @staticmethod
        def get_memory_usage(df: pd.DataFrame) -> Dict:
            """الحصول على تفاصيل استخدام الذاكرة"""
            return {
                'total_memory': df.memory_usage(deep=True).sum() / 1024**2,
                'by_column': df.memory_usage(deep=True).to_dict()
            }
    
    # ====================== تحسين الشبكة ======================
    class NetworkOptimizer:
        """محسن أداء الشبكة"""
        
        def __init__(self):
            self.session = None
            self.connector_limit = 100
        
        async def get_optimized_session(self):
            """الحصول على جلسة HTTP محسنة"""
            import aiohttp
            
            if not self.session:
                connector = aiohttp.TCPConnector(
                    limit=self.connector_limit,
                    ttl_dns_cache=300,
                    keepalive_timeout=30
                )
                timeout = aiohttp.ClientTimeout(total=30, connect=5)
                self.session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout
                )
            return self.session
        
        async def batch_requests(self, urls: List[str]) -> List[Dict]:
            """إرسال طلبات HTTP متعددة بشكل متوازي"""
            session = await self.get_optimized_session()
            
            async def fetch(url):
                async with session.get(url) as response:
                    return await response.json()
            
            tasks = [fetch(url) for url in urls]
            return await asyncio.gather(*tasks, return_exceptions=True)

# ====================== ديكوراتير تحسين الأداء ======================
def cached(ttl: int = 60):
    """ديكوراتير لتخزين النتائج في الكاش"""
    cache = {}
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    return result
            
            result = await func(*args, **kwargs)
            cache[key] = (result, time.time())
            return result
        return wrapper
    return decorator

def measure_performance(func):
    """ديكوراتير لقياس أداء الدوال"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        
        logger.debug(f"⚡ {func.__name__} took {(end - start)*1000:.2f}ms")
        return result
    return wrapper
