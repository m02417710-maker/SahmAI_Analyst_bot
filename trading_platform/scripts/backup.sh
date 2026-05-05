#!/bin/bash
# ملف: scripts/backup.sh
# المسار: /trading_platform/scripts/backup.sh
# الوظيفة: عمل نسخة احتياطية تلقائية

set -e

# الألوان للإخراج
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  نظام النسخ الاحتياطي - منصة التداول${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# إعدادات
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="trading_backup_${DATE}"
TEMP_DIR="/tmp/${BACKUP_NAME}"

# إنشاء المجلدات
mkdir -p ${BACKUP_DIR}
mkdir -p ${TEMP_DIR}

echo -e "${YELLOW}📁 إنشاء مجلد مؤقت: ${TEMP_DIR}${NC}"

# 1. نسخ قاعدة البيانات
echo -e "${YELLOW}💾 نسخ قاعدة البيانات...${NC}"
docker-compose exec -T timescaledb pg_dump -U trader trading_db > ${TEMP_DIR}/database.sql
echo -e "${GREEN}✅ تم نسخ قاعدة البيانات${NC}"

# 2. نسخ بيانات Redis
echo -e "${YELLOW}📊 نسخ بيانات Redis...${NC}"
docker-compose exec -T redis redis-cli --rdb /tmp/dump.rdb
docker cp $(docker-compose ps -q redis):/tmp/dump.rdb ${TEMP_DIR}/redis_dump.rdb
echo -e "${GREEN}✅ تم نسخ Redis${NC}"

# 3. نسخ السجلات
echo -e "${YELLOW}📝 نسخ السجلات...${NC}"
cp -r logs ${TEMP_DIR}/logs 2>/dev/null || echo "لا توجد سجلات"
echo -e "${GREEN}✅ تم نسخ السجلات${NC}"

# 4. نسخ الإعدادات
echo -e "${YELLOW}⚙️ نسخ الإعدادات...${NC}"
cp .env ${TEMP_DIR}/.env.backup 2>/dev/null || echo "لا يوجد ملف .env"
cp -r config ${TEMP_DIR}/config 2>/dev/null || echo "لا يوجد مجلد config"
echo -e "${GREEN}✅ تم نسخ الإعدادات${NC}"

# 5. نسخ النماذج المدربة
echo -e "${YELLOW}🧠 نسخ النماذج المدربة...${NC}"
cp -r backend/models ${TEMP_DIR}/models 2>/dev/null || echo "لا توجد نماذج"
echo -e "${GREEN}✅ تم نسخ النماذج${NC}"

# 6. إنشاء ملف المعلومات
cat > ${TEMP_DIR}/backup_info.txt << EOF
معلومات النسخة الاحتياطية
==========================
التاريخ: $(date)
المنصة: Trading Platform 4.0
البيانات المضمنة:
- قاعدة البيانات (PostgreSQL/TimescaleDB)
- بيانات Redis
- السجلات (logs)
- الإعدادات (.env, config)
- النماذج المدربة (models)

حجم النسخة: $(du -sh ${TEMP_DIR} | cut -f1)
EOF

# 7. ضغط النسخة
echo -e "${YELLOW}🗜️ ضغط النسخة الاحتياطية...${NC}"
cd /tmp
tar -czf ${BACKUP_NAME}.tar.gz ${BACKUP_NAME}
mv ${BACKUP_NAME}.tar.gz ${OLDPWD}/${BACKUP_DIR}/
cd ${OLDPWD}

# 8. تنظيف
echo -e "${YELLOW}🧹 تنظيف الملفات المؤقتة...${NC}"
rm -rf ${TEMP_DIR}

# 9. حذف النسخ القديمة (احتفظ بآخر 30 نسخة)
echo -e "${YELLOW}🗑️ حذف النسخ القديمة...${NC}"
cd ${BACKUP_DIR}
ls -t *.tar.gz | tail -n +31 | xargs -r rm -f
cd ..

# 10. عرض النتيجة
BACKUP_SIZE=$(du -sh ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz | cut -f1)
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ تم إنشاء النسخة الاحتياطية بنجاح!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "📦 اسم الملف: ${YELLOW}${BACKUP_NAME}.tar.gz${NC}"
echo -e "📏 الحجم: ${YELLOW}${BACKUP_SIZE}${NC}"
echo -e "📂 الموقع: ${YELLOW}${BACKUP_DIR}/${BACKUP_NAME}.tar.gz${NC}"
echo ""
echo -e "🔄 لاستعادة النسخة:"
echo -e "   ${GREEN}./scripts/restore.sh ${BACKUP_NAME}.tar.gz${NC}"
echo ""
