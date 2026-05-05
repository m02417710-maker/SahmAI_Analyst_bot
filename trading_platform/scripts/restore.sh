#!/bin/bash
# ملف: scripts/restore.sh
# المسار: /trading_platform/scripts/restore.sh
# الوظيفة: استعادة نسخة احتياطية

set -e

# الألوان للإخراج
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# التحقق من المعاملات
if [ -z "$1" ]; then
    echo -e "${RED}❌ يرجى تحديد ملف النسخة الاحتياطية${NC}"
    echo -e "الاستخدام: $0 <backup_file.tar.gz>"
    exit 1
fi

BACKUP_FILE=$1
BACKUP_DIR="./backups"
TEMP_DIR="/tmp/restore_$(date +%Y%m%d_%H%M%S)"

if [ ! -f "${BACKUP_DIR}/${BACKUP_FILE}" ] && [ ! -f "${BACKUP_FILE}" ]; then
    echo -e "${RED}❌ الملف ${BACKUP_FILE} غير موجود${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  استعادة النسخة الاحتياطية${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# تأكيد الاستعادة
echo -e "${YELLOW}⚠️ تحذير: هذه العملية ستحذف البيانات الحالية!${NC}"
read -p "هل أنت متأكد من المتابعة؟ (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo -e "${RED}❌ تم إلغاء العملية${NC}"
    exit 1
fi

# إنشاء مجلد مؤقت
mkdir -p ${TEMP_DIR}
echo -e "${YELLOW}📁 إنشاء مجلد مؤقت: ${TEMP_DIR}${NC}"

# فك الضغط
echo -e "${YELLOW}📦 فك ضغط الملف...${NC}"
if [ -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
    tar -xzf "${BACKUP_DIR}/${BACKUP_FILE}" -C ${TEMP_DIR}
else
    tar -xzf "${BACKUP_FILE}" -C ${TEMP_DIR}
fi

# العثور على المجلد المستخرج
EXTRACTED_DIR=$(find ${TEMP_DIR} -name "trading_backup_*" -type d | head -1)

if [ -z "${EXTRACTED_DIR}" ]; then
    echo -e "${RED}❌ فشل في فك الضغط${NC}"
    exit 1
fi

echo -e "${GREEN}✅ تم فك الضغط إلى: ${EXTRACTED_DIR}${NC}"

# إيقاف الخدمات
echo -e "${YELLOW}🛑 إيقاف الخدمات...${NC}"
docker-compose down

# استعادة قاعدة البيانات
echo -e "${YELLOW}💾 استعادة قاعدة البيانات...${NC}"
docker-compose up -d timescaledb
sleep 5
docker-compose exec -T timescaledb psql -U trader -d postgres -c "DROP DATABASE IF EXISTS trading_db;"
docker-compose exec -T timescaledb psql -U trader -d postgres -c "CREATE DATABASE trading_db;"
docker-compose exec -T timescaledb psql -U trader -d trading_db < ${EXTRACTED_DIR}/database.sql
echo -e "${GREEN}✅ تم استعادة قاعدة البيانات${NC}"

# استعادة Redis
if [ -f "${EXTRACTED_DIR}/redis_dump.rdb" ]; then
    echo -e "${YELLOW}📊 استعادة Redis...${NC}"
    docker cp ${EXTRACTED_DIR}/redis_dump.rdb $(docker-compose ps -q redis):/data/dump.rdb
    docker-compose restart redis
    echo -e "${GREEN}✅ تم استعادة Redis${NC}"
fi

# استعادة الإعدادات
if [ -f "${EXTRACTED_DIR}/.env.backup" ]; then
    echo -e "${YELLOW}⚙️ استعادة الإعدادات...${NC}"
    cp ${EXTRACTED_DIR}/.env.backup .env
    echo -e "${GREEN}✅ تم استعادة الإعدادات${NC}"
fi

# استعادة النماذج
if [ -d "${EXTRACTED_DIR}/models" ]; then
    echo -e "${YELLOW}🧠 استعادة النماذج...${NC}"
    cp -r ${EXTRACTED_DIR}/models backend/
    echo -e "${GREEN}✅ تم استعادة النماذج${NC}"
fi

# إعادة تشغيل جميع الخدمات
echo -e "${YELLOW}🚀 إعادة تشغيل الخدمات...${NC}"
docker-compose up -d

# تنظيف
echo -e "${YELLOW}🧹 تنظيف...${NC}"
rm -rf ${TEMP_DIR}

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ تم استعادة النسخة الاحتياطية بنجاح!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "📋 تم استعادة:"
echo -e "   • قاعدة البيانات"
echo -e "   • بيانات Redis"
echo -e "   • الإعدادات"
echo -e "   • النماذج المدربة"
echo ""
echo -e "🌐 يمكنك الآن فتح التطبيق: http://localhost"
echo ""
