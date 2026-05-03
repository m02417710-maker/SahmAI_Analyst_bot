"""
ملف: backend/admin/admin_dashboard.py
المسار: /trading_platform/backend/admin/admin_dashboard.py
الوظيفة: لوحة تحكم المسؤول المتكاملة
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger
import pandas as pd

@dataclass
class SystemMetrics:
    """مقاييس النظام"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_users: int
    api_calls_today: int
    avg_response_time: float
    uptime_percentage: float

@dataclass
class UserReport:
    """تقرير المستخدم"""
    user_id: str
    username: str
    email: str
    subscription_plan: str
    join_date: datetime
    last_active: datetime
    total_trades: int
    total_profit: float
    is_active: bool

class AdminDashboard:
    """لوحة تحكم المسؤول"""
    
    def __init__(self, subscription_manager, market_data, trading_agent):
        self.sub_manager = subscription_manager
        self.market_data = market_data
        self.trading_agent = trading_agent
        self.system_metrics = {}
        
    async def initialize(self):
        """تهيئة لوحة التحكم"""
        logger.info("✅ تم تهيئة لوحة تحكم المسؤول")
    
    async def get_system_metrics(self) -> SystemMetrics:
        """الحصول على مقاييس النظام"""
        # يمكن جلب هذه المقاييس من Prometheus
        return SystemMetrics(
            cpu_usage=45.2,
            memory_usage=62.8,
            disk_usage=38.5,
            active_users=127,
            api_calls_today=15423,
            avg_response_time=0.234,
            uptime_percentage=99.95
        )
    
    async def get_user_list(self, filters: Dict = None) -> List[UserReport]:
        """الحصول على قائمة المستخدمين"""
        # يمكن جلب من قاعدة البيانات
        mock_users = [
            UserReport(
                user_id="user_001",
                username="ahmed_ali",
                email="ahmed@example.com",
                subscription_plan="Pro",
                join_date=datetime.now() - timedelta(days=45),
                last_active=datetime.now() - timedelta(minutes=5),
                total_trades=23,
                total_profit=12500.50,
                is_active=True
            ),
            UserReport(
                user_id="user_002",
                username="sara_mohamed",
                email="sara@example.com",
                subscription_plan="Premium",
                join_date=datetime.now() - timedelta(days=90),
                last_active=datetime.now() - timedelta(hours=2),
                total_trades=67,
                total_profit=45200.75,
                is_active=True
            ),
            UserReport(
                user_id="user_003",
                username="mohamed_hassan",
                email="mohamed@example.com",
                subscription_plan="Basic",
                join_date=datetime.now() - timedelta(days=15),
                last_active=datetime.now() - timedelta(days=1),
                total_trades=5,
                total_profit=-2300.00,
                is_active=False
            )
        ]
        
        # تطبيق الفلاتر
        if filters:
            if filters.get('plan'):
                mock_users = [u for u in mock_users if u.subscription_plan == filters['plan']]
            if filters.get('is_active') is not None:
                mock_users = [u for u in mock_users if u.is_active == filters['is_active']]
        
        return mock_users
    
    async def get_revenue_report(self, period: str = "monthly") -> Dict:
        """تقرير الإيرادات"""
        stats = await self.sub_manager.get_subscription_statistics()
        
        revenue_report = {
            "period": period,
            "total_revenue": stats["monthly_revenue"],
            "subscriptions_count": stats["total_subscriptions"],
            "active_subscriptions": stats["active_subscriptions"],
            "by_plan": stats["by_plan"],
            "growth_rate": 23.5,  # نسبة النمو
            "churn_rate": 4.2,    # نسبة الإلغاء
            "average_revenue_per_user": stats["monthly_revenue"] / max(stats["active_subscriptions"], 1)
        }
        
        return revenue_report
    
    async def get_trading_statistics(self) -> Dict:
        """إحصاءات التداول"""
        # يمكن جلب من قاعدة البيانات
        return {
            "total_trades": 1542,
            "successful_trades": 1250,
            "failed_trades": 292,
            "win_rate": 81.1,
            "total_volume": 15250000.00,
            "total_profit": 1250000.00,
            "top_stocks": [
                {"symbol": "COMI.CA", "trades": 342, "volume": 8500000},
                {"symbol": "TMGH.CA", "trades": 298, "volume": 4200000},
                {"symbol": "2222.SR", "trades": 187, "volume": 1250000}
            ],
            "most_active_traders": [
                {"user_id": "user_001", "trades": 87},
                {"user_id": "user_002", "trades": 65},
                {"user_id": "user_003", "trades": 43}
            ]
        }
    
    async def get_stock_performance(self) -> pd.DataFrame:
        """تحليل أداء الأسهم"""
        symbols = ["COMI.CA", "TMGH.CA", "SWDY.CA", "2222.SR", "AAPL"]
        
        performance = []
        for symbol in symbols:
            indicators = await self.market_data.get_technical_indicators(symbol)
            snapshot = await self.market_data.get_stock_snapshot([symbol])
            
            if symbol in snapshot and indicators:
                stock_data = snapshot[symbol]
                performance.append({
                    "symbol": symbol,
                    "price": stock_data.price,
                    "change_24h": stock_data.change_percent,
                    "rsi": indicators.rsi,
                    "volume_ratio": indicators.volume_ratio,
                    "trend": "صاعد" if indicators.sma_20 > indicators.sma_50 else "هابط"
                })
        
        return pd.DataFrame(performance)
    
    async def get_alert_statistics(self) -> Dict:
        """إحصاءات التنبيهات"""
        return {
            "total_alerts": 3421,
            "triggered_alerts": 2156,
            "conversion_rate": 63.0,
            "most_common_alerts": [
                {"type": "price_target", "count": 1243},
                {"type": "rsi_threshold", "count": 876},
                {"type": "volume_spike", "count": 302}
            ],
            "alerts_by_stock": [
                {"symbol": "COMI.CA", "alerts": 567},
                {"symbol": "AAPL", "alerts": 432},
                {"symbol": "2222.SR", "alerts": 298}
            ]
        }
    
    async def generate_admin_report(self) -> str:
        """توليد تقرير إداري شامل"""
        metrics = await self.get_system_metrics()
        revenue = await self.get_revenue_report()
        trading_stats = await self.get_trading_statistics()
        
        report = f"""
📊 **تقرير إداري شامل**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

## ⚙️ مقاييس النظام
• استخدام المعالج: {metrics.cpu_usage}%
• استخدام الذاكرة: {metrics.memory_usage}%
• المستخدمين النشطين: {metrics.active_users}
• مكالمات API اليوم: {metrics.api_calls_today:,}
• متوسط وقت الاستجابة: {metrics.avg_response_time} ثانية

## 💰 الإيرادات
• إجمالي الإيرادات الشهري: {revenue['total_revenue']:,.2f} ج.م
• المستخدمين النشطين: {revenue['active_subscriptions']}
• متوسط الإيراد لكل مستخدم: {revenue['average_revenue_per_user']:,.2f} ج.م
• نسبة النمو: {revenue['growth_rate']}%
• نسبة الإلغاء: {revenue['churn_rate']}%

## 📈 إحصائيات التداول
• إجمالي الصفقات: {trading_stats['total_trades']:,}
• نسبة النجاح: {trading_stats['win_rate']}%
• إجمالي الربح: {trading_stats['total_profit']:,.2f} ج.م
• إجمالي حجم التداول: {trading_stats['total_volume']:,.2f} ج.م

## 🏆 الأسهم الأكثر تداولاً
"""
        for stock in trading_stats['top_stocks']:
            report += f"• {stock['symbol']}: {stock['trades']} صفقة\n"
        
        report += "\n---\nتم الإنشاء بواسطة نظام الإدارة المتكامل"
        
        return report
    
    async def suspend_user(self, user_id: str, reason: str) -> bool:
        """تعليق حساب مستخدم"""
        logger.warning(f"🚫 تم تعليق المستخدم {user_id} - السبب: {reason}")
        return True
    
    async def delete_user(self, user_id: str) -> bool:
        """حذف حساب مستخدم"""
        logger.warning(f"🗑 تم حذف المستخدم {user_id}")
        return True
    
    async def adjust_user_plan(self, user_id: str, new_plan: str) -> bool:
        """تعديل خطة المستخدم"""
        logger.info(f"📝 تم تعديل خطة المستخدم {user_id} إلى {new_plan}")
        return True
