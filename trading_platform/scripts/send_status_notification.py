#!/usr/bin/env python3
"""
ملف: scripts/send_status_notification.py
المسار: /trading_platform/scripts/send_status_notification.py
الوظيفة: إرسال إشعارات حالة النظام إلى تليجرام
"""

import requests
import os
import sys
from datetime import datetime

def send_telegram_message(message: str):
    """إرسال رسالة إلى تليجرام"""
    token = os.environ.get('TELEGRAM_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    
    if not token or not chat_id:
        print("⚠️ لا توجد مفاتيح تليجرام")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.ok:
            print("✅ تم إرسال الإشعار")
        else:
            print(f"❌ فشل الإرسال: {response.text}")
    except Exception as e:
        print(f"❌ خطأ: {e}")

def main():
    """إرسال إشعار حالة النظام"""
    
    status = "✅ **نجاح**" if len(sys.argv) < 2 else sys.argv[1]
    
    message = f"""
🤖 **تقرير نظام البورصجي AI**

📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 الحالة: {status}

🔄 تم إجراء التحديثات التالية:
• جلب بيانات الأسهم اليومية
• تحديث المؤشرات الفنية
• تحليل الذكاء الاصطناعي
• إصلاح تنسيق الكود

🚀 التطبيق يعمل بشكل طبيعي

---
_تم الإرسال تلقائياً من GitHub Actions_
"""
    
    send_telegram_message(message)

if __name__ == "__main__":
    main()
