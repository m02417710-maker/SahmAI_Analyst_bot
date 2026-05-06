#!/bin/bash
# ملف: deploy_complete.sh
# التشغيل الكامل والمتكامل

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║     🏆 منصة التداول المتكاملة - التشغيل الكامل 🏆          ║"
echo "║                     Trading Platform 4.0                     ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 1. فحص المتطلبات
check_requirements() {
    echo -e "${YELLOW}🔍 فحص المتطلبات...${NC}"
    
    commands=("docker" "docker-compose" "python3" "git" "curl")
    for cmd in "${commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            echo -e "${RED}❌ $cmd غير مثبت${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✅ جميع المتطلبات موجودة${NC}"
    echo ""
}

# 2. إعداد البيئة
setup_environment() {
    echo -e "${YELLOW}📝 إعداد البيئة...${NC}"
    
    if [ ! -f .env ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️ تم إنشاء ملف .env${NC}"
        echo -e "${YELLOW}   يرجى تعديله وإضافة مفاتيح API${NC}"
        read -p "اضغط Enter بعد تعديل الملف..."
    fi
    
    # إنشاء المجلدات المطلوبة
    mkdir -p logs models backups ssl certbot/www
    
    echo -e "${GREEN}✅ تم إعداد البيئة${NC}"
    echo ""
}

# 3. بناء الصور
build_images() {
    echo -e "${YELLOW}🏗️ بناء صور Docker...${NC}"
    docker-compose -f docker-compose.full.yml build --no-cache
    echo -e "${GREEN}✅ تم بناء الصور${NC}"
    echo ""
}

# 4. تشغيل الخدمات
start_services() {
    echo -e "${YELLOW}🚀 تشغيل الخدمات...${NC}"
    docker-compose -f docker-compose.full.yml up -d
    echo -e "${GREEN}✅ تم تشغيل جميع الخدمات${NC}"
    echo ""
}

# 5. انتظار الخدمات
wait_for_services() {
    echo -e "${YELLOW}⏳ انتظار الخدمات للبدء...${NC}"
    sleep 15
    
    # فحص صحة الخدمات
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null; then
            echo -e "${GREEN}✅ Backend يعمل${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Backend لا يعمل${NC}"
            exit 1
        fi
        sleep 2
    done
    
    echo ""
}

# 6. تهيئة البيانات
initialize_data() {
    echo -e "${YELLOW}📊 تهيئة البيانات...${NC}"
    docker-compose exec backend python scripts/init_data.py
    echo -e "${GREEN}✅ تم تهيئة البيانات${NC}"
    echo ""
}

# 7. إنشاء المستخدم المسؤول
create_admin() {
    echo -e "${YELLOW}👑 إنشاء مستخدم مسؤول...${NC}"
    docker-compose exec backend python scripts/create_admin.py
    echo ""
}

# 8. بدء المسابقات
start_competitions() {
    echo -e "${YELLOW}🏆 بدء المسابقات...${NC}"
    docker-compose exec backend python scripts/start_competitions.py
    echo -e "${GREEN}✅ تم بدء المسابقات${NC}"
    echo ""
}

# 9. عرض المعلومات
show_info() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              ✅ تم تشغيل المنصة بنجاح! ✅                     ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo -e "${BLUE}📍 الروابط:${NC}"
    echo -e "   • واجهة المستخدم: ${GREEN}http://localhost${NC}"
    echo -e "   • لوحة المسؤول: ${GREEN}http://localhost/admin${NC}"
    echo -e "   • توثيق API: ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "   • Grafana: ${GREEN}http://localhost:3000${NC} (admin/${GRAFANA_PASSWORD:-admin})"
    echo -e "   • Prometheus: ${GREEN}http://localhost:9090${NC}"
    echo ""
    echo -e "${BLUE}📱 تطبيق الموبايل:${NC}"
    echo -e "   • ${GREEN}cd mobile && flutter run${NC}"
    echo ""
    echo -e "${BLUE}🤖 بوت التليجرام:${NC}"
    echo -e "   • ابحث عن: ${GREEN}@TradingPlatformBot${NC}"
    echo ""
    echo -e "${BLUE}📚 المنصة التعليمية:${NC}"
    echo -e "   • ${GREEN}http://localhost/learning${NC}"
    echo ""
    echo -e "${BLUE}🏆 المسابقات:${NC}"
    echo -e "   • ${GREEN}http://localhost/competitions${NC}"
    echo ""
    echo -e "${BLUE}📝 الأوامر المتاحة:${NC}"
    echo -e "   • ${GREEN}make logs${NC} - عرض السجلات"
    echo -e "   • ${GREEN}make down${NC} - إيقاف الخدمات"
    echo -e "   • ${GREEN}make backup${NC} - نسخ احتياطي"
    echo -e "   • ${GREEN}make monitor${NC} - مراقبة النظام"
    echo ""
    echo -e "${YELLOW}⚠️ تنبيهات أمنية:${NC}"
    echo -e "   • قم بتغيير كلمة مرور المسؤول فوراً"
    echo -e "   • أضف مفاتيح SSL للإنتاج الحقيقي"
    echo -e "   • قم بتفعيل الـ Firewall"
    echo -e "   • قم بعمل نسخ احتياطية بشكل دوري"
    echo ""
}

# 10. فتح المتصفح
open_browser() {
    read -p "هل تريد فتح المتصفح الآن؟ (y/n): " open
    if [ "$open" = "y" ]; then
        if command -v xdg-open &> /dev/null; then
            xdg-open http://localhost
        elif command -v open &> /dev/null; then
            open http://localhost
        else
            echo -e "${YELLOW}افتح المتصفح يدوياً: http://localhost${NC}"
        fi
    fi
}

# ====================== التنفيذ الرئيسي ======================
main() {
    check_requirements
    setup_environment
    build_images
    start_services
    wait_for_services
    initialize_data
    create_admin
    start_competitions
    show_info
    open_browser
}

# تشغيل
main
# بعد تنفيذ جميع الملفات، قم بتشغيل الأمر التالي:

chmod +x deploy_complete.sh
./deploy_complete.sh
# 1. ارفع الملفات إلى GitHub
git add .github/ scripts/ utils/
git commit -m "🤖 إضافة نظام الأتمتة الكامل"
git push origin main

# 2. أضف Secrets في GitHub:
#    - GEMINI_API_KEY
#    - TELEGRAM_TOKEN
#    - TELEGRAM_CHAT_ID

# 3. شاهد النظام يعمل تلقائياً!
