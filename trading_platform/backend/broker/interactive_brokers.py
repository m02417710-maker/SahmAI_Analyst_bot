"""
ملف: backend/broker/interactive_brokers.py
المسار: /trading_platform/backend/broker/interactive_brokers.py
الوظيفة: التكامل مع Interactive Brokers API للتداول الحقيقي
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from ib_async import IB, Stock, Order, MarketOrder, LimitOrder
from ib_async import Contract, AccountSummary, Position
import pandas as pd
from loguru import logger

@dataclass
class BrokerAccount:
    """حساب الوسيط"""
    account_id: str
    currency: str
    buying_power: float
    cash_balance: float
    stock_value: float
    total_value: float
    day_trades_remaining: int

@dataclass
class BrokerOrder:
    """أمر التداول عبر الوسيط"""
    order_id: int
    symbol: str
    action: str  # BUY, SELL
    quantity: int
    order_type: str  # MARKET, LIMIT
    limit_price: Optional[float]
    status: str
    filled_quantity: int
    avg_fill_price: float
    created_at: datetime
    filled_at: Optional[datetime]

class InteractiveBrokersConnector:
    """موصل Interactive Brokers"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = None
        self.is_connected = False
        self.orders: Dict[int, BrokerOrder] = {}
        self.positions: Dict[str, Position] = {}
        
    async def connect(self) -> bool:
        """الاتصال بـ Interactive Brokers"""
        try:
            self.ib = IB()
            await self.ib.connectAsync(self.host, self.port, clientId=self.client_id)
            self.is_connected = True
            
            # بدء مراقبة الحساب
            asyncio.create_task(self._monitor_account())
            
            logger.info(f"✅ تم الاتصال بـ Interactive Brokers (Port: {self.port})")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في الاتصال بـ Interactive Brokers: {e}")
            return False
    
    async def disconnect(self):
        """قطع الاتصال"""
        if self.ib and self.is_connected:
            await self.ib.disconnectAsync()
            self.is_connected = False
            logger.info("تم قطع الاتصال بـ Interactive Brokers")
    
    async def get_account_summary(self) -> BrokerAccount:
        """الحصول على ملخص الحساب"""
        try:
            accounts = await self.ib.reqAccountSummaryAsync("All", "TotalCashValue, BuyingPower, StockMarketValue, NetLiquidation")
            
            for account in accounts:
                if account.tag == "TotalCashValue":
                    cash_balance = float(account.value)
                elif account.tag == "BuyingPower":
                    buying_power = float(account.value)
                elif account.tag == "StockMarketValue":
                    stock_value = float(account.value)
                elif account.tag == "NetLiquidation":
                    total_value = float(account.value)
            
            return BrokerAccount(
                account_id=self.ib.wrapper.accountValues[0].account if self.ib.wrapper.accountValues else "Unknown",
                currency="USD",
                buying_power=buying_power,
                cash_balance=cash_balance,
                stock_value=stock_value,
                total_value=total_value,
                day_trades_remaining=3  # مثال
            )
            
        except Exception as e:
            logger.error(f"خطأ في جلب ملخص الحساب: {e}")
            return None
    
    async def place_order(
        self,
        symbol: str,
        action: str,
        quantity: int,
        order_type: str = "MARKET",
        limit_price: Optional[float] = None
    ) -> Optional[BrokerOrder]:
        """وضع أمر تداول"""
        try:
            # إنشاء عقد السهم
            contract = Stock(symbol, "SMART", "USD")
            
            # إنشاء الأمر
            if order_type == "MARKET":
                order = MarketOrder(action, quantity)
            elif order_type == "LIMIT" and limit_price:
                order = LimitOrder(action, quantity, limit_price)
            else:
                raise ValueError(f"نوع أمر غير صالح: {order_type}")
            
            # إرسال الأمر
            trade = await self.ib.placeOrderAsync(contract, order)
            
            broker_order = BrokerOrder(
                order_id=trade.order.orderId,
                symbol=symbol,
                action=action,
                quantity=quantity,
                order_type=order_type,
                limit_price=limit_price,
                status=trade.orderStatus.status,
                filled_quantity=trade.orderStatus.filled,
                avg_fill_price=trade.orderStatus.avgFillPrice,
                created_at=datetime.now(),
                filled_at=datetime.now() if trade.orderStatus.status == "Filled" else None
            )
            
            self.orders[broker_order.order_id] = broker_order
            logger.info(f"✅ تم وضع أمر {action} لـ {quantity} من {symbol}")
            
            return broker_order
            
        except Exception as e:
            logger.error(f"خطأ في وضع الأمر: {e}")
            return None
    
    async def cancel_order(self, order_id: int) -> bool:
        """إلغاء أمر"""
        try:
            await self.ib.cancelOrderAsync(order_id)
            logger.info(f"✅ تم إلغاء الأمر {order_id}")
            return True
        except Exception as e:
            logger.error(f"خطأ في إلغاء الأمر: {e}")
            return False
    
    async def get_positions(self) -> List[Dict]:
        """الحصول على المراكز الحالية"""
        try:
            positions = await self.ib.reqPositionsAsync()
            
            result = []
            for position in positions:
                result.append({
                    "symbol": position.contract.symbol,
                    "quantity": position.position,
                    "avg_cost": position.avgCost,
                    "current_price": await self._get_current_price(position.contract.symbol),
                    "unrealized_pnl": position.unrealizedPNL,
                    "market_value": position.marketValue
                })
            
            return result
            
        except Exception as e:
            logger.error(f"خطأ في جلب المراكز: {e}")
            return []
    
    async def get_order_status(self, order_id: int) -> Optional[Dict]:
        """الحصول على حالة الأمر"""
        try:
            if order_id in self.orders:
                order = self.orders[order_id]
                return {
                    "order_id": order.order_id,
                    "status": order.status,
                    "filled_quantity": order.filled_quantity,
                    "avg_fill_price": order.avg_fill_price
                }
            return None
        except Exception as e:
            logger.error(f"خطأ في جلب حالة الأمر: {e}")
            return None
    
    async def _get_current_price(self, symbol: str) -> float:
        """الحصول على السعر الحالي"""
        try:
            contract = Stock(symbol, "SMART", "USD")
            ticker = await self.ib.reqMktDataAsync(contract)
            return ticker.marketPrice()
        except:
            return 0.0
    
    async def execute_strategy_order(self, signal: Dict) -> Optional[BrokerOrder]:
        """تنفيذ أمر بناءً على إشارة استراتيجية"""
        try:
            symbol = signal['symbol']
            action = signal['action']
            quantity = signal['quantity']
            order_type = signal.get('order_type', 'MARKET')
            limit_price = signal.get('limit_price')
            
            # التحقق من الرصيد
            account = await self.get_account_summary()
            if not account:
                return None
            
            if action == "BUY":
                estimated_cost = quantity * (limit_price or (await self._get_current_price(symbol)))
                if estimated_cost > account.buying_power:
                    logger.warning(f"رصيد غير كافٍ لشراء {symbol}")
                    return None
            
            # وضع الأمر
            order = await self.place_order(symbol, action, quantity, order_type, limit_price)
            
            # تسجيل في قاعدة البيانات
            await self._log_trade(signal, order)
            
            return order
            
        except Exception as e:
            logger.error(f"خطأ في تنفيذ أمر الاستراتيجية: {e}")
            return None
    
    async def _monitor_account(self):
        """مراقبة الحساب بشكل مستمر"""
        while self.is_connected:
            try:
                account = await self.get_account_summary()
                if account:
                    # التحقق من margin call
                    if account.buying_power < 1000:
                        logger.warning("⚠️ تحذير: رصيد شراء منخفض!")
                    
                    # تحديث Redis
                    await self._update_account_cache(account)
                
                await asyncio.sleep(60)  # كل دقيقة
                
            except Exception as e:
                logger.error(f"خطأ في مراقبة الحساب: {e}")
                await asyncio.sleep(10)
    
    async def _log_trade(self, signal: Dict, order: BrokerOrder):
        """تسجيل الصفقة"""
        # تخزين في قاعدة البيانات
        pass
    
    async def _update_account_cache(self, account: BrokerAccount):
        """تحديث الكاش"""
        # تخزين في Redis
        pass
