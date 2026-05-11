# 📊 محلل الأسهم - البورصة المصرية
## Advanced Stock Analysis Platform for Egyptian Exchange

> منصة متقدمة لتحليل الأسهم والبورصة المصرية مع مؤشرات فنية وتنبيهات ذكية وإدارة محفظة

---

## ✨ المميزات الرئيسية

### 📈 تحليل متقدم
- **مؤشرات فنية متقدمة**: SMA, EMA, RSI, MACD, Bollinger Bands
- **مؤشرات أساسية**: P/E, EPS, عائد التوزيع، معامل بيتا
- **رسوم بيانية تفاعلية**: شموع، أعمدة، خطوط
- **فترات زمنية متعددة**: يومي، أسبوعي، شهري، سنوي

### 🔔 نظام التنبيهات الذكي
- تنبيهات السعر والتغيرات
- تنبيهات فنية (تقاطع متوسطات، RSI)
- تنبيهات أساسية (أرباح، توزيعات)
- قنوات متعددة: داخل التطبيق، بريد إلكتروني، SMS

### 💼 إدارة المحفظة
- تتبع شامل للأسهم المملوكة
- حساب العائد والخسارة تلقائياً
- توزيع المحفظة بصرياً
- توصيات إعادة التوازن

### 📊 التقارير والتحليلات
- تقارير دورية (يومية، أسبوعية، شهرية، سنوية)
- تحليلات القطاعات
- توقعات الأداء
- مقارن الأسهم المتقدم

### 🔒 الأمان والخصوصية
- مصادقة آمنة مع JWT
- تشفير البيانات الحساسة
- حماية من الهجمات الشائعة
- سياسة خصوصية صارمة

---

## 🚀 البدء السريع

### المتطلبات
- **Node.js** v18+
- **PostgreSQL** v12+
- **Redis** v6+
- **Docker** (موصى به)

### التثبيت

```bash
# استنساخ المستودع
git clone https://github.com/yourname/stock-analyzer.git
cd stock-analyzer

# تثبيت المتعلقات
npm install
cd client && npm install && cd ..

# إعداد البيئة
cp .env.example .env

# تشغيل مع Docker
docker-compose up -d

# أو التشغيل المحلي
npm run dev
```

### الوصول
- **التطبيق**: http://localhost:3000
- **API**: http://localhost:5000/api
- **قاعدة البيانات**: localhost:5432

---

## 📁 هيكل المشروع

```
stock-analyzer/
├── server/                  # الخادم الخلفي
│   ├── routes/             # مسارات API
│   ├── controllers/        # معالجات الطلبات
│   ├── models/             # نماذج قاعدة البيانات
│   ├── middleware/         # وسيط المصادقة والتحقق
│   ├── services/           # منطق الأعمال
│   └── utils/              # وظائف مساعدة
├── client/                  # التطبيق الأمامي
│   ├── src/
│   │   ├── components/     # مكونات React
│   │   ├── pages/          # الصفحات
│   │   ├── redux/          # إدارة الحالة
│   │   ├── api/            # خدمات API
│   │   ├── utils/          # وظائف مساعدة
│   │   └── styles/         # أنماط CSS
├── docs/                    # التوثيق
├── tests/                   # الاختبارات
├── docker-compose.yml       # إعدادات Docker
├── .env.example             # متغيرات البيئة
└── README.md               # هذا الملف
```

---

## 📚 التوثيق

### أدلة التطبيق
- **[دليل التطوير](./docs/DEVELOPMENT.md)** - معلومات تفصيلية عن البيئة والإعداد
- **[دليل API](./docs/API.md)** - جميع نقاط النهاية والمعاملات
- **[دليل المساهمة](./CONTRIBUTING.md)** - كيفية المساهمة في المشروع
- **[سجل التغييرات](./CHANGELOG.md)** - تتبع التحديثات والإصلاحات

### وثائق أخرى
- [خطة التطوير الشاملة](./docs/Development_Plan.docx)
- [الدليل التقني للنشر](./docs/Technical_Implementation_Guide.docx)
- [مخطط المعمارية](./docs/Architecture.md)

---

## 🔌 API نقاط النهاية الرئيسية

### الأسهم
```
GET    /api/stocks                    # قائمة الأسهم
GET    /api/stocks/:id                # تفاصيل السهم
GET    /api/stocks/:id/technicals     # المؤشرات الفنية
GET    /api/stocks/:id/history        # البيانات التاريخية
```

### التنبيهات
```
POST   /api/alerts                    # إنشاء تنبيه
GET    /api/alerts                    # قائمة التنبيهات
PUT    /api/alerts/:id                # تحديث التنبيه
DELETE /api/alerts/:id                # حذف التنبيه
```

### المحفظة
```
POST   /api/portfolio                 # إضافة سهم
GET    /api/portfolio                 # بيانات المحفظة
PUT    /api/portfolio/:id             # تحديث المشاركة
DELETE /api/portfolio/:id             # إزالة السهم
```

### التقارير
```
GET    /api/reports/daily             # التقرير اليومي
GET    /api/reports/weekly            # التقرير الأسبوعي
GET    /api/reports/monthly           # التقرير الشهري
GET    /api/reports/analysis          # تحليل شامل
```

---

## 🛠️ أدوات التطوير

### البناء والاختبار
```bash
# بناء الإنتاج
npm run build

# تشغيل الاختبارات
npm test

# اختبارات التغطية
npm run test:coverage

# اختبارات E2E
npm run test:e2e
```

