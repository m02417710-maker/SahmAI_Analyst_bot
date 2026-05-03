# ملف: backend/Dockerfile
# المسار: /trading_platform/backend/Dockerfile

FROM python:3.10-slim

# تعيين متغيرات البيئة
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Africa/Cairo

# تثبيت الاعتماديات
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# إنشاء مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات
COPY requirements.txt .

# تثبيت متطلبات Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# إنشاء مجلدات ضرورية
RUN mkdir -p /app/logs
RUN mkdir -p /app/cache

# فتح المنفذ
EXPOSE 8000

# أمر التشغيل
CMD ["python", "main.py"]
