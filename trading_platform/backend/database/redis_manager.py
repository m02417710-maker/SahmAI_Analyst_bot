"""
ملف: backend/database/redis_manager.py
المسار: /trading_platform/backend/database/redis_manager.py
الوظيفة: إدارة Redis للتخزين المؤقت والبيانات اللحظية
"""

import redis.asyncio as redis
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger

class RedisManager:
    """مدير Redis للتخزين المؤقت"""
    
    def __init__(self, redis_url: str = "redis://:redis_secure_pass@redis:6379"):
        self.redis_url = redis_url
        self.client = None
        
    async def initialize(self):
        """تهيئة الاتصال بـ Redis"""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=20
            )
            
            # اختبار الاتصال
            await self.client.ping()
            
            logger.info("✅ تم تهيئة Redis بنجاح")
            
        except Exception as e:
            logger.error(f"خطأ في تهيئة Redis: {e}")
            raise
    
    async def set(self, key: str, value: Any, expiry: int = 3600):
        """تخزين قيمة مع صلاحية"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, str):
                value = str(value)
            
            await self.client.setex(key, expiry, value)
        except Exception as e:
            logger.error(f"خطأ في تخزين {key}: {e}")
    
    async def get(self, key: str) -> Optional[str]:
        """استرجاع قيمة"""
        try:
            value = await self.client.get(key)
            
            # محاولة تحويل JSON
            if value and (value.startswith('{') or value.startswith('[')):
                try:
                    return json.loads(value)
                except:
                    return value
            return value
        except Exception as e:
            logger.error(f"خطأ في استرجاع {key}: {e}")
            return None
    
    async def delete(self, key: str):
        """حذف مفتاح"""
        try:
            await self.client.delete(key)
        except Exception as e:
            logger.error(f"خطأ في حذف {key}: {e}")
    
    async def keys(self, pattern: str) -> List[str]:
        """البحث عن مفاتيح"""
        try:
            return await self.client.keys(pattern)
        except Exception as e:
            logger.error(f"خطأ في البحث عن {pattern}: {e}")
            return []
    
    async def hset(self, key: str, field: str, value: Any):
        """تخزين في hash"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self.client.hset(key, field, value)
        except Exception as e:
            logger.error(f"خطأ في hset {key}: {e}")
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """استرجاع من hash"""
        try:
            return await self.client.hget(key, field)
        except Exception as e:
            logger.error(f"خطأ في hget {key}: {e}")
            return None
    
    async def hgetall(self, key: str) -> Dict:
        """استرجاع كل محتويات hash"""
        try:
            result = await self.client.hgetall(key)
            # محاولة تحويل JSON للقيم
            parsed = {}
            for k, v in result.items():
                if v and (v.startswith('{') or v.startswith('[')):
                    try:
                        parsed[k] = json.loads(v)
                    except:
                        parsed[k] = v
                else:
                    parsed[k] = v
            return parsed
        except Exception as e:
            logger.error(f"خطأ في hgetall {key}: {e}")
            return {}
    
    async def store_market_snapshot(self, snapshot: Dict):
        """تخزين لمحة سوق كاملة"""
        try:
            await self.set("market:latest", snapshot, expiry=60)
            
            # تخزين كل سهم على حدة
            for symbol, data in snapshot.items():
                await self.set(f"stock:{symbol}", data.__dict__, expiry=5)
                
        except Exception as e:
            logger.error(f"خطأ في تخزين لمحة السوق: {e}")
    
    async def get_market_snapshot(self) -> Optional[Dict]:
        """استرجاع آخر لمحة سوق"""
        try:
            return await self.get("market:latest")
        except Exception as e:
            logger.error(f"خطأ في استرجاع لمحة السوق: {e}")
            return None
    
    async def ping(self):
        """اختبار الاتصال"""
        await self.client.ping()
    
    async def close(self):
        """إغلاق الاتصال"""
        if self.client:
            await self.client.close()
            logger.info("تم إغلاق اتصال Redis")
