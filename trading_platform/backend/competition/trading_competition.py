"""
ملف: backend/competition/trading_competition.py
المسار: /trading_platform/backend/competition/trading_competition.py
الوظيفة: نظام مسابقات التداول الافتراضية
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random
from loguru import logger

class CompetitionStatus(Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"

class CompetitionType(Enum):
    DAILY = "يومي"
    WEEKLY = "أسبوعي"
    MONTHLY = "شهري"
    SPECIAL = "خاص"

@dataclass
class Competition:
    """نموذج المسابقة"""
    id: str
    name: str
    type: CompetitionType
    status: CompetitionStatus
    start_date: datetime
    end_date: datetime
    initial_capital: float
    min_participants: int
    max_participants: int
    prize_pool: float
    entry_fee: float
    allowed_symbols: List[str]
    participants: List[str] = field(default_factory=list)
    winner_id: Optional[str] = None
    winner_return: Optional[float] = None

@dataclass
class ParticipantPortfolio:
    """محفظة المشارك في المسابقة"""
    user_id: str
    competition_id: str
    cash: float
    positions: Dict[str, Dict]  # symbol -> {quantity, avg_price}
    total_return: float = 0.0
    rank: int = 0
    trades: List[Dict] = field(default_factory=list)

class TradingCompetition:
    """نظام مسابقات التداول"""
    
    def __init__(self, market_data_manager):
        self.market_data = market_data_manager
        self.competitions: Dict[str, Competition] = {}
        self.portfolios: Dict[str, ParticipantPortfolio] = {}
        self.is_running = False
        
    async def initialize(self):
        """تهيئة النظام"""
        await self._load_competitions()
        logger.info("✅ تم تهيئة نظام المسابقات")
    
    async def create_competition(self, competition: Competition) -> bool:
        """إنشاء مسابقة جديدة"""
        try:
            self.competitions[competition.id] = competition
            await self._save_competition(competition)
            logger.info(f"✅ تم إنشاء مسابقة {competition.name}")
            return True
        except Exception as e:
            logger.error(f"خطأ في إنشاء المسابقة: {e}")
            return False
    
    async def join_competition(self, user_id: str, competition_id: str) -> bool:
        """الانضمام إلى مسابقة"""
        try:
            if competition_id not in self.competitions:
                logger.warning(f"المسابقة {competition_id} غير موجودة")
                return False
            
            competition = self.competitions[competition_id]
            
            # التحقق من حالة المسابقة
            if competition.status != CompetitionStatus.UPCOMING:
                logger.warning(f"لا يمكن الانضمام لمسابقة {competition.status.value}")
                return False
            
            # التحقق من العدد الأقصى
            if len(competition.participants) >= competition.max_participants:
                logger.warning("المسابقة مكتملة")
                return False
            
            # التحقق من الدفع (يمكن دمج مع نظام الاشتراكات)
            # if competition.entry_fee > 0:
            #     # معالجة الدفع
            #     pass
            
            # إضافة المشارك
            competition.participants.append(user_id)
            
            # إنشاء محفظة للمشارك
            portfolio_key = f"{user_id}_{competition_id}"
            self.portfolios[portfolio_key] = ParticipantPortfolio(
                user_id=user_id,
                competition_id=competition_id,
                cash=competition.initial_capital,
                positions={},
                trades=[]
            )
            
            logger.info(f"✅ انضم المستخدم {user_id} إلى مسابقة {competition.name}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في الانضمام للمسابقة: {e}")
            return False
    
    async def execute_trade(
        self,
        user_id: str,
        competition_id: str,
        symbol: str,
        action: str,
        quantity: int
    ) -> Dict:
        """تنفيذ صفقة في المسابقة"""
        try:
            competition = self.competitions.get(competition_id)
            if not competition or competition.status != CompetitionStatus.ACTIVE:
                return {"success": False, "message": "المسابقة غير نشطة"}
            
            # التحقق من أن السهم مسموح
            if symbol not in competition.allowed_symbols:
                return {"success": False, "message": "هذا السهم غير مسموح في المسابقة"}
            
            portfolio_key = f"{user_id}_{competition_id}"
            portfolio = self.portfolios.get(portfolio_key)
            if not portfolio:
                return {"success": False, "message": "المشارك غير موجود"}
            
            # جلب السعر الحالي
            snapshot = await self.market_data.get_stock_snapshot([symbol])
            if symbol not in snapshot:
                return {"success": False, "message": "لا يمكن جلب سعر السهم"}
            
            current_price = snapshot[symbol].price
            trade_value = current_price * quantity
            
            if action.upper() == "BUY":
                # التحقق من الرصيد
                if trade_value > portfolio.cash:
                    return {"success": False, "message": "رصيد غير كافٍ"}
                
                # تنفيذ الشراء
                portfolio.cash -= trade_value
                
                if symbol in portfolio.positions:
                    # تحديث مركز موجود
                    old_quantity = portfolio.positions[symbol]['quantity']
                    old_avg_price = portfolio.positions[symbol]['avg_price']
                    
                    new_quantity = old_quantity + quantity
                    new_avg_price = ((old_quantity * old_avg_price) + (quantity * current_price)) / new_quantity
                    
                    portfolio.positions[symbol] = {
                        'quantity': new_quantity,
                        'avg_price': new_avg_price
                    }
                else:
                    # مركز جديد
                    portfolio.positions[symbol] = {
                        'quantity': quantity,
                        'avg_price': current_price
                    }
                
            elif action.upper() == "SELL":
                # التحقق من وجود السهم
                if symbol not in portfolio.positions or portfolio.positions[symbol]['quantity'] < quantity:
                    return {"success": False, "message": "كمية غير كافية للبيع"}
                
                # تنفيذ البيع
                portfolio.cash += trade_value
                
                # تحديث المركز
                portfolio.positions[symbol]['quantity'] -= quantity
                
                if portfolio.positions[symbol]['quantity'] == 0:
                    del portfolio.positions[symbol]
            
            # تسجيل الصفقة
            portfolio.trades.append({
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': current_price,
                'value': trade_value
            })
            
            # تحديث العائد الإجمالي
            await self._update_participant_return(portfolio, competition)
            
            logger.info(f"✅ تم تنفيذ صفقة {action} لـ {quantity} من {symbol} في مسابقة {competition.name}")
            
            return {
                "success": True,
                "message": f"تم تنفيذ {action} بنجاح",
                "cash_remaining": portfolio.cash,
                "trade": {
                    "symbol": symbol,
                    "action": action,
                    "quantity": quantity,
                    "price": current_price,
                    "value": trade_value,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"خطأ في تنفيذ الصفقة: {e}")
            return {"success": False, "message": str(e)}
    
    async def _update_participant_return(self, portfolio: ParticipantPortfolio, competition: Competition):
        """تحديث عائد المشارك"""
        try:
            total_value = portfolio.cash
            
            # حساب قيمة المراكز
            for symbol, position in portfolio.positions.items():
                snapshot = await self.market_data.get_stock_snapshot([symbol])
                if symbol in snapshot:
                    current_price = snapshot[symbol].price
                    total_value += position['quantity'] * current_price
            
            initial_value = competition.initial_capital
            portfolio.total_return = ((total_value - initial_value) / initial_value) * 100
            
        except Exception as e:
            logger.error(f"خطأ في تحديث العائد: {e}")
    
    async def get_leaderboard(self, competition_id: str) -> List[Dict]:
        """الحصول على جدول المتصدرين"""
        try:
            competition = self.competitions.get(competition_id)
            if not competition:
                return []
            
            # تجميع جميع المشاركين
            participants_data = []
            for user_id in competition.participants:
                portfolio_key = f"{user_id}_{competition_id}"
                portfolio = self.portfolios.get(portfolio_key)
                
                if portfolio:
                    participants_data.append({
                        "user_id": user_id,
                        "return": portfolio.total_return,
                        "cash": portfolio.cash,
                        "positions_count": len(portfolio.positions)
                    })
            
            # ترتيب حسب العائد
            participants_data.sort(key=lambda x: x['return'], reverse=True)
            
            # إضافة الترتيب
            for idx, participant in enumerate(participants_data, 1):
                participant['rank'] = idx
                
                # تحديث الترتيب في الـ portfolio
                portfolio_key = f"{participant['user_id']}_{competition_id}"
                if portfolio_key in self.portfolios:
                    self.portfolios[portfolio_key].rank = idx
            
            return participants_data
            
        except Exception as e:
            logger.error(f"خطأ في جلب جدول المتصدرين: {e}")
            return []
    
    async def end_competition(self, competition_id: str) -> Dict:
        """إنهاء المسابقة وتوزيع الجوائز"""
        try:
            competition = self.competitions.get(competition_id)
            if not competition:
                return {"success": False, "message": "المسابقة غير موجودة"}
            
            if competition.status != CompetitionStatus.ACTIVE:
                return {"success": False, "message": "المسابقة غير نشطة"}
            
            # الحصول على جدول المتصدرين
            leaderboard = await self.get_leaderboard(competition_id)
            
            if not leaderboard:
                return {"success": False, "message": "لا يوجد مشاركين"}
            
            # تحديد الفائزين
            winner = leaderboard[0]
            competition.status = CompetitionStatus.ENDED
            competition.winner_id = winner['user_id']
            competition.winner_return = winner['return']
            
            # توزيع الجوائز
            prizes = {
                1: competition.prize_pool * 0.5,
                2: competition.prize_pool * 0.3,
                3: competition.prize_pool * 0.2
            }
            
            for idx, participant in enumerate(leaderboard[:3], 1):
                prize = prizes.get(idx, 0)
                # إضافة الجائزة للمستخدم
                await self._award_prize(participant['user_id'], prize, competition_id)
            
            # حفظ النتائج
            await self._save_competition_results(competition, leaderboard)
            
            logger.info(f"🏆 انتهت مسابقة {competition.name} - الفائز: {winner['user_id']} بعائد {winner['return']:.2f}%")
            
            return {
                "success": True,
                "competition": competition.name,
                "winner": {
                    "user_id": winner['user_id'],
                    "return": winner['return']
                },
                "prizes_distributed": True
            }
            
        except Exception as e:
            logger.error(f"خطأ في إنهاء المسابقة: {e}")
            return {"success": False, "message": str(e)}
    
    async def start_competition(self, competition_id: str) -> bool:
        """بدء المسابقة"""
        try:
            competition = self.competitions.get(competition_id)
            if not competition:
                return False
            
            if len(competition.participants) < competition.min_participants:
                logger.warning(f"عدد المشاركين غير كافٍ لبدء مسابقة {competition.name}")
                return False
            
            competition.status = CompetitionStatus.ACTIVE
            competition.start_date = datetime.now()
            
            logger.info(f"🚀 بدأت مسابقة {competition.name} مع {len(competition.participants)} مشارك")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في بدء المسابقة: {e}")
            return False
    
    async def _award_prize(self, user_id: str, amount: float, competition_id: str):
        """منح جائزة للمستخدم"""
        # يمكن إضافة الرصيد لحساب المستخدم الحقيقي
        logger.info(f"💰 تم منح {user_id} جائزة قدرها {amount} في مسابقة {competition_id}")
    
    async def get_user_competition_history(self, user_id: str) -> List[Dict]:
        """سجل مشاركات المستخدم"""
        history = []
        
        for comp_id, competition in self.competitions.items():
            if user_id in competition.participants:
                portfolio_key = f"{user_id}_{comp_id}"
                portfolio = self.portfolios.get(portfolio_key)
                
                history.append({
                    "competition_id": comp_id,
                    "competition_name": competition.name,
                    "type": competition.type.value,
                    "status": competition.status.value,
                    "start_date": competition.start_date.isoformat(),
                    "end_date": competition.end_date.isoformat(),
                    "final_return": portfolio.total_return if portfolio else 0,
                    "rank": portfolio.rank if portfolio else 0,
                    "is_winner": competition.winner_id == user_id
                })
        
        return sorted(history, key=lambda x: x['start_date'], reverse=True)
    
    async def create_daily_competition(self):
        """إنشاء مسابقة يومية تلقائية"""
        today = datetime.now()
        competition = Competition(
            id=f"daily_{today.strftime('%Y%m%d')}",
            name=f"مسابقة اليوم {today.strftime('%d/%m/%Y')}",
            type=CompetitionType.DAILY,
            status=CompetitionStatus.UPCOMING,
            start_date=today.replace(hour=9, minute=0, second=0),
            end_date=today.replace(hour=21, minute=0, second=0),
            initial_capital=10000,
            min_participants=5,
            max_participants=100,
            prize_pool=1000,
            entry_fee=10,
            allowed_symbols=["COMI.CA", "TMGH.CA", "AAPL", "MSFT", "TSLA"]
        )
        await self.create_competition(competition)
    
    async def _load_competitions(self):
        """تحميل المسابقات المحفوظة"""
        # إنشاء مسابقات تجريبية
        now = datetime.now()
        
        # مسابقة نشطة
        active_comp = Competition(
            id="weekly_001",
            name="مسابقة الأسبوع الأولى",
            type=CompetitionType.WEEKLY,
            status=CompetitionStatus.ACTIVE,
            start_date=now - timedelta(days=2),
            end_date=now + timedelta(days=5),
            initial_capital=50000,
            min_participants=10,
            max_participants=500,
            prize_pool=5000,
            entry_fee=25,
            allowed_symbols=["COMI.CA", "TMGH.CA", "SWDY.CA", "2222.SR", "AAPL", "MSFT", "GOOGL"]
        )
        
        # مسابقة قادمة
        upcoming_comp = Competition(
            id="monthly_001",
            name="بطولة الشهر - ديسمبر",
            type=CompetitionType.MONTHLY,
            status=CompetitionStatus.UPCOMING,
            start_date=now + timedelta(days=7),
            end_date=now + timedelta(days=37),
            initial_capital=100000,
            min_participants=50,
            max_participants=1000,
            prize_pool=50000,
            entry_fee=100,
            allowed_symbols=["COMI.CA", "TMGH.CA", "2222.SR", "1120.SR", "AAPL", "MSFT", "TSLA", "NVDA"]
        )
        
        self.competitions = {
            "weekly_001": active_comp,
            "monthly_001": upcoming_comp
        }
    
    async def _save_competition(self, competition: Competition):
        """حفظ بيانات المسابقة"""
        pass
    
    async def _save_competition_results(self, competition: Competition, leaderboard: List[Dict]):
        """حفظ نتائج المسابقة"""
        pass
