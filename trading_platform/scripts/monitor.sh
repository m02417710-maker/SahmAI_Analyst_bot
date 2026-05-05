#!/bin/bash
# ملف: scripts/monitor.sh
# المسار: /trading_platform/scripts/monitor.sh
# الوظيفة: مراقبة أداء المنصة

#!/bin/bash

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  مراقبة منصة التداول - لوحة المعلومات${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# وقت التشغيل
echo -e "${YELLOW}⏰ وقت التشغيل:${NC}"
uptime
echo ""

# Docker containers
echo -e "${YELLOW}🐳 حالة الحاويات:${NC}"
docker-compose ps
echo ""

# استخدام الموارد
echo -e "${YELLOW}📊 استخدام الموارد:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo ""

# فحص صحة API
echo -e "${YELLOW}🔍 فحص صحة API:${NC}"
HEALTH=$(curl -s http://localhost:8000/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ API يعمل بشكل طبيعي${NC}"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo -e "${RED}❌ API لا يستجيب${NC}"
fi
echo ""

# إحصائيات قاعدة البيانات
echo -e "${YELLOW}💾 إحصائيات قاعدة البيانات:${NC}"
docker-compose exec -T timescaledb psql -U trader -d trading_db -c "
SELECT 
    (SELECT COUNT(*) FROM stock_prices) as stock_records,
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM subscriptions) as active_subscriptions;
" 2>/dev/null || echo "لا يمكن الاتصال بقاعدة البيانات"
echo ""

# استخدام Redis
echo -e "${YELLOW}📡 إحصائيات Redis:${NC}"
docker-compose exec -T redis redis-cli INFO stats | grep -E "total_connections_received|total_commands_processed" 2>/dev/null || echo "لا يمكن الاتصال بـ Redis"
echo ""

# السجلات الحديثة
echo -e "${YELLOW}📝 آخر 10 سجلات خطأ:${NC}"
docker-compose logs --tail=10 backend 2>/dev/null | grep -i error || echo "لا توجد أخطاء حديثة"
echo ""

# مساحة القرص
echo -e "${YELLOW}💿 مساحة القرص:${NC}"
df -h / | awk 'NR==2 {print "المستخدم: " $3 " / " $2 " (" $5 ")"}'
echo ""

# عدد الطلبات
echo -e "${YELLOW}📈 إحصائيات API:${NC}"
if [ -f logs/access.log ]; then
    TOTAL_REQUESTS=$(wc -l < logs/access.log)
    TODAY_REQUESTS=$(grep "$(date +%Y-%m-%d)" logs/access.log | wc -l)
    echo "   • إجمالي الطلبات: $TOTAL_REQUESTS"
    echo "   • طلبات اليوم: $TODAY_REQUESTS"
else
    echo "   • لا توجد سجلات وصول"
fi
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ انتهت المراقبة${NC}"
echo -e "${BLUE}========================================${NC}"
