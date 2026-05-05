"""
ملف: backend/websocket/notification_manager.py
المسار: /trading_platform/backend/websocket/notification_manager.py
الوظيفة: نظام إشعارات WebSocket المتقدم
"""

import asyncio
from typing import Dict, List, Set, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import json
from loguru import logger

class ConnectionManager:
    """مدير اتصالات WebSocket"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_subscriptions: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """تسجيل اتصال جديد"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_subscriptions[user_id] = set()
        logger.info(f"✅ WebSocket متصل: {user_id}")
    
    def disconnect(self, user_id: str):
        """إزالة اتصال"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_subscriptions:
            del self.user_subscriptions[user_id]
        logger.info(f"❌ WebSocket مفصول: {user_id}")
    
    async def subscribe(self, user_id: str, symbol: str):
        """اشتراك في تحديثات سهم"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].add(symbol)
    
    async def unsubscribe(self, user_id: str, symbol: str):
        """إلغاء الاشتراك"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(symbol)
    
    async def send_personal_message(self, message: Dict, user_id: str):
        """إرسال رسالة خاصة لمستخدم"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except:
                self.disconnect(user_id)
    
    async def broadcast_to_subscribers(self, symbol: str, data: Dict):
        """بث تحديثات لمشتركي سهم معين"""
        for user_id, subscriptions in self.user_subscriptions.items():
            if symbol in subscriptions and user_id in self.active_connections:
                try:
                    await self.active_connections[user_id].send_json({
                        "type": "stock_update",
                        "symbol": symbol,
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    })
                except:
                    self.disconnect(user_id)
    
    async def broadcast_to_all(self, message: Dict):
        """بث رسالة لجميع المستخدمين"""
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except:
                self.disconnect(user_id)

class NotificationService:
    """خدمة الإشعارات المتكاملة"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.notification_queue = asyncio.Queue()
        self.is_running = False
        
    async def start(self):
        """بدء خدمة الإشعارات"""
        self.is_running = True
        asyncio.create_task(self._process_notifications())
        logger.info("🚀 بدء خدمة الإشعارات")
    
    async def send_notification(self, user_id: str, title: str, message: str, priority: str = "normal"):
        """إرسال إشعار لمستخدم"""
        notification = {
            "type": "notification",
            "title": title,
            "message": message,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
            "read": False
        }
        
        await self.connection_manager.send_personal_message(notification, user_id)
        
        # تخزين للإشعارات غير المقروءة
        await self._store_notification(user_id, notification)
    
    async def send_price_alert(self, user_id: str, symbol: str, price: float, target_price: float):
        """إرسال تنبيه سعر"""
        await self.send_notification(
            user_id=user_id,
            title=f"🔔 تنبيه سعر {symbol}",
            message=f"وصل سهم {symbol} إلى {price} (الهدف: {target_price})",
            priority="high"
        )
    
    async def send_signal_alert(self, user_id: str, symbol: str, action: str, confidence: float):
        """إرسال تنبيه إشارة تداول"""
        action_icon = "🟢" if action == "BUY" else "🔴"
        await self.send_notification(
            user_id=user_id,
            title=f"{action_icon} إشارة {action} لـ {symbol}",
            message=f"ثقة الإشارة: {confidence:.0f}% - تم اكتشاف فرصة {action}",
            priority="high"
        )
    
    async def send_market_alert(self, user_id: str, alert_type: str, message: str):
        """إرسال تنبيه سوق عام"""
        await self.send_notification(
            user_id=user_id,
            title=f"📊 تحديث السوق - {alert_type}",
            message=message,
            priority="medium"
        )
    
    async def _process_notifications(self):
        """معالجة قائمة الإشعارات"""
        while self.is_running:
            try:
                # معالجة الإشعارات في الخلفية
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"خطأ في معالجة الإشعارات: {e}")
    
    async def _store_notification(self, user_id: str, notification: Dict):
        """تخزين الإشعار في قاعدة البيانات"""
        # يمكن تخزين في Redis أو PostgreSQL
        pass

class WebSocketHandler:
    """معالج WebSocket الرئيسي"""
    
    def __init__(self, notification_service: NotificationService, market_data):
        self.notification_service = notification_service
        self.market_data = market_data
        self.connection_manager = ConnectionManager()
        
    async def handle_websocket(self, websocket: WebSocket, user_id: str):
        """معالجة اتصال WebSocket"""
        await self.connection_manager.connect(websocket, user_id)
        
        try:
            while True:
                # استقبال الرسائل من العميل
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # معالجة不同类型的الرسائل
                if message['type'] == 'subscribe':
                    for symbol in message.get('symbols', []):
                        await self.connection_manager.subscribe(user_id, symbol)
                    
                    await websocket.send_json({
                        "type": "subscribed",
                        "symbols": message.get('symbols', []),
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif message['type'] == 'unsubscribe':
                    for symbol in message.get('symbols', []):
                        await self.connection_manager.unsubscribe(user_id, symbol)
                
                elif message['type'] == 'ping':
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                
        except WebSocketDisconnect:
            self.connection_manager.disconnect(user_id)
        except Exception as e:
            logger.error(f"خطأ في WebSocket: {e}")
            self.connection_manager.disconnect(user_id)
