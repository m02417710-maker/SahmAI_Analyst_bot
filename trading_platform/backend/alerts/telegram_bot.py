"""
ملف: backend/alerts/telegram_bot.py
المسار: /trading_platform/backend/alerts/telegram_bot.py
الوظيفة: بوت تليجرام متقدم للتنبيهات والتقارير التفاعلية
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from loguru import logger

class TradingTelegramBot:
    """بوت تليجرام المتكامل لمنصة التداول"""
    
    def __init__(self, token: str, trading_agent):
        self.token = token
        self.trading_agent = trading_agent
        self.application = None
        self.user_alerts = {}  # تخزين تنبيهات المستخدمين
        self.user_portfolios = {}  # محافظ المستخدمين
        
    async def initialize(self):
        """تهيئة البوت"""
        self.application = Application.builder().token(self.token).build()
        
        # تسجيل المعالجات
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("report", self.report_command))
        self.application.add_handler(CommandHandler("analyze", self.analyze_command))
        self.application.add_handler(CommandHandler("portfolio", self.portfolio_command))
        self.application.add_handler(CommandHandler("alert", self.alert_command))
        
        # معالج الأزرار
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # معالج الرسائل
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("✅ تم تهيئة بوت التليجرام")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /start"""
        user = update.effective_user
        
        welcome_text = f"""
🚀 **مرحباً بك {user.first_name}!**

أنا **بوت التحليل الاستثماري الذكي** لمنصة التداول.

📊 **ماذا يمكنني أن أقدم لك؟**

• 📈 **تحليل فني متقدم** للأسهم المصرية والسعودية والأمريكية
• 🔍 **اكتشاف فرص استثمارية** باستخدام الذكاء الاصطناعي
• 📊 **تقرير يومي** شامل عن أفضل الفرص
• 💼 **إدارة محفظتك** ومتابعة أدائها
• 🔔 **تنبيهات فورية** عند تغيرات الأسعار

📌 **الأوامر المتاحة:**
/report - تقرير يومي شامل
/analyze <رمز> - تحليل سهم محدد
/portfolio - إدارة محفظتك
/alert - تفعيل التنبيهات
/help - المساعدة

**ابدأ الآن باختيار الخدمة المناسبة لك!**
        """
        
        keyboard = [
            [InlineKeyboardButton("📈 تقرير اليوم", callback_data='daily_report')],
            [InlineKeyboardButton("🔍 تحليل سهم", callback_data='analyze_stock')],
            [InlineKeyboardButton("💼 محفظتي", callback_data='my_portfolio')],
            [InlineKeyboardButton("🔔 إدارة التنبيهات", callback_data='manage_alerts')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /report - إرسال التقرير اليومي"""
        await update.message.reply_text("📊 **جاري إنشاء التقرير اليومي...**", parse_mode='Markdown')
        
        # توليد التقرير من الوكيل الذكي
        report = await self.trading_agent.generate_daily_report()
        
        # تقسيم التقرير إذا كان طويلاً
        if len(report) > 4000:
            parts = [report[i:i+4000] for i in range(0, len(report), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(report, parse_mode='Markdown')
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /analyze <symbol>"""
        # استخراج رمز السهم من الأمر
        args = context.args
        if not args:
            await update.message.reply_text(
                "⚠️ **يرجى إدخال رمز السهم**\n\n"
                "مثال:\n"
                "`/analyze COMI.CA` - للأسهم المصرية\n"
                "`/analyze 2222.SR` - للأسهم السعودية\n"
                "`/analyze AAPL` - للأسهم الأمريكية",
                parse_mode='Markdown'
            )
            return
        
        symbol = args[0].upper()
        
        await update.message.reply_text(f"🔍 **جاري تحليل {symbol}...**", parse_mode='Markdown')
        
        # تحليل السهم
        opportunities = await self.trading_agent.scan_market([symbol])
        
        if opportunities:
            opp = opportunities[0]
            
            analysis_text = f"""
📊 **تحليل سهم {opp.name} ({opp.symbol})**

💰 **السعر الحالي:** {opp.current_price:.2f}
🎯 **السعر المستهدف:** {opp.target_price:.2f}
📈 **العائد المتوقع:** {opp.upside_percent:+.1f}%

**التوصية:** 
"""
            if opp.action == "strong_buy":
                analysis_text += "🟢 **شراء قوي**\n"
            elif opp.action == "buy":
                analysis_text += "🟡 **شراء**\n"
            elif opp.action == "hold":
                analysis_text += "⚪ **انتظار**\n"
            elif opp.action == "sell":
                analysis_text += "🟠 **بيع**\n"
            else:
                analysis_text += "🔴 **بيع قوي**\n"
            
            analysis_text += f"""
**المخاطرة:** {opp.risk_level}
**الأفق الزمني:** {opp.time_frame}
**الثقة:** {opp.confidence:.0f}%

**المؤشرات الفنية:**
• RSI: {opp.indicators.get('rsi', 'N/A'):.1f}
• حجم التداول: {opp.indicators.get('volume_ratio', 'N/A'):.1f}x المتوسط
• الاتجاه: {'صاعد' if opp.indicators.get('trend') == 'up' else 'هابط'}

**أسباب التوصية:**
"""
            for reason in opp.reasons:
                analysis_text += f"• {reason}\n"
            
            # إضافة أزرار تفاعلية
            keyboard = [
                [InlineKeyboardButton("📊 رسم بياني", callback_data=f'chart_{opp.symbol}')],
                [InlineKeyboardButton("🔔 تنبيه عند السعر", callback_data=f'alert_{opp.symbol}_{opp.current_price}')],
                [InlineKeyboardButton("➕ إضافة للمحفظة", callback_data=f'add_portfolio_{opp.symbol}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                analysis_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                f"❌ **عذراً، لم نتمكن من تحليل {symbol}**\n\n"
                "الرجاء التأكد من:\n"
                "• صحة رمز السهم\n"
                "• وجود بيانات كافية للسهم\n"
                "• اتصال الشبكة",
                parse_mode='Markdown'
            )
    
    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /portfolio - إدارة المحفظة"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_portfolios or not self.user_portfolios[user_id]:
            keyboard = [
                [InlineKeyboardButton("➕ إضافة سهم للمحفظة", callback_data='add_stock')],
                [InlineKeyboardButton("📖 كيفية الاستخدام", callback_data='portfolio_help')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "💼 **محفظتك الاستثمارية فارغة**\n\n"
                "أضف أسهمك لمتابعة أدائها وتحليلها بشكل دوري.\n\n"
                "يمكنك إضافة أسهم من خلال:\n"
                "• أمر /analyze ثم الضغط على 'إضافة للمحفظة'\n"
                "• أو استخدام الزر أدناه",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
        
        # عرض المحفظة
        portfolio = self.user_portfolios[user_id]
        total_value = 0
        total_change = 0
        
        portfolio_text = "💼 **محفظتك الاستثمارية**\n\n"
        
        for symbol, data in portfolio.items():
            # جلب السعر الحالي
            snapshot = await self.trading_agent.market_data.get_stock_snapshot([symbol])
            if symbol in snapshot:
                current_price = snapshot[symbol].price
                buy_price = data.get('buy_price', current_price)
                quantity = data.get('quantity', 1)
                
                value = current_price * quantity
                cost = buy_price * quantity
                profit = value - cost
                profit_percent = (profit / cost) * 100 if cost > 0 else 0
                
                total_value += value
                total_change += profit
                
                portfolio_text += f"**{symbol}**\n"
                portfolio_text += f"  • السعر الحالي: {current_price:.2f}\n"
                portfolio_text += f"  • الكمية: {quantity}\n"
                portfolio_text += f"  • القيمة: {value:.2f}\n"
                portfolio_text += f"  • الربح/الخسارة: {profit:+.2f} ({profit_percent:+.1f}%)\n\n"
        
        portfolio_text += f"---\n"
        portfolio_text += f"**إجمالي المحفظة:** {total_value:.2f}\n"
        portfolio_text += f"**إجمالي الربح/الخسارة:** {total_change:+.2f}\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ إضافة سهم", callback_data='add_stock')],
            [InlineKeyboardButton("🗑 حذف سهم", callback_data='remove_stock')],
            [InlineKeyboardButton("🔄 تحديث", callback_data='refresh_portfolio')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(portfolio_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def alert_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /alert - إدارة التنبيهات"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_alerts:
            self.user_alerts[user_id] = {}
        
        alerts = self.user_alerts[user_id]
        
        if not alerts:
            alert_text = "🔔 **ليس لديك تنبيهات مفعلة**\n\n"
            alert_text += "يمكنك تفعيل التنبيهات من خلال:\n"
            alert_text += "• أمر /analyze ثم الضغط على 'تنبيه عند السعر'\n"
            alert_text += "• استخدام الأمر `/alert <رمز> <سعر>`\n\n"
            alert_text += "مثال: `/alert COMI.CA 60`"
        else:
            alert_text = "🔔 **تنبيهاتك الحالية**\n\n"
            for symbol, target_price in alerts.items():
                alert_text += f"• {symbol}: عند سعر {target_price}\n"
        
        keyboard = [
            [InlineKeyboardButton("🗑 حذف جميع التنبيهات", callback_data='clear_alerts')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(alert_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /help"""
        help_text = """
📚 **دليل استخدام بوت التحليل الاستثماري**

**الأوامر الأساسية:**
/report - عرض تقرير يومي شامل عن أفضل الفرص
/analyze <رمز> - تحليل سهم محدد
/portfolio - إدارة ومتابعة محفظتك
/alert - إدارة التنبيهات

**أمثلة:**
• `/analyze COMI.CA` - تحليل البنك التجاري الدولي
• `/analyze 2222.SR` - تحليل أرامكو
• `/analyze AAPL` - تحليل Apple

**الميزات المتقدمة:**
• ✅ تحديثات فورية للأسعار
• ✅ إشارات ذكية للبيع والشراء
• ✅ تحليل فني متقدم (RSI, MACD, BB)
• ✅ تنبيهات عند وصول السعر لهدفك
• ✅ تقارير دورية مخصصة

**للحصول على المساعدة:**
• @support - دعم فني
• documentation.com - توثيق كامل

**تنبيه:** التحليل للأغراض التعليمية فقط وليس نصيحة استثمارية.
        """
        
        keyboard = [
            [InlineKeyboardButton("📈 تقرير اليوم", callback_data='daily_report')],
            [InlineKeyboardButton("🔍 تحليل سهم سريع", callback_data='analyze_stock')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية"""
        text = update.message.text
        user_id = update.effective_user.id
        
        # إذا كان المستخدم في حالة انتظار إدخال رمز
        if context.user_data.get('awaiting_symbol'):
            symbol = text.upper()
            context.user_data['awaiting_symbol'] = False
            
            # تحليل السهم
            opportunities = await self.trading_agent.scan_market([symbol])
            
            if opportunities:
                opp = opportunities[0]
                response = f"✅ **تم تحليل {symbol}**\n\n"
                response += f"💰 السعر: {opp.current_price:.2f}\n"
                response += f"📈 التوصية: {opp.action}\n"
                response += f"🎯 الهدف: {opp.target_price:.2f}"
            else:
                response = f"❌ لم نتمكن من تحليل {symbol}. يرجى التحقق من الرمز."
            
            await update.message.reply_text(response, parse_mode='Markdown')
            return
        
        # ردود افتراضية
        if "مرحب" in text or "السلام" in text:
            await update.message.reply_text(
                "👋 وعليكم السلام! أنا هنا لمساعدتك.\n"
                "استخدم /help لمعرفة الأوامر المتاحة."
            )
        else:
            await update.message.reply_text(
                "🤖 لست متأكداً مما تطلبه.\n"
                "استخدم /help لعرض جميع الأوامر المتاحة."
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أزرار القائمة التفاعلية"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == 'daily_report':
            await self.report_command(update, context)
        
        elif data == 'analyze_stock':
            await query.message.reply_text(
                "📝 **أرسل رمز السهم الذي تريد تحليله**\n\n"
                "مثال: COMI.CA أو 2222.SR أو AAPL"
            )
            context.user_data['awaiting_symbol'] = True
        
        elif data == 'my_portfolio':
            await self.portfolio_command(update, context)
        
        elif data == 'manage_alerts':
            await self.alert_command(update, context)
        
        elif data == 'clear_alerts':
            user_id = update.effective_user.id
            if user_id in self.user_alerts:
                self.user_alerts[user_id].clear()
                await query.message.reply_text("✅ **تم حذف جميع التنبيهات بنجاح**")
        
        elif data.startswith('alert_'):
            # إضافة تنبيه: alert_SYMBOL_PRICE
            parts = data.split('_')
            if len(parts) >= 3:
                symbol = parts[1]
                price = float(parts[2])
                user_id = update.effective_user.id
                
                if user_id not in self.user_alerts:
                    self.user_alerts[user_id] = {}
                
                self.user_alerts[user_id][symbol] = price
                await query.message.reply_text(
                    f"✅ **تم تفعيل التنبيه لسهم {symbol}**\n"
                    f"سيتم إعلامك عند وصول السعر إلى {price}"
                )
        
        elif data.startswith('add_portfolio_'):
            # إضافة للمحفظة
            symbol = data.replace('add_portfolio_', '')
            user_id = update.effective_user.id
            
            if user_id not in self.user_portfolios:
                self.user_portfolios[user_id] = {}
            
            if symbol not in self.user_portfolios[user_id]:
                # جلب السعر الحالي
                snapshot = await self.trading_agent.market_data.get_stock_snapshot([symbol])
                if symbol in snapshot:
                    current_price = snapshot[symbol].price
                    
                    self.user_portfolios[user_id][symbol] = {
                        'buy_price': current_price,
                        'quantity': 1,
                        'added_date': datetime.now().isoformat()
                    }
                    
                    await query.message.reply_text(
                        f"✅ **تم إضافة {symbol} إلى محفظتك**\n"
                        f"سعر الشراء: {current_price:.2f}"
                    )
                else:
                    await query.message.reply_text(f"❌ لم نتمكن من إضافة {symbol}")
            else:
                await query.message.reply_text(f"⚠️ {symbol} موجود بالفعل في محفظتك")
        
        elif data == 'refresh_portfolio':
            await self.portfolio_command(update, context)
    
    async def run(self):
        """تشغيل البوت"""
        await self.initialize()
        
        # بدء البوت
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("🚀 بوت التليجرام يعمل الآن...")
        
        # الحفاظ على التشغيل
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.application.stop()

# ====================== التشغيل ======================
async def main():
    """اختبار البوت"""
    import sys
    sys.path.append('/trading_platform/backend')
    
    from agents.trading_agent import TradingAgent
    from api.market_data import MarketDataManager
    
    # تهيئة المكونات
    market_data = MarketDataManager()
    await market_data.initialize()
    
    trading_agent = TradingAgent(market_data)
    await trading_agent.initialize()
    
    # تشغيل البوت
    bot_token = "YOUR_BOT_TOKEN_HERE"  # ضع التوكن هنا
    bot = TradingTelegramBot(bot_token, trading_agent)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
