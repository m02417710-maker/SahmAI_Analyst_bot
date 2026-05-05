#!/usr/bin/env python3
"""
ملف: scripts/health_check.py
المسار: /trading_platform/scripts/health_check.py
الوظيفة: فحص صحة النظام وإرسال تنبيهات
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, List

# تكوين التنبيهات
ALERT_WEBHOOK = "https://hooks.slack.com/services/xxx/xxx/xxx"  # Slack webhook
HEALTH_CHECK_URL = "http://localhost:8000/health"

def check_health() -> Dict:
    """فحص صحة النظام"""
    try:
        response = requests.get(HEALTH_CHECK_URL, timeout=10)
        return response.json()
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def send_alert(message: str):
    """إرسال تنبيه"""
    alert_data = {
        "text": f"⚠️ تنبيه صحي: {message}",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        requests.post(ALERT_WEBHOOK, json=alert_data)
    except:
        pass

def main():
    """الدالة الرئيسية"""
    health = check_health()
    
    if health.get('status') != 'healthy':
        send_alert(f"النظام غير صحي: {health}")
        sys.exit(1)
    
    print("✅ النظام يعمل بشكل طبيعي")
    sys.exit(0)

if __name__ == "__main__":
    main()
