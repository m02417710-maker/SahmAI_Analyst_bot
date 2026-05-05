"""
ملف: backend/api/public_api.py
المسار: /trading_platform/backend/api/public_api.py
الوظيفة: واجهة برمجة تطبيقات مفتوحة للمطورين
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import APIKeyHeader
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import hashlib
import hmac
import secrets
from pydantic import BaseModel, Field
from loguru import logger

# ====================== نماذج API ======================
class APIRequest(BaseModel):
    symbol: str
    period: Optional[str] = "1d"

class APIResponse(BaseModel):
    success: bool
    data: Dict
    timestamp: str
    rate_limit_remaining: int

class WebhookPayload(BaseModel):
    event_type: str
    symbol: str
    data: Dict
    timestamp: str

# ====================== إدارة المفاتيح ======================
class APIKeyManager:
    """مدير مفاتيح API للمطورين"""
    
    def __init__(self):
        self.api_keys: Dict[str, Dict] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        
    def generate_api_key(self, user_id: str, plan: str = "basic") -> str:
        """توليد مفتاح API جديد"""
        api_key = secrets.token_urlsafe(32)
        api_secret = secrets.token_urlsafe(32)
        
        self.api_keys[api_key] = {
            "user_id": user_id,
            "api_secret": api_secret,
            "plan": plan,
            "created_at": datetime.now(),
            "rate_limit": self._get_rate_limit(plan),
            "requests_count": 0
        }
        
        return api_key
    
    def verify_api_key(self, api_key: str, api_secret: str = None) -> Optional[str]:
        """التحقق من صحة المفتاح"""
        if api_key not in self.api_keys:
            return None
        
        key_data = self.api_keys[api_key]
        
        if api_secret and key_data["api_secret"] != api_secret:
            return None
        
        return key_data["user_id"]
    
    def check_rate_limit(self, api_key: str) -> bool:
        """التحقق من حد الاستخدام"""
        if api_key not in self.api_keys:
            return False
        
        key_data = self.api_keys[api_key]
        limit = key_data["rate_limit"]
        
        # تنظيف الطلبات القديمة
        now = datetime.now()
        if api_key not in self.rate_limits:
            self.rate_limits[api_key] = []
        
        # إزالة الطلبات الأقدم من دقيقة
        self.rate_limits[api_key] = [
            t for t in self.rate_limits[api_key]
            if (now - t).seconds < 60
        ]
        
        # التحقق من الحد
        if len(self.rate_limits[api_key]) >= limit:
            return False
        
        # تسجيل الطلب
        self.rate_limits[api_key].append(now)
        key_data["requests_count"] += 1
        
        return True
    
    def _get_rate_limit(self, plan: str) -> int:
        """حد الاستخدام حسب الخطة"""
        limits = {
            "free": 10,      # 10 طلب في الدقيقة
            "basic": 60,     # 60 طلب في الدقيقة
            "pro": 300,      # 300 طلب في الدقيقة
            "enterprise": 1000  # 1000 طلب في الدقيقة
        }
        return limits.get(plan, 10)
    
    def get_remaining_requests(self, api_key: str) -> int:
        """الطلبات المتبقية"""
        if api_key not in self.api_keys:
            return 0
        
        limit = self.api_keys[api_key]["rate_limit"]
        used = len(self.rate_limits.get(api_key, []))
        
        return max(0, limit - used)

# ====================== خادم API العام ======================
class PublicAPI:
    """واجهة برمجة التطبيقات العامة"""
    
    def __init__(self, market_data, trading_agent, subscription_manager):
        self.market_data = market_data
        self.trading_agent = trading_agent
        self.subscription_manager = subscription_manager
        self.key_manager = APIKeyManager()
        self.app = FastAPI(title="Trading Platform API", version="1.0.0")
        self._setup_routes()
        
    def _setup_routes(self):
        """إعداد مسارات API"""
        
        # أمان API
        api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        
        async def verify_api_key(
            api_key: str = Depends(api_key_header),
            api_secret: str = Header(None, alias="X-API-Secret")
        ) -> str:
            """التحقق من مفتاح API"""
            if not api_key:
                raise HTTPException(status_code=401, detail="مطلوب مفتاح API")
            
            user_id = self.key_manager.verify_api_key(api_key, api_secret)
            if not user_id:
                raise HTTPException(status_code=401, detail="مفتاح API غير صالح")
            
            if not self.key_manager.check_rate_limit(api_key):
                raise HTTPException(status_code=429, detail="تجاوز حد الاستخدام")
            
            return user_id
        
        # ====================== نقاط النهاية العامة ======================
        
        @self.app.get("/")
        async def root():
            """الصفحة الرئيسية للAPI"""
            return {
                "name": "Trading Platform API",
                "version": "1.0.0",
                "documentation": "/docs",
                "endpoints": [
                    "/stock/{symbol}",
                    "/indicators/{symbol}",
                    "/market/opportunities",
                    "/market/snapshot",
                    "/search/{query}",
                    "/webhook/register"
                ]
            }
        
        @self.app.get("/stock/{symbol}", response_model=APIResponse)
        async def get_stock_data(
            symbol: str,
            period: str = "1d",
            user_id: str = Depends(verify_api_key)
        ):
            """جلب بيانات سهم"""
            try:
                # جلب البيانات
                snapshot = await self.market_data.get_stock_snapshot([symbol])
                
                if symbol not in snapshot:
                    raise HTTPException(status_code=404, detail="السهم غير موجود")
                
                stock_data = snapshot[symbol]
                
                # جلب المؤشرات
                indicators = await self.market_data.get_technical_indicators(symbol)
                
                remaining = self.key_manager.get_remaining_requests(
                    self._get_api_key_from_header(user_id)
                )
                
                return APIResponse(
                    success=True,
                    data={
                        "symbol": symbol,
                        "price": stock_data.price,
                        "change": stock_data.change,
                        "change_percent": stock_data.change_percent,
                        "volume": stock_data.volume,
                        "rsi": indicators.rsi if indicators else None,
                        "sma_20": indicators.sma_20 if indicators else None,
                        "sma_50": indicators.sma_50 if indicators else None
                    },
                    timestamp=datetime.now().isoformat(),
                    rate_limit_remaining=remaining
                )
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/indicators/{symbol}", response_model=APIResponse)
        async def get_indicators(
            symbol: str,
            user_id: str = Depends(verify_api_key)
        ):
            """جلب المؤشرات الفنية"""
            try:
                indicators = await self.market_data.get_technical_indicators(symbol)
                
                if not indicators:
                    raise HTTPException(status_code=404, detail="لا توجد مؤشرات")
                
                remaining = self.key_manager.get_remaining_requests(
                    self._get_api_key_from_header(user_id)
                )
                
                return APIResponse(
                    success=True,
                    data={
                        "symbol": symbol,
                        "rsi": indicators.rsi,
                        "macd": indicators.macd,
                        "sma_20": indicators.sma_20,
                        "sma_50": indicators.sma_50,
                        "volume_ratio": indicators.volume_ratio,
                        "bb_upper": indicators.bb_upper,
                        "bb_lower": indicators.bb_lower
                    },
                    timestamp=datetime.now().isoformat(),
                    rate_limit_remaining=remaining
                )
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/market/opportunities", response_model=APIResponse)
        async def get_opportunities(
            limit: int = 10,
            user_id: str = Depends(verify_api_key)
        ):
            """الحصول على فرص الاستثمار"""
            try:
                symbols = ["COMI.CA", "TMGH.CA", "AAPL", "MSFT", "TSLA"]
                opportunities = await self.trading_agent.scan_market(symbols)
                
                result = []
                for opp in opportunities[:limit]:
                    result.append({
                        "symbol": opp.symbol,
                        "name": opp.name,
                        "current_price": opp.current_price,
                        "target_price": opp.target_price,
                        "upside_percent": opp.upside_percent,
                        "action": opp.action,
                        "confidence": opp.confidence,
                        "reasons": opp.reasons
                    })
                
                remaining = self.key_manager.get_remaining_requests(
                    self._get_api_key_from_header(user_id)
                )
                
                return APIResponse(
                    success=True,
                    data={
                        "opportunities": result,
                        "count": len(result)
                    },
                    timestamp=datetime.now().isoformat(),
                    rate_limit_remaining=remaining
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/market/snapshot")
        async def get_market_snapshot(
            symbols: str = "COMI.CA,TMGH.CA,AAPL",
            user_id: str = Depends(verify_api_key)
        ):
            """لمحة سريعة عن السوق"""
            try:
                symbol_list = symbols.split(',')
                snapshot = await self.market_data.get_stock_snapshot(symbol_list)
                
                result = {}
                for symbol, data in snapshot.items():
                    result[symbol] = {
                        "price": data.price,
                        "change_percent": data.change_percent,
                        "volume": data.volume
                    }
                
                return result
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/search/{query}")
        async def search_stocks(
            query: str,
            user_id: str = Depends(verify_api_key)
        ):
            """البحث عن أسهم"""
            try:
                # قائمة الأسهم المتاحة
                stocks_db = {
                    "COMI.CA": "البنك التجاري الدولي",
                    "TMGH.CA": "طلعت مصطفى",
                    "AAPL": "Apple Inc.",
                    "MSFT": "Microsoft Corp.",
                    "TSLA": "Tesla Inc.",
                    "2222.SR": "أرامكو السعودية"
                }
                
                results = []
                query_lower = query.lower()
                
                for symbol, name in stocks_db.items():
                    if query_lower in symbol.lower() or query_lower in name.lower():
                        results.append({
                            "symbol": symbol,
                            "name": name
                        })
                
                return {
                    "query": query,
                    "results": results,
                    "count": len(results)
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/webhook/register")
        async def register_webhook(
            url: str,
            events: List[str],
            user_id: str = Depends(verify_api_key)
        ):
            """تسجيل Webhook للتطبيقات الخارجية"""
            try:
                # تخزين الـ webhook
                webhook_id = secrets.token_urlsafe(16)
                
                # يمكن تخزين في قاعدة البيانات
                
                return {
                    "success": True,
                    "webhook_id": webhook_id,
                    "message": "تم تسجيل webhook بنجاح"
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/webhook/test")
        async def test_webhook(
            payload: WebhookPayload,
            user_id: str = Depends(verify_api_key)
        ):
            """اختبار webhook"""
            return {
                "received": True,
                "payload": payload.dict()
            }
        
        @self.app.get("/rate-limit")
        async def get_rate_limit(
            user_id: str = Depends(verify_api_key)
        ):
            """الحصول على معلومات حد الاستخدام"""
            api_key = self._get_api_key_from_header(user_id)
            remaining = self.key_manager.get_remaining_requests(api_key)
            
            if api_key in self.key_manager.api_keys:
                limit = self.key_manager.api_keys[api_key]["rate_limit"]
                used = limit - remaining
                
                return {
                    "limit": limit,
                    "used": used,
                    "remaining": remaining,
                    "reset_in_seconds": 60
                }
            
            return {"error": "مفتاح غير صالح"}
    
    def _get_api_key_from_header(self, user_id: str) -> str:
        """استخراج مفتاح API من الطلب"""
        # يمكن تنفيذ منطق استخراج المفتاح
        return ""
    
    def get_app(self) -> FastAPI:
        """الحصول على تطبيق FastAPI"""
        return self.app
