"""
ملف: backend/copy_trading/copy_trader.py
المسار: /trading_platform/backend/copy_trading/copy_trader.py
الوظيفة: نظام نسخ الصفقات من المتداولين المحترفين
"""

import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

class TraderLevel(Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"

@dataclass
class MasterTrader:
    """متداول محترف يمكن النسخ منه"""
    id: str
    username: str
    level: TraderLevel
    followers_count: int
    total_pnl: float
    win_rate: float
    avg_return: float
    max_drawdown: float
    total_trades: int
    monthly_performance: List[float]
    is_active: bool = True
    fee_percentage: float = 0.0

@dataclass
class CopiedTrade:
    """صفقة منسوخة"""
    id: str
    master_trader_id: str
    follower_id: str
    original_trade_id: str
    symbol: str
    action: str
    quantity: int
    price: float
    copy_ratio: float
    timestamp: datetime
    status: str = "pending"

@dataclass
class Follower:
    """مستخدم ينسخ الصفقات"""
    id: str
    username: str
    master_traders: List[str]
    total_invested: float
    total_profit: float
    copy_ratio: float = 1.0  # 1.0 = نفس الحجم
    auto_copy: bool = True
    max_risk_per_trade: float = 5.0  # نسبة المخاطرة القصوى

class CopyTradingSystem:
    """نظام نسخ الصفقات"""
    
    def __init__(self, broker_connector, subscription_manager):
        self.broker = broker_connector
        self.subscription_manager = subscription_manager
        self.master_traders: Dict[str, MasterTrader] = {}
        self.followers: Dict[str, Follower] = {}
        self.copied_trades: List[CopiedTrade] = []
        self.is_running = False
        
    async def initialize(self):
        """تهيئة النظام"""
        await self._load_master_traders()
        await self._load_followers()
        logger.info("✅ تم تهيئة نظام نسخ الصفقات")
    
    async def register_master_trader(self, trader: MasterTrader) -> bool:
        """تسجيل متداول محترف"""
        try:
            self.master_traders[trader.id] = trader
            await self._save_master_trader(trader)
            logger.info(f"✅ تم تسجيل المتداول المحترف {trader.username}")
            return True
        except Exception as e:
            logger.error(f"خطأ في تسجيل المتداول: {e}")
            return False
    
    async def follow_master(self, follower_id: str, master_id: str) -> bool:
        """بدء متابعة متداول محترف"""
        try:
            if master_id not in self.master_traders:
                logger.warning(f"المتداول {master_id} غير موجود")
                return False
            
            if follower_id not in self.followers:
                self.followers[follower_id] = Follower(
                    id=follower_id,
                    username=f"user_{follower_id}",
                    master_traders=[],
                    total_invested=0,
                    total_profit=0
                )
            
            if master_id not in self.followers[follower_id].master_traders:
                self.followers[follower_id].master_traders.append(master_id)
                self.master_traders[master_id].followers_count += 1
                
                await self._save_follower(self.followers[follower_id])
                logger.info(f"✅ المستخدم {follower_id} يتابع الآن {self.master_traders[master_id].username}")
            
            return True
            
        except Exception as e:
            logger.error(f"خطأ في متابعة المتداول: {e}")
            return False
    
    async def unfollow_master(self, follower_id: str, master_id: str) -> bool:
        """إلغاء متابعة متداول"""
        try:
            if follower_id in self.followers and master_id in self.followers[follower_id].master_traders:
                self.followers[follower_id].master_traders.remove(master_id)
                self.master_traders[master_id].followers_count -= 1
                
                logger.info(f"✅ المستخدم {follower_id} توقف عن متابعة {self.master_traders[master_id].username}")
            
            return True
        except Exception as e:
            logger.error(f"خطأ في إلغاء المتابعة: {e}")
            return False
    
    async def start_copying(self):
        """بدء نظام نسخ الصفقات"""
        self.is_running = True
        asyncio.create_task(self._monitor_master_trades())
        logger.info("🚀 بدء تشغيل نظام نسخ الصفقات")
    
    async def stop_copying(self):
        """إيقاف نظام نسخ الصفقات"""
        self.is_running = False
        logger.info("🛑 إيقاف نظام نسخ الصفقات")
    
    async def _monitor_master_trades(self):
        """مراقبة صفقات المتداولين المحترفين"""
        while self.is_running:
            try:
                for master_id, master in self.master_traders.items():
                    if master.is_active:
                        # جلب الصفقات الجديدة للمتداول
                        new_trades = await self._get_master_new_trades(master_id)
                        
                        for trade in new_trades:
                            # نسخ الصفقة لكل المتابعين
                            await self._copy_trade_to_followers(master_id, trade)
                
                await asyncio.sleep(5)  # فحص كل 5 ثواني
                
            except Exception as e:
                logger.error(f"خطأ في مراقبة الصفقات: {e}")
                await asyncio.sleep(10)
    
    async def _copy_trade_to_followers(self, master_id: str, trade: Dict):
        """نسخ صفقة إلى المتابعين"""
        try:
            # العثور على جميع متابعي هذا المتداول
            followers = [
                f for f in self.followers.values() 
                if master_id in f.master_traders and f.auto_copy
            ]
            
            for follower in followers:
                # التحقق من صلاحية الاشتراك
                subscription = await self.subscription_manager.get_user_subscription(follower.id)
                if not subscription or subscription.plan.type.value not in ["pro", "premium", "enterprise"]:
                    logger.warning(f"المستخدم {follower.id} لا يملك صلاحية نسخ الصفقات")
                    continue
                
                # حساب الكمية المناسبة
                copy_quantity = int(trade['quantity'] * follower.copy_ratio)
                
                # التحقق من حد المخاطرة
                account = await self.broker.get_account_summary()
                if account:
                    trade_value = copy_quantity * trade['price']
                    risk_percent = (trade_value / account.total_value) * 100
                    
                    if risk_percent > follower.max_risk_per_trade:
                        logger.warning(f"تجاوز حد المخاطرة للمستخدم {follower.id}")
                        continue
                
                # تنفيذ الأمر المنسوخ
                copied_trade = CopiedTrade(
                    id=self._generate_trade_id(),
                    master_trader_id=master_id,
                    follower_id=follower.id,
                    original_trade_id=trade['id'],
                    symbol=trade['symbol'],
                    action=trade['action'],
                    quantity=copy_quantity,
                    price=trade['price'],
                    copy_ratio=follower.copy_ratio,
                    timestamp=datetime.now(),
                    status="executed"
                )
                
                # تنفيذ الأمر عبر الوسيط
                order = await self.broker.execute_strategy_order({
                    'symbol': trade['symbol'],
                    'action': trade['action'],
                    'quantity': copy_quantity,
                    'order_type': 'MARKET'
                })
                
                if order:
                    self.copied_trades.append(copied_trade)
                    logger.info(f"✅ تم نسخ صفقة {trade['symbol']} للمستخدم {follower.id}")
                    
                    # تحديث إحصائيات التابع
                    if trade['action'] == 'BUY':
                        follower.total_invested += copy_quantity * trade['price']
                
        except Exception as e:
            logger.error(f"خطأ في نسخ الصفقة: {e}")
    
    async def get_top_traders(self, limit: int = 10) -> List[MasterTrader]:
        """الحصول على أفضل المتداولين"""
        sorted_traders = sorted(
            self.master_traders.values(),
            key=lambda x: x.total_pnl,
            reverse=True
        )
        return sorted_traders[:limit]
    
    async def get_follower_performance(self, follower_id: str) -> Dict:
        """الحصول على أداء التابع"""
        follower = self.followers.get(follower_id)
        if not follower:
            return {}
        
        follower_trades = [t for t in self.copied_trades if t.follower_id == follower_id]
        
        total_profit = 0
        winning_trades = 0
        
        for trade in follower_trades:
            # حساب الربح/الخسارة (مبسط)
            profit = trade.quantity * (await self._get_current_price(trade.symbol) - trade.price)
            total_profit += profit
            if profit > 0:
                winning_trades += 1
        
        win_rate = (winning_trades / len(follower_trades)) * 100 if follower_trades else 0
        
        return {
            "follower_id": follower_id,
            "username": follower.username,
            "master_traders": follower.master_traders,
            "total_invested": follower.total_invested,
            "total_profit": total_profit,
            "return_percentage": (total_profit / follower.total_invested) * 100 if follower.total_invested > 0 else 0,
            "total_trades": len(follower_trades),
            "win_rate": win_rate,
            "copied_trades": [
                {
                    "symbol": t.symbol,
                    "action": t.action,
                    "quantity": t.quantity,
                    "price": t.price,
                    "timestamp": t.timestamp.isoformat()
                }
                for t in follower_trades[-20:]  # آخر 20 صفقة
            ]
        }
    
    async def _get_master_new_trades(self, master_id: str) -> List[Dict]:
        """جلب الصفقات الجديدة للمتداول"""
        # يمكن جلب من WebSocket أو قاعدة البيانات
        # حالياً بيانات تجريبية
        return []
    
    async def _get_current_price(self, symbol: str) -> float:
        """الحصول على السعر الحالي"""
        # يمكن جلب من market_data
        return 100.0
    
    def _generate_trade_id(self) -> str:
        """توليد معرف فريد للصفقة"""
        return f"CT_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    async def _save_master_trader(self, trader: MasterTrader):
        """حفظ بيانات المتداول"""
        pass
    
    async def _save_follower(self, follower: Follower):
        """حفظ بيانات التابع"""
        pass
    
    async def _load_master_traders(self):
        """تحميل بيانات المتداولين"""
        # بيانات تجريبية
        mock_masters = [
            MasterTrader(
                id="master_001",
                username="محمد_العربي",
                level=TraderLevel.DIAMOND,
                followers_count=1542,
                total_pnl=1250000,
                win_rate=78.5,
                avg_return=15.2,
                max_drawdown=12.3,
                total_trades=234,
                monthly_performance=[5.2, 8.1, 12.4, 15.8, 18.2, 22.1],
                fee_percentage=10
            ),
            MasterTrader(
                id="master_002",
                username="سارة_الغامدي",
                level=TraderLevel.GOLD,
                followers_count=892,
                total_pnl=850000,
                win_rate=72.3,
                avg_return=12.8,
                max_drawdown=15.6,
                total_trades=187,
                monthly_performance=[3.1, 5.2, 8.5, 11.2, 14.5, 16.8],
                fee_percentage=8
            )
        ]
        
        for master in mock_masters:
            self.master_traders[master.id] = master
    
    async def _load_followers(self):
        """تحميل بيانات التابعين"""
        pass