### المراقبة والسجلات
```bash
# عرض السجلات
docker-compose logs -f

# قاعدة البيانات
psql -U postgres -d stock_analyzer

# Redis
redis-cli
```

---

## 📊 نموذج البيانات الرئيسي

### Users (المستخدمون)
```
- id: UUID
- email: string (فريد)
- password: hashed string
- fullName: string
- createdAt: timestamp
```

### Stocks (الأسهم)
```
- id: UUID
- code: string (رمز السهم)
- name: string
- currentPrice: decimal
- change: decimal
- changePercent: decimal
- volume: integer
- marketCap: decimal
- lastUpdated: timestamp
```

### Alerts (التنبيهات)
```
- id: UUID
- userId: UUID
- stockId: UUID
- type: enum (PRICE, TECHNICAL, FUNDAMENTAL)
- condition: string
- targetValue: decimal
- isActive: boolean
- channels: array
- createdAt: timestamp
```

### Portfolio (المحفظة)
```
- id: UUID
- userId: UUID
- stockId: UUID
- quantity: integer
- purchasePrice: decimal
- purchaseDate: date
- currentValue: decimal
- totalReturn: decimal
```

---

## 🔐 الأمان

### أفضل الممارسات
✅ تشفير كل البيانات الحساسة  
✅ مصادقة JWT مع فترات انتهاء صلاحية
✅ Rate limiting على جميع APIs  
✅ Validation وتنظيف جميع المدخلات  
✅ استخدام HTTPS/TLS  
✅ CORS مُحكّم  
✅ SQL injection prevention  
✅ XSS protection  

### المفاتيح والسرية
- احتفظ بـ `.env` آمنة ولا تنسخها إلى الإنتاج
- استخدم بيئات آمنة لتخزين المفاتيح
- أدوِّر المفاتيح بانتظام
- سجّل جميع الوصولات الحساسة

---

## 📈 الأداء

### تحسينات التخزين المؤقت
- Redis للبيانات اللحظية
- CDN للملفات الثابتة
- تحميل كسول للبيانات الثقيلة

### اختبارات الحمل
- استهداف: 10,000 مستخدم متزامن
- وقت الاستجابة: < 500ms
- معدل التوفر: > 99.5%

---

## 📱 الأنظمة المدعومة

- ✅ Web (React - جميع المتصفحات الحديثة)
- 🔄 Mobile (قادم - React Native)
- 📱 iOS App (قادم)
- 🤖 Android App (قادم)
- 📦 Desktop (قادم - Electron)

---

## 💡 الخارطة الطريقية

### Q1 2025
- ✅ البنية الأساسية والـ MVP
- ⬜ المؤشرات الفنية المتقدمة
- ⬜ نظام التنبيهات الكامل

### Q2 2025
- ⬜ تطبيق الجوال (iOS/Android)
- ⬜ التقارير والتحليلات المتقدمة
- ⬜ واجهة API عامة

### Q3-Q4 2025
- ⬜ الذكاء الاصطناعي والتنبؤ
- ⬜ دعم العملات الرقمية
- ⬜ تكامل مع منصات أخرى

---

## 🤝 المساهمة

نرحب بمساهماتك! اطلع على [دليل المساهمة](./CONTRIBUTING.md) للتفاصيل.

```bash
# خطوات المساهمة
1. fork المستودع
2. أنشئ فرع ميزة (git checkout -b feature/amazing-feature)
3. اكتب الكود والاختبارات
4. اعمل commit (git commit -m 'Add amazing feature')
5. ادفع (git push origin feature/amazing-feature)
6. افتح Pull Request
```

---

## 📄 الترخيص

هذا المشروع مرخص تحت [MIT License](./LICENSE) - اطلع على الملف للتفاصيل.

---

## 📞 التواصل والدعم

- **البريد الإلكتروني**: support@stockanalyzer.eg
- **تويتر**: [@StockAnalyzerEG](https://twitter.com/StockAnalyzerEG)
- **GitHub Issues**: [Report a bug](https://github.com/yourname/stock-analyzer/issues)
- **الموقع الرسمي**: [www.stockanalyzer.eg](https://www.stockanalyzer.eg)

---

## 👥 الفريق

| الاسم | الدور | GitHub |
|------|------|--------|
| محمد أحمد | المدير | [@your-github](https://github.com) |
| فاطمة علي | مطور أمامي | [@your-github](https://github.com) |
| علي محمود | مطور خلفي | [@your-github](https://github.com) |

---

## 🙏 شكر وتقدير

شكر خاص إلى:
- فريق عمل البورصة المصرية
- المساهمين والداعمين
- مجتمع المطورين المصري

---

## 📊 الإحصائيات

![GitHub stars](https://img.shields.io/github/stars/yourname/stock-analyzer)
![GitHub forks](https://img.shields.io/github/forks/yourname/stock-analyzer)
![GitHub issues](https://img.shields.io/github/issues/yourname/stock-analyzer)
![License](https://img.shields.io/badge/license-MIT-blue)
![Node version](https://img.shields.io/badge/node-v18%2B-green)
![React version](https://img.shields.io/badge/react-v18%2B-blue)

---

## 📝 ملاحظات مهمة

⚠️ **تحذير**: هذا التطبيق لأغراض تعليمية وإعلامية فقط. لا يشكل نصيحة استثمارية.

📌 **المسؤولية**: المستخدمون مسؤولون بالكامل عن قراراتهم الاستثمارية.

🔄 **التحديثات**: البيانات قد لا تكون فورية بنسبة 100%. يجب التحقق من المصادر الرسمية.

---

**آخر تحديث**: يناير 2025  
**الإصدار**: 1.0.0-beta
