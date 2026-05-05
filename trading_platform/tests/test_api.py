"""
ملف: tests/test_api.py
المسار: /trading_platform/tests/test_api.py
الوظيفة: اختبارات API للمنصة
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

class TestAPI:
    """اختبارات واجهة API"""
    
    def test_root_endpoint(self):
        """اختبار نقطة النهاية الرئيسية"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    def test_health_check(self):
        """اختبار فحص الصحة"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_stock_data(self):
        """اختبار جلب بيانات السهم"""
        response = client.get("/api/stock/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert "symbol" in data
        assert "price" in data
    
    def test_technical_indicators(self):
        """اختبار المؤشرات الفنية"""
        response = client.get("/api/indicators/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert "rsi" in data
        assert "sma_20" in data
    
    def test_market_opportunities(self):
        """اختبار فرص السوق"""
        response = client.get("/api/market/opportunities")
        assert response.status_code == 200
        data = response.json()
        assert "opportunities" in data
    
    def test_search_stocks(self):
        """اختبار البحث عن الأسهم"""
        response = client.get("/api/search/Apple")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    def test_invalid_symbol(self):
        """اختبار رمز غير صالح"""
        response = client.get("/api/stock/INVALID_SYMBOL")
        assert response.status_code == 404
    
    def test_daily_report(self):
        """اختبار التقرير اليومي"""
        response = client.get("/api/report/daily")
        assert response.status_code == 200
        data = response.json()
        assert "report" in data

class TestWebSocket:
    """اختبارات WebSocket"""
    
    def test_websocket_connection(self):
        """اختبار اتصال WebSocket"""
        # يمكن تنفيذ اختبار WebSocket
        pass

if __name__ == "__main__":
    pytest.main(["-v", __file__])
