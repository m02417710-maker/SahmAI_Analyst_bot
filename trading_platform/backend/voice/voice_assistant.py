"""
ملف: backend/voice/voice_assistant.py
المسار: /trading_platform/backend/voice/voice_assistant.py
الوظيفة: مساعد صوتي متقدم لتوصيات التداول
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import speech_recognition as sr
from gtts import gTTS
import pygame
import io
from loguru import logger

class VoiceAssistant:
    """المساعد الصوتي للتداول"""
    
    def __init__(self, trading_agent, market_data):
        self.trading_agent = trading_agent
        self.market_data = market_data
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        
    async def initialize(self):
        """تهيئة المساعد الصوتي"""
        pygame.mixer.init()
        logger.info("✅ تم تهيئة المساعد الصوتي")
    
    async def start_listening(self):
        """بدء الاستماع للأوامر الصوتية"""
        self.is_listening = True
        asyncio.create_task(self._listen_loop())
        logger.info("🎤 بدء الاستماع للأوامر الصوتية")
    
    async def _listen_loop(self):
        """حلقة الاستماع المستمر"""
        while self.is_listening:
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    audio = await asyncio.get_event_loop().run_in_executor(
                        None, self.recognizer.listen, source
                    )
                    
                    # تحويل الصوت إلى نص
                    text = await asyncio.get_event_loop().run_in_executor(
                        None, self.recognizer.recognize_arabic, audio
                    )
                    
                    # معالجة الأمر
                    response = await self._process_command(text)
                    
                    # تحويل الرد إلى صوت
                    if response:
                        await self.speak(response)
                        
            except sr.UnknownValueError:
                pass
            except Exception as e:
                logger.error(f"خطأ في الاستماع: {e}")
    
    async def _process_command(self, command: str) -> Optional[str]:
        """معالجة الأمر الصوتي"""
        command_lower = command.lower()
        
        # تحليل السهم
        if "حلل" in command_lower or "تحليل" in command_lower:
            # استخراج رمز السهم
            symbols = ["كومي", "سي آي بي", "أرامكو", "آبل", "تسلا"]
            for symbol in symbols:
                if symbol in command_lower:
                    return await self._analyze_stock_voice(symbol)
        
        # السعر الحالي
        elif "سعر" in command_lower or "كم سعر" in command_lower:
            for symbol in symbols:
                if symbol in command_lower:
                    return await self._get_price_voice(symbol)
        
        # أفضل الفرص
        elif "أفضل" in command_lower or "فرص" in command_lower:
            return await self._get_top_opportunities()
        
        # محفظتي
        elif "محفظتي" in command_lower or "أرباحي" in command_lower:
            return await self._get_portfolio_summary()
        
        # مساعدة
        elif "مساعدة" in command_lower or "help" in command_lower:
            return self._get_help_message()
        
        return None
    
    async def _analyze_stock_voice(self, symbol_name: str) -> str:
        """تحليل سهم بصوت"""
        # تحويل الاسم إلى رمز
        symbol_map = {
            "كومي": "COMI.CA",
            "سي آي بي": "COMI.CA",
            "أرامكو": "2222.SR",
            "آبل": "AAPL",
            "تسلا": "TSLA"
        }
        
        symbol = symbol_map.get(symbol_name, "COMI.CA")
        
        # جلب التحليل
        opportunities = await self.trading_agent.scan_market([symbol])
        
        if opportunities:
            opp = opportunities[0]
            return f"""
            تحليل سهم {symbol_name}:
            السعر الحالي {opp.current_price:.2f}
            التوصية {opp.action}
            العائد المتوقع {opp.upside_percent:+.1f} بالمئة
            الثقة {opp.confidence:.0f} بالمئة
            الأسباب: {', '.join(opp.reasons[:2])}
            """
        
        return f"عذراً، لم أتمكن من تحليل سهم {symbol_name}"
    
    async def _get_price_voice(self, symbol_name: str) -> str:
        """الحصول على السعر بصوت"""
        symbol_map = {
            "كومي": "COMI.CA",
            "سي آي بي": "COMI.CA",
            "أرامكو": "2222.SR",
            "آبل": "AAPL",
            "تسلا": "TSLA"
        }
        
        symbol = symbol_map.get(symbol_name, "COMI.CA")
        
        snapshot = await self.market_data.get_stock_snapshot([symbol])
        
        if symbol in snapshot:
            data = snapshot[symbol]
            direction = "ارتفع" if data.change_percent > 0 else "انخفض"
            return f"""
            سهم {symbol_name} الآن بسعر {data.price:.2f}
            {direction} بنسبة {abs(data.change_percent):.2f} بالمئة
            """
        
        return f"عذراً، لم أتمكن من جلب سعر {symbol_name}"
    
    async def _get_top_opportunities(self) -> str:
        """أفضل فرص الاستثمار بصوت"""
        symbols = ["COMI.CA", "TMGH.CA", "AAPL", "MSFT"]
        opportunities = await self.trading_agent.scan_market(symbols)
        
        if not opportunities:
            return "لا توجد فرص استثمارية حالياً"
        
        top = opportunities[0]
        return f"""
        أفضل فرصة استثمارية حالياً هي {top.name}
        السعر {top.current_price:.2f}
        العائد المتوقع {top.upside_percent:+.1f} بالمئة
        التوصية {top.action}
        """
    
    async def _get_portfolio_summary(self) -> str:
        """ملخص المحفظة بصوت"""
        # يمكن جلب من قاعدة البيانات
        return """
        محفظتك الحالية:
        إجمالي القيمة 150 ألف جنيه
        إجمالي الربح 12 ألف جنيه بنسبة 8.7 بالمئة
        لديك 3 مراكز مفتوحة
        أفضل صفقة حالياً هي البنك التجاري الدولي بربح 5 آلاف جنيه
        """
    
    def _get_help_message(self) -> str:
        """رسالة المساعدة"""
        return """
        مرحباً! أنا مساعدك الصوتي للتداول.
        يمكنك أن تطلب مني:
        - تحليل سهم مثل: 'حلل لي سهم كومي'
        - سعر السهم مثل: 'كم سعر أرامكو'
        - أفضل الفرص مثل: 'عطيني أفضل فرص اليوم'
        - محفظتي مثل: 'أخبرني عن محفظتي'
        
        كيف يمكنني مساعدتك اليوم؟
        """
    
    async def speak(self, text: str):
        """تحويل النص إلى صوت وتشغيله"""
        try:
            # تحويل النص إلى صوت (بالعربية)
            tts = gTTS(text=text, lang='ar')
            
            # حفظ في الذاكرة
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            
            # تشغيل الصوت
            pygame.mixer.music.load(fp)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"خطأ في تشغيل الصوت: {e}")
    
    async def send_voice_alert(self, symbol: str, alert_type: str, message: str):
        """إرسال تنبيه صوتي"""
        alert_text = f"تنبيه {alert_type} لسهم {symbol}: {message}"
        await self.speak(alert_text)
