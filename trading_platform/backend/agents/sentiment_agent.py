"""
ملف: backend/agents/sentiment_agent.py
المسار: /trading_platform/backend/agents/sentiment_agent.py
الوظيفة: تحليل المشاعر من الأخبار ووسائل التواصل الاجتماعي
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import google.generativeai as genai
from loguru import logger

@dataclass
class NewsArticle:
    """نموذج مقال إخباري"""
    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    sentiment_score: float = 0.0
    relevance_score: float = 0.0
    impact: str = "neutral"

@dataclass
class MarketSentiment:
    """تحليل مشاعر السوق"""
    overall_score: float  # -1 to 1
    sentiment: str  # bullish, bearish, neutral
    confidence: float
    sources: Dict[str, float]
    top_news: List[NewsArticle]
    recommendations: List[str]

class SentimentAgent:
    """وكيل تحليل المشاعر والأخبار"""
    
    def __init__(self, gemini_api_key: str = None):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.gemini_api_key = gemini_api_key
        self.news_sources = {
            'reuters': 'https://api.reuters.com/news',
            'bloomberg': 'https://api.bloomberg.com/news',
            'cnbc': 'https://api.cnbc.com/news',
            'aljazeera': 'https://api.aljazeera.net/news',
        }
        
    async def initialize(self):
        """تهيئة الوكيل"""
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        
        logger.info("✅ تم تهيئة وكيل تحليل المشاعر")
    
    async def fetch_news(self, symbol: str, days_back: int = 7) -> List[NewsArticle]:
        """جلب الأخبار المتعلقة بسهم معين"""
        articles = []
        
        # استخدام APIs مختلفة لجلب الأخبار
        for source_name, source_url in self.news_sources.items():
            try:
                # محاكاة جلب الأخبار (يمكن استبدال بـ API حقيقي)
                articles.extend(await self._fetch_from_source(source_name, symbol))
            except Exception as e:
                logger.error(f"خطأ في جلب أخبار {source_name}: {e}")
        
        # تحليل المشاعر لكل مقال
        for article in articles:
            article.sentiment_score = self._analyze_sentiment(article.title + " " + article.content)
            article.relevance_score = self._calculate_relevance(article, symbol)
        
        # ترتيب حسب الأهمية
        articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return articles[:20]  # أعلى 20 مقال
    
    async def _fetch_from_source(self, source: str, symbol: str) -> List[NewsArticle]:
        """جلب الأخبار من مصدر محدد"""
        # يمكن تنفيذ API حقيقي هنا
        # حالياً نعيد بيانات تجريبية
        mock_articles = [
            NewsArticle(
                title=f"تحليل: سهم {symbol} يشهد نشاطاً غير مسبوق اليوم",
                content=f"شهد سهم {symbol} تداولات كثيفة اليوم مع ارتفاع في حجم التداول...",
                source=source,
                url=f"https://{source}.com/news/{symbol}",
                published_at=datetime.now() - timedelta(hours=3)
            ),
            NewsArticle(
                title=f"توقعات إيجابية لسهم {symbol} من كبار المحللين",
                content=f"رفع بنك الاستثمار تقديراته لسهم {symbol} إلى 'شراء' مع هدف سعرى جديد...",
                source=source,
                url=f"https://{source}.com/news/{symbol}",
                published_at=datetime.now() - timedelta(hours=8)
            )
        ]
        return mock_articles
    
    def _analyze_sentiment(self, text: str) -> float:
        """تحليل المشاعر باستخدام VADER"""
        scores = self.sentiment_analyzer.polarity_scores(text)
        return scores['compound']  # -1 (سلبي) إلى +1 (إيجابي)
    
    def _calculate_relevance(self, article: NewsArticle, symbol: str) -> float:
        """حساب مدى صلة المقال بالسهم"""
        relevance = 0.0
        text = (article.title + " " + article.content).lower()
        
        # كلمات مفتاحية تزيد الأهمية
        keywords = [symbol.lower(), 'stock', 'share', 'price', 'market']
        for keyword in keywords:
            if keyword in text:
                relevance += 0.2
        
        # حد أقصى 1.0
        return min(relevance, 1.0)
    
    async def analyze_market_sentiment(self, symbols: List[str]) -> Dict[str, MarketSentiment]:
        """تحليل مشاعر السوق لمجموعة من الأسهم"""
        results = {}
        
        for symbol in symbols:
            # جلب الأخبار
            news = await self.fetch_news(symbol)
            
            if not news:
                continue
            
            # حساب المتوسط العام للمشاعر
            total_sentiment = sum(article.sentiment_score for article in news)
            avg_sentiment = total_sentiment / len(news) if news else 0
            
            # تحديد اتجاه السوق
            if avg_sentiment > 0.2:
                sentiment = "bullish"
            elif avg_sentiment < -0.2:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            
            # تحليل مصادر الأخبار
            sources_sentiment = {}
            for source in self.news_sources.keys():
                source_news = [n for n in news if n.source == source]
                if source_news:
                    source_sentiment = sum(n.sentiment_score for n in source_news) / len(source_news)
                    sources_sentiment[source] = source_sentiment
            
            # توليد توصيات باستخدام Gemini إذا كان متاحاً
            recommendations = await self._generate_recommendations(symbol, news, avg_sentiment)
            
            results[symbol] = MarketSentiment(
                overall_score=avg_sentiment,
                sentiment=sentiment,
                confidence=min(abs(avg_sentiment) * 100, 95),
                sources=sources_sentiment,
                top_news=news[:5],
                recommendations=recommendations
            )
        
        return results
    
    async def _generate_recommendations(self, symbol: str, news: List[NewsArticle], sentiment: float) -> List[str]:
        """توليد توصيات باستخدام Gemini AI"""
        if not hasattr(self, 'gemini_model'):
            return [
                f"المشاعر العامة لسهم {symbol} {self._get_sentiment_text(sentiment)}",
                "يُنصح بمتابعة الأخبار عن كثب"
            ]
        
        try:
            # تجهيز النص للتحليل
            news_summary = "\n".join([f"- {n.title} (المصدر: {n.source})" for n in news[:5]])
            
            prompt = f"""
            بناءً على الأخبار التالية لسهم {symbol}:
            
            {news_summary}
            
            المشاعر العامة: {self._get_sentiment_text(sentiment)} (نسبة: {sentiment:.2f})
            
            قدم 3 توصيات استثمارية مختصرة وعملية للمستثمرين.
            """
            
            response = self.gemini_model.generate_content(prompt)
            recommendations = response.text.split('\n')
            
            return [rec.strip() for rec in recommendations if rec.strip()]
            
        except Exception as e:
            logger.error(f"خطأ في توليد التوصيات لـ {symbol}: {e}")
            return ["تحليل المشاعر يشير إلى فرصة مراجعة السهم"]
    
    def _get_sentiment_text(self, sentiment: float) -> str:
        """الحصول على نص وصفي للمشاعر"""
        if sentiment > 0.3:
            return "إيجابية جداً"
        elif sentiment > 0.1:
            return "إيجابية"
        elif sentiment < -0.3:
            return "سلبية جداً"
        elif sentiment < -0.1:
            return "سلبية"
        else:
            return "محايدة"
    
    async def get_breaking_news_alert(self) -> Optional[Dict]:
        """الحصول على تنبيهات للأخبار العاجلة"""
        # فحص الأخبار العاجلة التي تؤثر على السوق
        # يمكن تنفيذ WebSocket للاستماع للأخبار الفورية
        return None
