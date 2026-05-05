# ملف: Makefile
# المسار: /trading_platform/Makefile

.PHONY: help install dev build prod up down logs clean test backup restore

help:
	@echo "📋 أوامر منصة التداول:"
	@echo ""
	@echo "  make install     - تثبيت المتطلبات"
	@echo "  make dev         - تشغيل بيئة التطوير"
	@echo "  make build       - بناء الصور"
	@echo "  make prod        - تشغيل بيئة الإنتاج"
	@echo "  make up          - تشغيل الخدمات"
	@echo "  make down        - إيقاف الخدمات"
	@echo "  make logs        - عرض السجلات"
	@echo "  make clean       - تنظيف الملفات المؤقتة"
	@echo "  make test        - تشغيل الاختبارات"
	@echo "  make backup      - عمل نسخة احتياطية"
	@echo "  make restore     - استعادة نسخة احتياطية"

install:
	@echo "📦 تثبيت المتطلبات..."
	pip install -r backend/requirements.txt
	cd mobile && flutter pub get
	cd frontend && npm install

dev:
	@echo "🚀 تشغيل بيئة التطوير..."
	docker-compose up

build:
	@echo "🏗️ بناء الصور..."
	docker-compose build --no-cache

prod:
	@echo "🏭 تشغيل بيئة الإنتاج..."
	docker-compose -f docker-compose.prod.yml up -d

up:
	@echo "▶️ تشغيل الخدمات..."
	docker-compose up -d

down:
	@echo "⏹️ إيقاف الخدمات..."
	docker-compose down

logs:
	@echo "📄 عرض السجلات..."
	docker-compose logs -f

clean:
	@echo "🧹 تنظيف الملفات المؤقتة..."
	docker-compose down -v
	docker system prune -f
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".cache" -exec rm -rf {} +
	find . -type d -name "logs" -exec rm -rf {} +

test:
	@echo "🧪 تشغيل الاختبارات..."
	pytest backend/tests/ -v

backup:
	@echo "💾 عمل نسخة احتياطية..."
	./scripts/backup.sh

restore:
	@echo "🔄 استعادة نسخة احتياطية..."
	./scripts/restore.sh

status:
	@echo "📊 حالة الخدمات..."
	docker-compose ps

shell:
	@echo "🐚 الدخول إلى shell الخلفية..."
	docker-compose exec backend bash

init:
	@echo "📋 تهيئة البيانات..."
	docker-compose exec backend python scripts/init_data.py

admin:
	@echo "👑 إنشاء مستخدم مسؤول..."
	docker-compose exec backend python scripts/create_admin.py

competitions:
	@echo "🏆 بدء المسابقات..."
	docker-compose exec backend python scripts/start_competitions.py

update:
	@echo "🔄 تحديث التطبيق..."
	git pull
	docker-compose build
	docker-compose up -d
	docker-compose exec backend python scripts/migrate.py

monitor:
	@echo "📊 فتح مراقبة Grafana..."
	open http://localhost:3000

api-docs:
	@echo "📖 فتح توثيق API..."
	open http://localhost:8000/docs
