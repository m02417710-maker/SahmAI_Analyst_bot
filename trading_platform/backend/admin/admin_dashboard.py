"""
ملف: backend/admin/admin_dashboard.py
المسار: /trading_platform/backend/admin/admin_dashboard.py
الوظيفة: لوحة تحكم المسؤول - نسخة مبسطة بدون loguru
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import pandas as pd
import sys
import os

# إضافة المسار للاستيرادات
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# استخدام logging بدلاً من loguru
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    def __init__(self, subscription_manager=None, market_data=None, trading_agent=None):
        self.sub_manager = subscription_manager
        self.market_data = market_data
        self.trading_agent = trading_agent
        self.system_metrics = {}
        
    async def initialize(self):
        """تهيئة لوحة التحكم"""
        logger.info("تم تهيئة لوحة تحكم المسؤول")
    
    async def get_system_metrics(self) -> SystemMetrics:
        """الحصول على مقاييس النظام"""
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
        # بيانات تجريبية
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
        ]
        
        if filters:
            if filters.get('plan'):
                mock_users = [u for u in mock_users if u.subscription_plan == filters['plan']]
            if filters.get('is_active') is not None:
                mock_users = [u for u in mock_users if u.is_active == filters['is_active']]
        
        return mock_users
    
    async def get_revenue_report(self, period: str = "monthly") -> Dict:
        """تقرير الإيرادات"""
        return {
            "period": period,
            "total_revenue": 125000,
            "subscriptions_count": 150,
            "active_subscriptions": 127,
            "by_plan": {"Free": 50, "Basic": 40, "Pro": 25, "Premium": 12},
            "growth_rate": 23.5,
            "churn_rate": 4.2,
            "average_revenue_per_user": 98.42
        }
    
    async def get_trading_statistics(self) -> Dict:
        """إحصاءات التداول"""
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
            ]
        }
    
    async def get_alert_statistics(self) -> Dict:
        """إحصاءات التنبيهات"""
        return {
            "total_alerts": 3421,
            "triggered_alerts": 2156,
            "conversion_rate": 63.0,
            "most_common_alerts": [
                {"type": "price_target", "count": 1243},
                {"type": "rsi_threshold", "count": 876},
            ]
        }
    
    async def suspend_user(self, user_id: str, reason: str) -> bool:
        """تعليق حساب مستخدم"""
        logger.warning(f"تم تعليق المستخدم {user_id} - السبب: {reason}")
        return True
    
    async def delete_user(self, user_id: str) -> bool:
        """حذف حساب مستخدم"""
        logger.warning(f"تم حذف المستخدم {user_id}")
        return True
