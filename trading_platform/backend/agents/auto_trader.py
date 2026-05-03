"""
ملف: backend/agents/auto_trader.py
المسار: /trading_platform/backend/agents/auto_trader.py
الوظيفة: نظام التداول الآلي - تنفيذ الصفقات تلقائياً
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import numpy as np

class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"

class OrderStatus(Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

@dataclass
class Order:
    """نموذج أمر التداول"""
    id: str
    symbol: str
    type: OrderType
    price: float
    quantity: int
    status: OrderStatus
    created_at: datetime
    executed_at: Optional[datetime] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

@dataclass
class TradingStrategy:
    """استراتيجية التداول"""
    name: str
    symbol: str
    conditions: Dict
    quantity: int
    stop_loss_percent: float
    take_profit_percent: float
    is_active: bool = True

class AutoTrader:
    """نظام التداول الآلي الذكي"""
    
    def __init__(self, market_data_manager, trading_agent):
        self.market_data = market_data_manager
        self.trading_agent = trading_agent
        self.orders: Dict[str, Order] = {}
        self.strategies: Dict[str, TradingStrategy] = {}
        self.positions: Dict[str, Dict] = {}  # المراكز المفتوحة
        self.is_running = False
        
    async def initialize(self):
        """تهيئة النظام"""
        # تحميل الاستراتيجيات المحفوظة
        await self._load_strategies()
        
        # تحميل المراكز المفتوحة
        await self._load_positions()
        
        logger.info("✅ تم تهيئة نظام التداول الآلي")
    
    async def start(self):
        """بدء تشغيل النظام"""
        self.is_running = True
        asyncio.create_task(self._monitor_loop())
        logger.info("🚀 بدء تشغيل نظام التداول الآلي")
    
    async def stop(self):
        """إيقاف النظام"""
        self.is_running = False
        logger.info("🛑 إيقاف نظام التداول الآلي")
    
    async def _monitor_loop(self):
        """حلقة المراقبة الرئيسية"""
        while self.is_running:
            try:
                # فحص الاستراتيجيات النشطة
                for strategy in self.strategies.values():
                    if strategy.is_active:
                        await self._check_strategy(strategy)
                
                # فحص المراكز المفتوحة (وقف الخسارة/جني الأرباح)
                await self._check_positions()
                
                # فحص الأوامر المعلقة
                await self._check_pending_orders()
                
                await asyncio.sleep(5)  # فحص كل 5 ثواني
                
            except Exception as e:
                logger.error(f"خطأ في حلقة المراقبة: {e}")
    
    async def add_strategy(self, strategy: TradingStrategy):
        """إضافة استراتيجية تداول جديدة"""
        self.strategies[strategy.symbol] = strategy
        await self._save_strategy(strategy)
        logger.info(f"✅ تم إضافة استراتيجية لـ {strategy.symbol}")
    
    async def remove_strategy(self, symbol: str):
        """إزالة استراتيجية"""
        if symbol in self.strategies:
            del self.strategies[symbol]
            logger.info(f"🗑 تم إزالة استراتيجية {symbol}")
    
    async def _check_strategy(self, strategy: TradingStrategy):
        """فحص شروط الاستراتيجية"""
        try:
            # جلب المؤشرات الفنية
            indicators = await self.market_data.get_technical_indicators(strategy.symbol)
            if not indicators:
                return
            
            # جلب السعر الحالي
            snapshot = await self.market_data.get_stock_snapshot([strategy.symbol])
            if strategy.symbol not in snapshot:
                return
            
            current_price = snapshot[strategy.symbol].price
            conditions = strategy.conditions
            
            # فحص شروط الشراء
            buy_signals = 0
            sell_signals = 0
            
            # شرط RSI
            rsi = indicators.rsi
            if 'rsi_below' in conditions and rsi < conditions['rsi_below']:
                buy_signals += 1
            if 'rsi_above' in conditions and rsi > conditions['rsi_above']:
                sell_signals += 1
            
            # شرط المتوسطات المتحركة
            if 'sma_cross' in conditions:
                if indicators.sma_20 > indicators.sma_50:
                    buy_signals += 1
                elif indicators.sma_20 < indicators.sma_50:
                    sell_signals += 1
            
            # شرط حجم التداول
            if 'volume_ratio' in conditions and indicators.volume_ratio > conditions['volume_ratio']:
                buy_signals += 1
            
            # اتخاذ القرار
            required_signals = conditions.get('required_signals', 2)
            
            # تنفيذ أمر شراء
            if buy_signals >= required_signals and strategy.symbol not in self.positions:
                await self._execute_order(Order(
                    id=self._generate_order_id(),
                    symbol=strategy.symbol,
                    type=OrderType.BUY,
                    price=current_price,
                    quantity=strategy.quantity,
                    status=OrderStatus.PENDING,
                    created_at=datetime.now(),
                    stop_loss=current_price * (1 - strategy.stop_loss_percent / 100),
                    take_profit=current_price * (1 + strategy.take_profit_percent / 100)
                ))
            
            # تنفيذ أمر بيع
            elif sell_signals >= required_signals and strategy.symbol in self.positions:
                await self._execute_order(Order(
                    id=self._generate_order_id(),
                    symbol=strategy.symbol,
                    type=OrderType.SELL,
                    price=current_price,
                    quantity=strategy.quantity,
                    status=OrderStatus.PENDING,
                    created_at=datetime.now()
                ))
                
        except Exception as e:
            logger.error(f"خطأ في فحص استراتيجية {strategy.symbol}: {e}")
    
    async def _execute_order(self, order: Order):
        """تنفيذ أمر تداول"""
        try:
            # محاكاة تنفيذ الأمر (في الحقيقة سيتم الاتصال بـ API الوسيط)
            logger.info(f"📊 تنفيذ أمر {order.type.value} لـ {order.symbol} بسعر {order.price}")
            
            # تحديث حالة الأمر
            order.status = OrderStatus.EXECUTED
            order.executed_at = datetime.now()
            self.orders[order.id] = order
            
            # تحديث المراكز
            if order.type == OrderType.BUY:
                self.positions[order.symbol] = {
                    'entry_price': order.price,
                    'quantity': order.quantity,
                    'stop_loss': order.stop_loss,
                    'take_profit': order.take_profit,
                    'entry_time': order.executed_at
                }
                logger.info(f"✅ تم شراء {order.quantity} من {order.symbol}")
                
            elif order.type == OrderType.SELL:
                if order.symbol in self.positions:
                    # حساب الربح/الخسارة
                    position = self.positions[order.symbol]
                    profit = (order.price - position['entry_price']) * order.quantity
                    profit_percent = ((order.price - position['entry_price']) / position['entry_price']) * 100
                    
                    logger.info(f"✅ تم بيع {order.quantity} من {order.symbol}")
                    logger.info(f"   الربح/الخسارة: {profit:+.2f} ({profit_percent:+.1f}%)")
                    
                    # إزالة من المراكز المفتوحة
                    del self.positions[order.symbol]
            
            # حفظ الأمر في قاعدة البيانات
            await self._save_order(order)
            
        except Exception as e:
            logger.error(f"خطأ في تنفيذ أمر {order.id}: {e}")
            order.status = OrderStatus.FAILED
    
    async def _check_positions(self):
        """فحص المراكز المفتوحة لوقف الخسارة وجني الأرباح"""
        for symbol, position in list(self.positions.items()):
            try:
                # جلب السعر الحالي
                snapshot = await self.market_data.get_stock_snapshot([symbol])
                if symbol not in snapshot:
                    continue
                
                current_price = snapshot[symbol].price
                entry_price = position['entry_price']
                
                # فحص وقف الخسارة
                if position['stop_loss'] and current_price <= position['stop_loss']:
                    logger.warning(f"⚠️ تفعيل وقف الخسارة لـ {symbol} عند {current_price}")
                    await self._execute_order(Order(
                        id=self._generate_order_id(),
                        symbol=symbol,
                        type=OrderType.STOP_LOSS,
                        price=current_price,
                        quantity=position['quantity'],
                        status=OrderStatus.PENDING,
                        created_at=datetime.now()
                    ))
                
                # فحص جني الأرباح
                elif position['take_profit'] and current_price >= position['take_profit']:
                    logger.info(f"🎯 تحقيق هدف الربح لـ {symbol} عند {current_price}")
                    await self._execute_order(Order(
                        id=self._generate_order_id(),
                        symbol=symbol,
                        type=OrderType.TAKE_PROFIT,
                        price=current_price,
                        quantity=position['quantity'],
                        status=OrderStatus.PENDING,
                        created_at=datetime.now()
                    ))
                    
            except Exception as e:
                logger.error(f"خطأ في فحص مركز {symbol}: {e}")
    
    async def _check_pending_orders(self):
        """فحص الأوامر المعلقة"""
        # يمكن إضافة منطق لفحص الأوامر المعلقة مثل أوامر الحد
        pass
    
    async def get_portfolio_summary(self) -> Dict:
        """الحصول على ملخص المحفظة"""
        total_value = 0
        total_invested = 0
        positions_summary = []
        
        for symbol, position in self.positions.items():
            # جلب السعر الحالي
            snapshot = await self.market_data.get_stock_snapshot([symbol])
            current_price = snapshot[symbol].price if symbol in snapshot else position['entry_price']
            
            current_value = current_price * position['quantity']
            invested_value = position['entry_price'] * position['quantity']
            profit = current_value - invested_value
            profit_percent = (profit / invested_value) * 100 if invested_value > 0 else 0
            
            total_value += current_value
            total_invested += invested_value
            
            positions_summary.append({
                'symbol': symbol,
                'quantity': position['quantity'],
                'entry_price': position['entry_price'],
                'current_price': current_price,
                'current_value': current_value,
                'profit': profit,
                'profit_percent': profit_percent,
                'stop_loss': position['stop_loss'],
                'take_profit': position['take_profit']
            })
        
        total_profit = total_value - total_invested
        total_profit_percent = (total_profit / total_invested) * 100 if total_invested > 0 else 0
        
        return {
            'total_value': total_value,
            'total_invested': total_invested,
            'total_profit': total_profit,
            'total_profit_percent': total_profit_percent,
            'positions': positions_summary,
            'positions_count': len(positions_summary)
        }
    
    def _generate_order_id(self) -> str:
        """توليد معرف فريد للأمر"""
        return f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    async def _save_strategy(self, strategy: TradingStrategy):
        """حفظ الاستراتيجية في قاعدة البيانات"""
        # يمكن تخزين في Redis أو PostgreSQL
        pass
    
    async def _load_strategies(self):
        """تحميل الاستراتيجيات المحفوظة"""
        pass
    
    async def _save_positions(self):
        """حفظ المراكز"""
        pass
    
    async def _load_positions(self):
        """تحميل المراكز المحفوظة"""
        pass
    
    async def _save_order(self, order: Order):
        """حفظ الأمر"""
        pass
