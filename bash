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
