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
