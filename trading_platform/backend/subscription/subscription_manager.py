"""
ملف: backend/subscription/subscription_manager.py
المسار: /trading_platform/backend/subscription/subscription_manager.py
الوظيفة: إدارة الاشتراكات والخطط والباقات
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import stripe
import asyncio
from loguru import logger

class PlanType(Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"

@dataclass
class Plan:
    """نموذج خطة الاشتراك"""
    id: str
    name: str
    type: PlanType
    price_monthly: float
    price_yearly: float
    features: Dict[str, bool]
    limits: Dict[str, int]
    currency: str = "EGP"

@dataclass
class Subscription:
    """نموذج اشتراك المستخدم"""
    id: str
    user_id: str
    plan: Plan
    status: SubscriptionStatus
    start_date: datetime
    end_date: datetime
    auto_renew: bool = True
    payment_method: str = ""
    last_payment_date: Optional[datetime] = None

@dataclass
class PaymentTransaction:
    """نموذج عملية الدفع"""
    id: str
    user_id: str
    amount: float
    currency: str
    status: str
    payment_method: str
    transaction_date: datetime
    subscription_id: str
    receipt_url: str = ""

class SubscriptionManager:
    """مدير الاشتراكات والفواتير"""
    
    def __init__(self, stripe_api_key: str = None):
        self.plans: Dict[PlanType, Plan] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.transactions: Dict[str, PaymentTransaction] = {}
        
        # تهيئة Stripe إذا توفر المفتاح
        if stripe_api_key:
            stripe.api_key = stripe_api_key
            self.stripe_enabled = True
        else:
            self.stripe_enabled = False
        
    async def initialize(self):
        """تهيئة الخطط والخدمات"""
        await self._load_plans()
        await self._load_subscriptions()
        logger.info("✅ تم تهيئة نظام الاشتراكات")
    
    async def _load_plans(self):
        """تحميل خطط الاشتراك"""
        self.plans = {
            PlanType.FREE: Plan(
                id="free_plan",
                name="مجاني",
                type=PlanType.FREE,
                price_monthly=0,
                price_yearly=0,
                features={
                    "stock_analysis": True,
                    "basic_indicators": True,
                    "daily_report": True,
                    "realtime_data": False,
                    "ai_analysis": False,
                    "auto_trading": False,
                    "telegram_bot": False,
                    "portfolio_tracking": False,
                    "alerts": False,
                    "api_access": False
                },
                limits={
                    "max_stocks": 5,
                    "max_alerts": 3,
                    "charts_per_day": 10,
                    "api_calls_per_day": 100
                }
            ),
            PlanType.BASIC: Plan(
                id="basic_plan",
                name="أساسي",
                type=PlanType.BASIC,
                price_monthly=99,
                price_yearly=990,
                features={
                    "stock_analysis": True,
                    "basic_indicators": True,
                    "daily_report": True,
                    "realtime_data": True,
                    "ai_analysis": False,
                    "auto_trading": False,
                    "telegram_bot": True,
                    "portfolio_tracking": True,
                    "alerts": True,
                    "api_access": False
                },
                limits={
                    "max_stocks": 20,
                    "max_alerts": 10,
                    "charts_per_day": 50,
                    "api_calls_per_day": 500
                }
            ),
            PlanType.PRO: Plan(
                id="pro_plan",
                name="احترافي",
                type=PlanType.PRO,
                price_monthly=299,
                price_yearly=2990,
                features={
                    "stock_analysis": True,
                    "basic_indicators": True,
                    "daily_report": True,
                    "realtime_data": True,
                    "ai_analysis": True,
                    "auto_trading": False,
                    "telegram_bot": True,
                    "portfolio_tracking": True,
                    "alerts": True,
                    "api_access": True
                },
                limits={
                    "max_stocks": 100,
                    "max_alerts": 50,
                    "charts_per_day": 500,
                    "api_calls_per_day": 5000
                }
            ),
            PlanType.PREMIUM: Plan(
                id="premium_plan",
                name="بريميوم",
                type=PlanType.PREMIUM,
                price_monthly=599,
                price_yearly=5990,
                features={
                    "stock_analysis": True,
                    "basic_indicators": True,
                    "daily_report": True,
                    "realtime_data": True,
                    "ai_analysis": True,
                    "auto_trading": True,
                    "telegram_bot": True,
                    "portfolio_tracking": True,
                    "alerts": True,
                    "api_access": True
                },
                limits={
                    "max_stocks": 500,
                    "max_alerts": 200,
                    "charts_per_day": 5000,
                    "api_calls_per_day": 50000
                }
            ),
            PlanType.ENTERPRISE: Plan(
                id="enterprise_plan",
                name="مؤسسات",
                type=PlanType.ENTERPRISE,
                price_monthly=1499,
                price_yearly=14990,
                features={
                    "stock_analysis": True,
                    "basic_indicators": True,
                    "daily_report": True,
                    "realtime_data": True,
                    "ai_analysis": True,
                    "auto_trading": True,
                    "telegram_bot": True,
                    "portfolio_tracking": True,
                    "alerts": True,
                    "api_access": True
                },
                limits={
                    "max_stocks": 9999,
                    "max_alerts": 999,
                    "charts_per_day": 99999,
                    "api_calls_per_day": 999999
                }
            )
        }
    
    async def create_subscription(
        self,
        user_id: str,
        plan_type: PlanType,
        payment_method: str,
        auto_renew: bool = True
    ) -> Tuple[Subscription, bool]:
        """إنشاء اشتراك جديد"""
        try:
            plan = self.plans.get(plan_type)
            if not plan:
                return None, False
            
            # معالجة الدفع
            if self.stripe_enabled:
                payment_success = await self._process_stripe_payment(user_id, plan.price_monthly)
            else:
                # محاكاة الدفع للتجربة
                payment_success = True
            
            if not payment_success:
                return None, False
            
            # إنشاء الاشتراك
            subscription = Subscription(
                id=self._generate_subscription_id(),
                user_id=user_id,
                plan=plan,
                status=SubscriptionStatus.ACTIVE,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                auto_renew=auto_renew,
                payment_method=payment_method,
                last_payment_date=datetime.now()
            )
            
            self.subscriptions[subscription.id] = subscription
            
            # تسجيل المعاملة
            await self._record_transaction(
                user_id=user_id,
                amount=plan.price_monthly,
                subscription_id=subscription.id,
                status="success"
            )
            
            logger.info(f"✅ تم إنشاء اشتراك {plan.name} للمستخدم {user_id}")
            return subscription, True
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء الاشتراك: {e}")
            return None, False
    
    async def cancel_subscription(self, subscription_id: str) -> bool:
        """إلغاء الاشتراك"""
        try:
            if subscription_id not in self.subscriptions:
                return False
            
            subscription = self.subscriptions[subscription_id]
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.auto_renew = False
            
            logger.info(f"✅ تم إلغاء اشتراك {subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في إلغاء الاشتراك: {e}")
            return False
    
    async def renew_subscription(self, subscription_id: str) -> bool:
        """تجديد الاشتراك"""
        try:
            if subscription_id not in self.subscriptions:
                return False
            
            subscription = self.subscriptions[subscription_id]
            
            if not subscription.auto_renew:
                return False
            
            # معالجة الدفع للتجديد
            if self.stripe_enabled:
                payment_success = await self._process_stripe_payment(
                    subscription.user_id,
                    subscription.plan.price_monthly
                )
            else:
                payment_success = True
            
            if payment_success:
                subscription.end_date = datetime.now() + timedelta(days=30)
                subscription.last_payment_date = datetime.now()
                subscription.status = SubscriptionStatus.ACTIVE
                
                # تسجيل المعاملة
                await self._record_transaction(
                    user_id=subscription.user_id,
                    amount=subscription.plan.price_monthly,
                    subscription_id=subscription_id,
                    status="renewal"
                )
                
                logger.info(f"✅ تم تجديد اشتراك {subscription_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"خطأ في تجديد الاشتراك: {e}")
            return False
    
    async def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """الحصول على اشتراك المستخدم"""
        for sub in self.subscriptions.values():
            if sub.user_id == user_id and sub.status == SubscriptionStatus.ACTIVE:
                return sub
        return None
    
    async def check_user_limit(self, user_id: str, limit_type: str) -> bool:
        """التحقق من حدود المستخدم"""
        subscription = await self.get_user_subscription(user_id)
        
        if not subscription:
            subscription = await self.get_user_subscription(user_id) or Subscription(
                id="",
                user_id=user_id,
                plan=self.plans[PlanType.FREE],
                status=SubscriptionStatus.ACTIVE,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=365)
            )
        
        # يمكن إضافة منطق لفحص الاستخدام الفعلي
        return True
    
    async def upgrade_plan(self, user_id: str, new_plan_type: PlanType) -> bool:
        """ترقية الخطة"""
        try:
            current_sub = await self.get_user_subscription(user_id)
            
            if current_sub:
                # حساب الفرق في السعر
                new_plan = self.plans[new_plan_type]
                old_plan = current_sub.plan
                
                price_diff = new_plan.price_monthly - old_plan.price_monthly
                
                if price_diff > 0:
                    # معالجة الدفع الإضافي
                    if self.stripe_enabled:
                        payment_success = await self._process_stripe_payment(user_id, price_diff)
                    else:
                        payment_success = True
                    
                    if not payment_success:
                        return False
                
                # تحديث الخطة
                current_sub.plan = new_plan
                current_sub.end_date = datetime.now() + timedelta(days=30)
                
                logger.info(f"✅ تمت ترقية المستخدم {user_id} إلى {new_plan.name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"خطأ في ترقية الخطة: {e}")
            return False
    
    async def _process_stripe_payment(self, user_id: str, amount: float) -> bool:
        """معالجة الدفع عبر Stripe"""
        try:
            # إنشاء جلسة دفع
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'egp',
                        'unit_amount': int(amount * 100),  # بالقروش
                        'product_data': {
                            'name': 'اشتراك منصة التداول',
                            'description': f'اشتراك لمدة شهر - المستخدم {user_id}',
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='https://trading-platform.com/success',
                cancel_url='https://trading-platform.com/cancel',
            )
            
            # في التطبيق الحقيقي، سننتظر تأكيد الدفع عبر webhook
            return True
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الدفع: {e}")
            return False
    
    async def _record_transaction(
        self,
        user_id: str,
        amount: float,
        subscription_id: str,
        status: str
    ):
        """تسجيل معاملة مالية"""
        transaction = PaymentTransaction(
            id=self._generate_transaction_id(),
            user_id=user_id,
            amount=amount,
            currency="EGP",
            status=status,
            payment_method="card",
            transaction_date=datetime.now(),
            subscription_id=subscription_id
        )
        
        self.transactions[transaction.id] = transaction
        
        # حفظ في قاعدة البيانات
        await self._save_transaction(transaction)
    
    async def get_user_transactions(self, user_id: str) -> List[PaymentTransaction]:
        """الحصول على معاملات المستخدم"""
        return [t for t in self.transactions.values() if t.user_id == user_id]
    
    def _generate_subscription_id(self) -> str:
        """توليد معرف اشتراك فريد"""
        return f"SUB_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def _generate_transaction_id(self) -> str:
        """توليد معرف معاملة فريد"""
        return f"TXN_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    async def _load_subscriptions(self):
        """تحميل الاشتراكات المحفوظة"""
        pass
    
    async def _save_transaction(self, transaction: PaymentTransaction):
        """حفظ المعاملة"""
        pass
    
    async def _load_transactions(self):
        """تحميل المعاملات المحفوظة"""
        pass

    async def get_subscription_statistics(self) -> Dict:
        """إحصائيات الاشتراكات للوحة التحكم"""
        stats = {
            "total_subscriptions": 0,
            "active_subscriptions": 0,
            "by_plan": {},
            "monthly_revenue": 0,
            "yearly_revenue": 0
        }
        
        for sub in self.subscriptions.values():
            stats["total_subscriptions"] += 1
            
            if sub.status == SubscriptionStatus.ACTIVE:
                stats["active_subscriptions"] += 1
            
            plan_name = sub.plan.name
            if plan_name not in stats["by_plan"]:
                stats["by_plan"][plan_name] = 0
            stats["by_plan"][plan_name] += 1
        
        # حساب الإيرادات من المعاملات
        for trans in self.transactions.values():
            if trans.status in ["success", "renewal"]:
                stats["monthly_revenue"] += trans.amount
        
        stats["yearly_revenue"] = stats["monthly_revenue"] * 12
        
        return stats
