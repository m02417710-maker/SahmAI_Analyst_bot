"""
ملف: backend/middleware/logging.py
المسار: /trading_platform/backend/middleware/logging.py
الوظيفة: تسجيل الطلبات والأحداث
"""

import time
import json
from datetime import datetime
from typing import Dict, Any
from fastapi import Request
from loguru import logger
import uuid

class LoggingMiddleware:
    """وسيط تسجيل الطلبات"""
    
    def __init__(self):
        self.request_count = 0
        
    async def log_request(self, request: Request, call_next):
        """تسجيل الطلب"""
        # توليد معرف فريد للطلب
        request_id = str(uuid.uuid4())
        
        # بدء التوقيت
        start_time = time.time()
        
        # تسجيل معلومات الطلب
        log_data = {
            'request_id': request_id,
            'method': request.method,
            'url': str(request.url),
            'client_ip': request.client.host,
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"📥 طلب وارد: {json.dumps(log_data, ensure_ascii=False)}")
        
        # تنفيذ الطلب
        try:
            response = await call_next(request)
            
            # حساب وقت المعالجة
            process_time = (time.time() - start_time) * 1000
            
            # تسجيل الاستجابة
            response_data = {
                'request_id': request_id,
                'status_code': response.status_code,
                'process_time_ms': round(process_time, 2)
            }
            
            logger.info(f"📤 رد صادر: {json.dumps(response_data, ensure_ascii=False)}")
            
            # إضافة رأس الـ request ID
            response.headers['X-Request-ID'] = request_id
            
            # تحديث الإحصائيات
            self.request_count += 1
            
            return response
            
        except Exception as e:
            # تسجيل الأخطاء
            error_data = {
                'request_id': request_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            logger.error(f"❌ خطأ: {json.dumps(error_data, ensure_ascii=False)}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الطلبات"""
        return {
            'total_requests': self.request_count,
            'timestamp': datetime.now().isoformat()
        }

# ====================== تسجيل الأداء ======================
class PerformanceLogger:
    """تسجيل أداء النظام"""
    
    def __init__(self):
        self.metrics = {
            'api_response_times': [],
            'database_query_times': [],
            'ai_inference_times': []
        }
    
    def record_api_response(self, endpoint: str, duration_ms: float):
        """تسجيل وقت استجابة API"""
        self.metrics['api_response_times'].append({
            'endpoint': endpoint,
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat()
        })
        
        # الاحتفاظ بآخر 1000 قياس فقط
        if len(self.metrics['api_response_times']) > 1000:
            self.metrics['api_response_times'] = self.metrics['api_response_times'][-1000:]
    
    def record_db_query(self, query: str, duration_ms: float):
        """تسجيل وقت استعلام قاعدة البيانات"""
        self.metrics['database_query_times'].append({
            'query': query[:100],  # تقطيع الاستعلام الطويل
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_average_response_time(self) -> float:
        """متوسط وقت الاستجابة"""
        if not self.metrics['api_response_times']:
            return 0.0
        
        times = [m['duration_ms'] for m in self.metrics['api_response_times']]
        return sum(times) / len(times)
    
    def get_slow_endpoints(self, threshold_ms: int = 1000) -> list:
        """نقاط النهاية البطيئة"""
        slow = []
        for metric in self.metrics['api_response_times']:
            if metric['duration_ms'] > threshold_ms:
                slow.append(metric)
        return slow
    
    def get_performance_report(self) -> Dict:
        """تقرير الأداء"""
        avg_response = self.get_average_response_time()
        slow_endpoints = self.get_slow_endpoints()
        
        return {
            'average_response_time_ms': round(avg_response, 2),
            'total_requests': len(self.metrics['api_response_times']),
            'slow_endpoints_count': len(slow_endpoints),
            'slow_endpoints': slow_endpoints[:10],  # آخر 10 endpoints بطيئة
            'timestamp': datetime.now().isoformat()
        }
