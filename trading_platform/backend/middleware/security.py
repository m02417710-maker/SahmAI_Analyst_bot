"""
ملف: backend/middleware/security.py
المسار: /trading_platform/backend/middleware/security.py
الوظيفة: وسائط الأمان المتقدمة للحماية من الهجمات
"""

import time
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import jwt
from loguru import logger

# ====================== Rate Limiting ======================
limiter = Limiter(key_func=get_remote_address)

class SecurityMiddleware:
    """وسيط الأمان المتكامل"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.rate_limits = {}
        self.blocked_ips = set()
        self.request_log = {}
        
    async def rate_limit_check(self, request: Request, limit: int = 100, window: int = 60) -> bool:
        """التحقق من حد الطلبات"""
        client_ip = request.client.host
        
        # التحقق من الحظر
        if client_ip in self.blocked_ips:
            raise HTTPException(status_code=403, detail="IP محظور")
        
        now = time.time()
        
        if client_ip not in self.request_log:
            self.request_log[client_ip] = []
        
        # تنظيف الطلبات القديمة
        self.request_log[client_ip] = [
            ts for ts in self.request_log[client_ip] 
            if now - ts < window
        ]
        
        # التحقق من الحد
        if len(self.request_log[client_ip]) >= limit:
            # حظر IP مؤقت بعد 10 محاولات
            if len(self.request_log[client_ip]) >= limit + 10:
                self.blocked_ips.add(client_ip)
                logger.warning(f"🚫 تم حظر IP: {client_ip}")
            return False
        
        self.request_log[client_ip].append(now)
        return True
    
    async def validate_jwt_token(self, token: str) -> Dict:
        """التحقق من صحة JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=["HS256"]
            )
            
            # التحقق من انتهاء الصلاحية
            if payload.get('exp') < datetime.now().timestamp():
                raise HTTPException(status_code=401, detail="انتهت صلاحية التوكن")
            
            return payload
            
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="توكن غير صالح")
    
    async def generate_jwt_token(self, user_id: str, expires_in: int = 3600) -> str:
        """توليد JWT token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.now().timestamp() + expires_in,
            'iat': datetime.now().timestamp(),
            'iss': 'trading-platform'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    async def validate_api_key(self, api_key: str, api_secret: str) -> bool:
        """التحقق من صحة مفتاح API"""
        # التحقق من التوقيع
        expected_signature = hmac.new(
            key=self.secret_key.encode(),
            msg=api_key.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, api_secret)
    
    async def sanitize_input(self, text: str) -> str:
        """تنظيف المدخلات من الـ XSS والهجمات"""
        # إزالة الـ HTML tags
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # إزالة الـ JavaScript
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        
        # ترميز الأحرف الخطرة
        dangerous_chars = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
            '&': '&amp;'
        }
        
        for char, replacement in dangerous_chars.items():
            text = text.replace(char, replacement)
        
        return text
    
    async def check_sql_injection(self, query: str) -> bool:
        """التحقق من هجمات SQL Injection"""
        sql_patterns = [
            r'\bSELECT\b.*\bFROM\b',
            r'\bINSERT\b.*\bINTO\b',
            r'\bUPDATE\b.*\bSET\b',
            r'\bDELETE\b.*\bFROM\b',
            r'\bDROP\b.*\bTABLE\b',
            r'\bUNION\b.*\bSELECT\b',
            r'--',
            r';.*\bDROP\b',
        ]
        
        import re
        for pattern in sql_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False

# ====================== التوكن ======================
security = HTTPBearer()

class AuthHandler:
    """معالج المصادقة"""
    
    def __init__(self, security_middleware: SecurityMiddleware):
        self.security = security_middleware
    
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict:
        """الحصول على المستخدم الحالي"""
        token = credentials.credentials
        payload = await self.security.validate_jwt_token(token)
        return payload
    
    async def require_admin(self, user: Dict = Depends(get_current_user)) -> Dict:
        """طلب صلاحيات مسؤول"""
        if not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="صلاحيات غير كافية")
        return user
    
    async def require_premium(self, user: Dict = Depends(get_current_user)) -> Dict:
        """طلب صلاحيات مميزة"""
        if user.get('subscription_plan') not in ['premium', 'pro', 'enterprise']:
            raise HTTPException(status_code=403, detail="مطلوب اشتراك مميز")
        return user

# ====================== CORS配置 ======================
class CORSMiddleware:
    """تكوين CORS للحماية"""
    
    async def __call__(self, request: Request, call_next):
        # التحقق من origin
        origin = request.headers.get('origin', '')
        allowed_origins = [
            'https://trading-platform.com',
            'https://www.trading-platform.com',
            'http://localhost:3000',
            'http://localhost:8000'
        ]
        
        if origin and origin not in allowed_origins:
            # منع الطلبات من origins غير مسموحة
            raise HTTPException(status_code=403, detail="Origin غير مسموح")
        
        response = await call_next(request)
        
        # إضافة رؤوس الأمان
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
