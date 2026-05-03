"""
ملف: backend/main.py
المسار: /trading_platform/backend/main.py
الوظيفة: خادم API الرئيسي - نقطة الدخول للخدمات
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager
from loguru import logger
import sys

# إعداد التسجيل
logger.add(
    "logs/trading_api_{time}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO"
)

# استيراد المكونات الداخلية
from api.market_data import MarketDataManager
from agents.trading_agent import TradingAgent
from agents.sentiment_agent import SentimentAgent
from database.timescale_manager import TimescaleManager
from database.redis_manager import RedisManager

# ====================== نماذج البيانات ======================
class StockAnalysisRequest(BaseModel):
    symbol: str
    period: str = "1y"

class AlertCreate(BaseModel):
    symbol: str
    target_price: float
    user_id: str

class PortfolioAdd(BaseModel):
    symbol: str
    quantity: int
    buy_price: float

# ====================== تهيئة التطبيق ======================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """إدارة دورة حياة التطبيق"""
    logger.info("🚀 بدء تشغيل منصة التحليل الاستثماري...")
    
    # تهيئة المديرين
    app.state.market_data = MarketDataManager()
    await app.state.market_data.initialize()
    
    app.state.trading_agent = TradingAgent(app.state.market_data)
    await app.state.trading_agent.initialize()
    
    app.state.sentiment_agent = SentimentAgent()
    await app.state.sentiment_agent.initialize()
    
    app.state.db_manager = TimescaleManager()
    await app.state.db_manager.initialize()
    
    app.state.redis_manager = RedisManager()
    await app.state.redis_manager.initialize()
    
    # بدء المهام الخلفية
    asyncio.create_task(update_market_data_background())
    
    logger.info("✅ تم تشغيل جميع الخدمات بنجاح")
    
    yield
    
    # إغلاق الاتصالات
    logger.info("🛑 إغلاق التطبيق...")
    await app.state.redis_manager.close()
    await app.state.db_manager.close()

# إنشاء تطبيق FastAPI
app = FastAPI(
    title="Trading Platform API",
    description="منصة تحليل وتداول الأسهم بالذكاء الاصطناعي",
    version="3.0.0",
    lifespan=lifespan
)

# إضافة CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== المهام الخلفية ======================
async def update_market_data_background():
    """تحديث بيانات السوق في الخلفية كل دقيقة"""
    while True:
        try:
            # تحديث بيانات الأسهم الرئيسية
            symbols = ["COMI.CA", "TMGH.CA", "2222.SR", "AAPL", "MSFT"]
            snapshot = await app.state.market_data.get_stock_snapshot(symbols)
            
            # تخزين في Redis
            await app.state.redis_manager.store_market_snapshot(snapshot)
            
            # تخزين في TimescaleDB
            for symbol, data in snapshot.items():
                await app.state.db_manager.insert_stock_data(data)
            
            logger.info(f"✅ تحديث بيانات السوق - {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"خطأ في تحديث البيانات: {e}")
        
        await asyncio.sleep(60)  # تحديث كل دقيقة

# ====================== نقاط النهاية (Endpoints) ======================

@app.get("/")
async def root():
    """الصفحة الرئيسية للAPI"""
    return {
        "name": "Trading Platform API",
        "version": "3.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "stock": "/api/stock/{symbol}",
            "indicators": "/api/indicators/{symbol}",
            "opportunities": "/api/market/opportunities",
            "report": "/api/report/daily",
            "search": "/api/search/{query}"
        }
    }

@app.get("/api/stock/{symbol}")
async def get_stock_data(symbol: str):
    """جلب بيانات السهم"""
    try:
        snapshot = await app.state.market_data.get_stock_snapshot([symbol])
        
        if symbol not in snapshot:
            raise HTTPException(status_code=404, detail=f"السهم {symbol} غير موجود")
        
        stock_data = snapshot[symbol]
        
        # جلب الرسم البياني
        chart_data = await app.state.market_data.get_chart_data(symbol)
        
        return {
            "symbol": stock_data.symbol,
            "price": stock_data.price,
            "change": stock_data.change,
            "change_percent": stock_data.change_percent,
            "volume": stock_data.volume,
            "high_52w": stock_data.high_52w,
            "low_52w": stock_data.low_52w,
            "timestamp": stock_data.timestamp.isoformat(),
            "chart_data": chart_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطأ في جلب بيانات {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/indicators/{symbol}")
async def get_technical_indicators(symbol: str):
    """جلب المؤشرات الفنية"""
    try:
        indicators = await app.state.market_data.get_technical_indicators(symbol)
        
        if not indicators:
            raise HTTPException(status_code=404, detail=f"لا توجد مؤشرات لـ {symbol}")
        
        return {
            "symbol": symbol,
            "rsi": indicators.rsi,
            "macd": indicators.macd,
            "macd_signal": indicators.macd_signal,
            "sma_20": indicators.sma_20,
            "sma_50": indicators.sma_50,
            "bb_upper": indicators.bb_upper,
            "bb_lower": indicators.bb_lower,
            "volume_ratio": indicators.volume_ratio,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطأ في مؤشرات {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market/opportunities")
async def get_market_opportunities(limit: int = 10):
    """الحصول على فرص الاستثمار"""
    try:
        symbols = ["COMI.CA", "TMGH.CA", "SWDY.CA", "EAST.CA", 
                   "2222.SR", "1120.SR", "AAPL", "MSFT", "TSLA", "GOOGL"]
        
        opportunities = await app.state.trading_agent.scan_market(symbols)
        
        # تحويل إلى قاموس لـ JSON
        result = []
        for opp in opportunities[:limit]:
            result.append({
                "symbol": opp.symbol,
                "name": opp.name,
                "current_price": opp.current_price,
                "target_price": opp.target_price,
                "upside_percent": opp.upside_percent,
                "confidence": opp.confidence,
                "action": opp.action,
                "risk_level": opp.risk_level,
                "time_frame": opp.time_frame,
                "reasons": opp.reasons,
                "indicators": opp.indicators
            })
        
        return {
            "opportunities": result,
            "count": len(result),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"خطأ في جلب الفرص: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/report/daily")
async def get_daily_report():
    """توليد تقرير يومي"""
    try:
        report = await app.state.trading_agent.generate_daily_report()
        
        return {
            "report": report,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"خطأ في توليد التقرير: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/{query}")
async def search_stocks(query: str):
    """البحث عن الأسهم"""
    try:
        # قائمة الأسهم المتاحة
        stocks_db = {
            "COMI.CA": {"name": "البنك التجاري الدولي", "market": "EGX"},
            "TMGH.CA": {"name": "طلعت مصطفى القابضة", "market": "EGX"},
            "SWDY.CA": {"name": "السويدي إليكتريك", "market": "EGX"},
            "2222.SR": {"name": "أرامكو السعودية", "market": "TADAWUL"},
            "1120.SR": {"name": "مصرف الراجحي", "market": "TADAWUL"},
            "AAPL": {"name": "Apple Inc.", "market": "NASDAQ"},
            "MSFT": {"name": "Microsoft Corp.", "market": "NASDAQ"},
            "TSLA": {"name": "Tesla Inc.", "market": "NASDAQ"},
            "GOOGL": {"name": "Alphabet Inc.", "market": "NASDAQ"},
        }
        
        # بحث في الرموز والأسماء
        results = []
        query_lower = query.lower()
        
        for symbol, info in stocks_db.items():
            if (query_lower in symbol.lower() or 
                query_lower in info['name'].lower()):
                results.append({
                    "symbol": symbol,
                    "name": info['name'],
                    "market": info['market']
                })
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"خطأ في البحث: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/alerts")
async def create_alert(alert: AlertCreate):
    """إنشاء تنبيه جديد"""
    try:
        # تخزين في Redis
        alert_key = f"alert:{alert.user_id}:{alert.symbol}"
        await app.state.redis_manager.set(
            alert_key,
            alert.target_price,
            expiry=86400 * 30  # 30 يوم
        )
        
        return {
            "status": "success",
            "message": f"تم إنشاء تنبيه لـ {alert.symbol} عند {alert.target_price}",
            "alert": alert
        }
    except Exception as e:
        logger.error(f"خطأ في إنشاء التنبيه: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts/{user_id}")
async def get_user_alerts(user_id: str):
    """جلب تنبيهات المستخدم"""
    try:
        pattern = f"alert:{user_id}:*"
        keys = await app.state.redis_manager.keys(pattern)
        
        alerts = []
        for key in keys:
            value = await app.state.redis_manager.get(key)
            symbol = key.split(":")[-1]
            alerts.append({
                "symbol": symbol,
                "target_price": float(value) if value else 0
            })
        
        return {
            "user_id": user_id,
            "alerts": alerts,
            "count": len(alerts)
        }
    except Exception as e:
        logger.error(f"خطأ في جلب التنبيهات: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/{user_id}")
async def add_to_portfolio(user_id: str, portfolio: PortfolioAdd):
    """إضافة سهم للمحفظة"""
    try:
        portfolio_key = f"portfolio:{user_id}:{portfolio.symbol}"
        
        await app.state.redis_manager.hset(portfolio_key, {
            "quantity": portfolio.quantity,
            "buy_price": portfolio.buy_price,
            "added_date": datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "message": f"تم إضافة {portfolio.symbol} للمحفظة",
            "portfolio": portfolio
        }
    except Exception as e:
        logger.error(f"خطأ في إضافة للمحفظة: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/{user_id}")
async def get_portfolio(user_id: str):
    """جلب محفظة المستخدم"""
    try:
        pattern = f"portfolio:{user_id}:*"
        keys = await app.state.redis_manager.keys(pattern)
        
        portfolio = []
        total_value = 0
        total_profit = 0
        
        for key in keys:
            data = await app.state.redis_manager.hgetall(key)
            symbol = key.split(":")[-1]
            
            # جلب السعر الحالي
            snapshot = await app.state.market_data.get_stock_snapshot([symbol])
            current_price = snapshot[symbol].price if symbol in snapshot else data.get('buy_price', 0)
            
            quantity = int(data.get('quantity', 1))
            buy_price = float(data.get('buy_price', 0))
            
            value = current_price * quantity
            cost = buy_price * quantity
            profit = value - cost
            profit_percent = (profit / cost) * 100 if cost > 0 else 0
            
            total_value += value
            total_profit += profit
            
            portfolio.append({
                "symbol": symbol,
                "quantity": quantity,
                "buy_price": buy_price,
                "current_price": current_price,
                "value": value,
                "profit": profit,
                "profit_percent": profit_percent,
                "added_date": data.get('added_date')
            })
        
        return {
            "user_id": user_id,
            "portfolio": portfolio,
            "total_value": total_value,
            "total_profit": total_profit,
            "total_profit_percent": (total_profit / (total_value - total_profit)) * 100 if total_value > total_profit else 0
        }
    except Exception as e:
        logger.error(f"خطأ في جلب المحفظة: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ====================== صحة الخدمات ======================
@app.get("/health")
async def health_check():
    """فحص صحة الخدمات"""
    services = {
        "api": "healthy",
        "market_data": "unknown",
        "redis": "unknown",
        "database": "unknown"
    }
    
    try:
        # فحص Redis
        await app.state.redis_manager.ping()
        services["redis"] = "healthy"
    except:
        services["redis"] = "unhealthy"
    
    try:
        # فحص قاعدة البيانات
        await app.state.db_manager.ping()
        services["database"] = "healthy"
    except:
        services["database"] = "unhealthy"
    
    try:
        # فحص بيانات السوق
        await app.state.market_data.get_stock_snapshot(["AAPL"])
        services["market_data"] = "healthy"
    except:
        services["market_data"] = "degraded"
    
    all_healthy = all(s == "healthy" for s in services.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services,
        "timestamp": datetime.now().isoformat()
    }

# ====================== التشغيل ======================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
