"""
ملف: backend/api/market_data.py
المسار: /trading_platform/backend/api/market_data.py
الوظيفة: إدارة جلب البيانات من مصادر متعددة (لحظية وتاريخية)
"""

import asyncio
import aiohttp
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
import redis.asyncio as redis
from abc import ABC, abstractmethod

# ====================== نماذج البيانات ======================
@dataclass
class StockData:
    """نموذج بيانات السهم"""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    high_52w: float
    low_52w: float
    timestamp: datetime
    
@dataclass
class TechnicalIndicators:
    """المؤشرات الفنية"""
    rsi: float
    macd: float
    macd_signal: float
    sma_20: float
    sma_50: float
    bb_upper: float
    bb_lower: float
    volume_ratio: float

# ====================== مزودي البيانات ======================
class DataProvider(ABC):
    """واجهة موحدة لمقدمي البيانات"""
    
    @abstractmethod
    async def get_realtime_price(self, symbol: str) -> float:
        pass
    
    @abstractmethod
    async def get_historical_data(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        pass

class YahooFinanceProvider(DataProvider):
    """مزود Yahoo Finance"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 5  # seconds
    
    async def get_realtime_price(self, symbol: str) -> float:
        """جلب السعر اللحظي"""
        cache_key = f"price_{symbol}"
        
        # التحقق من الكاش
        if cache_key in self.cache:
            cached_time, cached_price = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_ttl:
                return cached_price
        
        try:
            # تشغيل في thread pool لأن yfinance متزامن
            loop = asyncio.get_event_loop()
            stock = await loop.run_in_executor(None, yf.Ticker, symbol)
            info = await loop.run_in_executor(None, lambda: stock.info)
            
            price = info.get('regularMarketPrice', 0)
            if price == 0:
                price = info.get('currentPrice', 0)
            
            # تخزين في الكاش
            self.cache[cache_key] = (datetime.now(), price)
            return price
            
        except Exception as e:
            logger.error(f"خطأ في جلب سعر {symbol}: {e}")
            return 0.0
    
    async def get_historical_data(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        """جلب البيانات التاريخية"""
        try:
            loop = asyncio.get_event_loop()
            stock = await loop.run_in_executor(None, yf.Ticker, symbol)
            df = await loop.run_in_executor(
                None, 
                lambda: stock.history(start=start, end=end)
            )
            return df
        except Exception as e:
            logger.error(f"خطأ في جلب تاريخ {symbol}: {e}")
            return pd.DataFrame()

# ====================== المدير الرئيسي ======================
class MarketDataManager:
    """المدير الرئيسي لبيانات السوق"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.providers = {
            'yahoo': YahooFinanceProvider()
        }
        self.redis_client = None
        self.redis_url = redis_url
        
    async def initialize(self):
        """تهيئة الاتصالات"""
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
        logger.info("✅ تم تهيئة مدير بيانات السوق")
    
    async def get_stock_snapshot(self, symbols: List[str]) -> Dict[str, StockData]:
        """جلب لمحة سريعة لمجموعة أسهم"""
        results = {}
        
        # جلب البيانات بالتوازي
        tasks = [self._get_single_stock_data(symbol) for symbol in symbols]
        stock_data_list = await asyncio.gather(*tasks)
        
        for stock_data in stock_data_list:
            if stock_data:
                results[stock_data.symbol] = stock_data
        
        return results
    
    async def _get_single_stock_data(self, symbol: str) -> Optional[StockData]:
        """جلب بيانات سهم واحد"""
        try:
            # محاولة من الكاش أولاً
            cached = await self.redis_client.get(f"stock:{symbol}")
            if cached:
                import json
                data = json.loads(cached)
                return StockData(**data)
            
            # جلب من المزود
            price = await self.providers['yahoo'].get_realtime_price(symbol)
            if price == 0:
                return None
            
            # جلب معلومات إضافية
            loop = asyncio.get_event_loop()
            stock = await loop.run_in_executor(None, yf.Ticker, symbol)
            info = await loop.run_in_executor(None, lambda: stock.info)
            
            previous_close = info.get('previousClose', price)
            change = price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close else 0
            
            stock_data = StockData(
                symbol=symbol,
                price=price,
                change=change,
                change_percent=change_percent,
                volume=info.get('volume', 0),
                high_52w=info.get('fiftyTwoWeekHigh', price),
                low_52w=info.get('fiftyTwoWeekLow', price),
                timestamp=datetime.now()
            )
            
            # تخزين في الكاش لمدة 5 ثواني
            import json
            await self.redis_client.setex(
                f"stock:{symbol}",
                5,
                json.dumps(stock_data.__dict__, default=str)
            )
            
            return stock_data
            
        except Exception as e:
            logger.error(f"خطأ في بيانات {symbol}: {e}")
            return None
    
    async def get_technical_indicators(self, symbol: str) -> Optional[TechnicalIndicators]:
        """حساب المؤشرات الفنية المتقدمة"""
        try:
            end = datetime.now()
            start = end - timedelta(days=100)  # 100 يوم للتحليل
            
            df = await self.providers['yahoo'].get_historical_data(symbol, start, end)
            
            if df.empty or len(df) < 50:
                return None
            
            import pandas_ta as ta
            
            # حساب المؤشرات
            rsi = ta.rsi(df['Close'], length=14)
            macd_data = ta.macd(df['Close'])
            sma_20 = ta.sma(df['Close'], length=20)
            sma_50 = ta.sma(df['Close'], length=50)
            bb = ta.bbands(df['Close'], length=20)
            
            # المتوسطات
            avg_volume = ta.sma(df['Volume'], length=20)
            volume_ratio = df['Volume'].iloc[-1] / avg_volume.iloc[-1] if avg_volume.iloc[-1] > 0 else 1
            
            indicators = TechnicalIndicators(
                rsi=rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50,
                macd=macd_data['MACD_12_26_9'].iloc[-1] if not pd.isna(macd_data['MACD_12_26_9'].iloc[-1]) else 0,
                macd_signal=macd_data['MACDs_12_26_9'].iloc[-1] if not pd.isna(macd_data['MACDs_12_26_9'].iloc[-1]) else 0,
                sma_20=sma_20.iloc[-1] if not pd.isna(sma_20.iloc[-1]) else df['Close'].iloc[-1],
                sma_50=sma_50.iloc[-1] if not pd.isna(sma_50.iloc[-1]) else df['Close'].iloc[-1],
                bb_upper=bb['BBU_20_2.0'].iloc[-1] if not pd.isna(bb['BBU_20_2.0'].iloc[-1]) else df['Close'].iloc[-1] * 1.05,
                bb_lower=bb['BBL_20_2.0'].iloc[-1] if not pd.isna(bb['BBL_20_2.0'].iloc[-1]) else df['Close'].iloc[-1] * 0.95,
                volume_ratio=volume_ratio
            )
            
            return indicators
            
        except Exception as e:
            logger.error(f"خطأ في حساب المؤشرات لـ {symbol}: {e}")
            return None
    
    async def get_chart_data(self, symbol: str, period: str = "1y") -> Dict:
        """جلب بيانات الرسم البياني (OHLCV)"""
        try:
            end = datetime.now()
            
            # تحديد فترة البدء بناءً على الاختيار
            period_map = {
                "1d": timedelta(days=1),
                "1w": timedelta(weeks=1),
                "1m": timedelta(days=30),
                "3m": timedelta(days=90),
                "6m": timedelta(days=180),
                "1y": timedelta(days=365),
                "2y": timedelta(days=730),
                "5y": timedelta(days=1825)
            }
            
            delta = period_map.get(period, timedelta(days=365))
            start = end - delta
            
            df = await self.providers['yahoo'].get_historical_data(symbol, start, end)
            
            if df.empty:
                return {}
            
            # تحويل إلى JSON للواجهة
            chart_data = {
                'dates': df.index.strftime('%Y-%m-%d').tolist(),
                'open': df['Open'].tolist(),
                'high': df['High'].tolist(),
                'low': df['Low'].tolist(),
                'close': df['Close'].tolist(),
                'volume': df['Volume'].tolist()
            }
            
            return chart_data
            
        except Exception as e:
            logger.error(f"خطأ في بيانات الرسم البياني لـ {symbol}: {e}")
            return {}

# ====================== التشغيل ======================
async def main():
    """اختبار المدير"""
    manager = MarketDataManager()
    await manager.initialize()
    
    # اختبار جلب بيانات سهم
    data = await manager.get_stock_snapshot(["COMI.CA", "TMGH.CA"])
    for symbol, stock_data in data.items():
        print(f"{symbol}: {stock_data.price} ({stock_data.change_percent:+.2f}%)")
    
    # اختبار المؤشرات
    indicators = await manager.get_technical_indicators("COMI.CA")
    if indicators:
        print(f"RSI: {indicators.rsi:.2f}")
        print(f"متوسط 20: {indicators.sma_20:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
