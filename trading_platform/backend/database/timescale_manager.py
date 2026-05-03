"""
ملف: backend/database/timescale_manager.py
المسار: /trading_platform/backend/database/timescale_manager.py
الوظيفة: إدارة قاعدة البيانات الزمنية (TimescaleDB)
"""

import asyncpg
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from loguru import logger

class TimescaleManager:
    """مدير قاعدة البيانات الزمنية"""
    
    def __init__(self, dsn: str = "postgresql://trader:secure_password_2024@timescaledb:5432/trading_db"):
        self.dsn = dsn
        self.pool = None
        
    async def initialize(self):
        """تهيئة الاتصال بقاعدة البيانات"""
        try:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            # إنشاء الجداول إذا لم تكن موجودة
            await self.create_tables()
            
            logger.info("✅ تم تهيئة TimescaleDB بنجاح")
            
        except Exception as e:
            logger.error(f"خطأ في تهيئة TimescaleDB: {e}")
            raise
    
    async def create_tables(self):
        """إنشاء الجداول اللازمة"""
        async with self.pool.acquire() as conn:
            # تفعيل TimescaleDB extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
            
            # جدول بيانات الأسهم
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_prices (
                    time TIMESTAMPTZ NOT NULL,
                    symbol TEXT NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    volume BIGINT,
                    high DECIMAL(10, 2),
                    low DECIMAL(10, 2),
                    change_percent DECIMAL(10, 2)
                );
            """)
            
            # تحويل إلى hypertable
            await conn.execute("""
                SELECT create_hypertable('stock_prices', 'time', if_not_exists => TRUE);
            """)
            
            # إنشاء فهارس
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_stock_symbol_time 
                ON stock_prices (symbol, time DESC);
            """)
            
            # جدول المؤشرات الفنية
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS technical_indicators (
                    time TIMESTAMPTZ NOT NULL,
                    symbol TEXT NOT NULL,
                    rsi DECIMAL(5, 2),
                    macd DECIMAL(10, 4),
                    sma_20 DECIMAL(10, 2),
                    sma_50 DECIMAL(10, 2),
                    volume_ratio DECIMAL(5, 2)
                );
            """)
            
            await conn.execute("""
                SELECT create_hypertable('technical_indicators', 'time', if_not_exists => TRUE);
            """)
            
            # جدول التوصيات
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    time TIMESTAMPTZ NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target_price DECIMAL(10, 2),
                    confidence DECIMAL(5, 2),
                    reasons TEXT[]
                );
            """)
            
            logger.info("✅ تم إنشاء جميع الجداول")
    
    async def insert_stock_data(self, stock_data):
        """إدخال بيانات السهم"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO stock_prices (time, symbol, price, volume, change_percent)
                    VALUES ($1, $2, $3, $4, $5)
                """, 
                    datetime.now(),
                    stock_data.symbol,
                    stock_data.price,
                    stock_data.volume,
                    stock_data.change_percent
                )
        except Exception as e:
            logger.error(f"خطأ في إدخال بيانات {stock_data.symbol}: {e}")
    
    async def insert_indicators(self, symbol: str, indicators):
        """إدخال المؤشرات الفنية"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO technical_indicators 
                    (time, symbol, rsi, macd, sma_20, sma_50, volume_ratio)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    datetime.now(),
                    symbol,
                    indicators.rsi,
                    indicators.macd,
                    indicators.sma_20,
                    indicators.sma_50,
                    indicators.volume_ratio
                )
        except Exception as e:
            logger.error(f"خطأ في إدخال مؤشرات {symbol}: {e}")
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.DataFrame:
        """جلب البيانات التاريخية"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT time, price, volume, change_percent
                    FROM stock_prices
                    WHERE symbol = $1 
                    AND time BETWEEN $2 AND $3
                    ORDER BY time ASC
                """, symbol, start_date, end_date)
                
                if not rows:
                    return pd.DataFrame()
                
                df = pd.DataFrame([dict(row) for row in rows])
                df.set_index('time', inplace=True)
                return df
                
        except Exception as e:
            logger.error(f"خطأ في جلب تاريخ {symbol}: {e}")
            return pd.DataFrame()
    
    async def ping(self):
        """اختبار الاتصال"""
        async with self.pool.acquire() as conn:
            await conn.execute("SELECT 1")
    
    async def close(self):
        """إغلاق الاتصال"""
        if self.pool:
            await self.pool.close()
            logger.info("تم إغلاق اتصال TimescaleDB")
