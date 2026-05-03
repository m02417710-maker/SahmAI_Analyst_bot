# 1. إنشاء المجلد الرئيسي للمشروع
mkdir stock-egypt-analyst
cd stock-egypt-analyst

# 2. إنشاء الهيكل الداخلي
mkdir -p .streamlit
mkdir -p assets
mkdir -p utils

# 3. إنشاء الملفات الأساسية
touch app.py
touch requirements.txt
touch README.md
touch .gitignore
touch .streamlit/secrets.toml
cp .env.example .env
# قم بتعديل .env وأضف مفاتيح API الخاصة بك
docker-compose up -d
# تشغيل جميع الخدمات
docker-compose up -d

# تشغيل خدمة محددة
docker-compose up backend

# إيقاف الخدمات
docker-compose down

# عرض السجلات
docker-compose logs -f backend
# تحديث بيانات السوق يدوياً
curl -X POST http://localhost:8000/api/market/update

# إعادة حساب المؤشرات
curl -X POST http://localhost:8000/api/indicators/recalculate
curl "http://localhost:8000/api/stock/COMI.CA"
curl "http://localhost:8000/api/market/opportunities"
curl "http://localhost:8000/api/search/الراجحي"
# تشغيل اختبارات الوحدة
pytest backend/tests/

# اختبار الأداء
locust -f tests/load_test.py
# 1. سحب المشروع
git clone https://github.com/yourusername/trading_platform.git
cd trading_platform

# 2. إعداد البيئة
cp .env.example .env
# - أضف GEMINI_API_KEY
# - أضف TELEGRAM_TOKEN

# 3. تشغيل جميع الخدمات
docker-compose up -d

# 4. التحقق من الخدمات
docker-compose ps

# 5. الوصول إلى:
# - واجهة الويب: http://localhost
# - API docs: http://localhost:8000/docs
# - Grafana: http://localhost:3000 (admin/admin)
# - Prometheus: http://localhost:9090

# 6. مشاهدة السجلات
docker-compose logs -f auto_trader
docker-compose logs -f sentiment_agent
# 1. إضافة المتغيرات الجديدة إلى .env
echo """
# Stripe API Keys (للدعم)
STRIPE_PUBLIC_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Tax Settings
TAX_RATE=0.225
TAX_AUTHORITY_ID=123456

# Admin Settings
ADMIN_EMAIL=admin@trading-platform.com
ADMIN_PASSWORD_HASH=xxx
""" >> .env

# 2. إعادة بناء وتشغيل جميع الخدمات
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 3. إنشاء مستخدم مسؤول
docker-compose exec backend python scripts/create_admin.py

# 4. التحقق من جميع الخدمات
docker-compose ps
docker-compose logs -f --tail=50

# 5. فتح لوحة التحكم
echo """
✅ المنصة جاهزة للتشغيل!

🔗 الروابط:
- تطبيق الويب: http://localhost
- لوحة تحكم المسؤول: http://localhost/admin
- توثيق API: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

📱 تطبيق الموبايل:
- flutter run lib/main.dart

🤖 بوت التليجرام:
- ابحث عن @TradingPlatformBot

💰 نظام الاشتراكات:
- مجاني: 0 ج.م
- أساسي: 99 ج.م/شهر
- احترافي: 299 ج.م/شهر
- بريميوم: 599 ج.م/شهر
- مؤسسات: 1499 ج.م/شهر
"""
