#!/bin/bash
# ملف: scripts/ssl_renew.sh
# المسار: /trading_platform/scripts/ssl_renew.sh
# الوظيفة: تجديد شهادات SSL تلقائياً

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  تجديد شهادات SSL${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# إيقاف Nginx مؤقتاً
echo -e "${YELLOW}🛑 إيقاف Nginx...${NC}"
docker-compose stop nginx

# تجديد الشهادة
echo -e "${YELLOW}🔑 تجديد الشهادة...${NC}"
certbot renew --standalone --preferred-challenges http

# نسخ الشهادات الجديدة
echo -e "${YELLOW}📁 نسخ الشهادات...${NC}"
cp /etc/letsencrypt/live/trading-platform.com/fullchain.pem ./ssl/
cp /etc/letsencrypt/live/trading-platform.com/privkey.pem ./ssl/

# إعادة تشغيل Nginx
echo -e "${YELLOW}🚀 إعادة تشغيل Nginx...${NC}"
docker-compose start nginx

echo -e "${GREEN}✅ تم تجديد الشهادات بنجاح!${NC}"
