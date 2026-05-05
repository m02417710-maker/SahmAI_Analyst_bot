"""
ملف: backend/social/social_trading.py
المسار: /trading_platform/backend/social/social_trading.py
الوظيفة: نظام التداول الاجتماعي - مشاركة الصفقات والتفاعل
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

class PostType(Enum):
    TRADE_ALERT = "تنبيه صفقة"
    MARKET_ANALYSIS = "تحليل سوق"
    EDUCATIONAL = "محتوى تعليمي"
    QUESTION = "سؤال"
    DISCUSSION = "نقاش"

class ReactionType(Enum):
    LIKE = "👍"
    PROFITABLE = "💰"
    INSIGHTFUL = "💡"
    HELPFUL = "🙏"
    FUNNY = "😄"

@dataclass
class SocialPost:
    """منشور في شبكة التداول الاجتماعية"""
    id: str
    user_id: str
    username: str
    type: PostType
    content: str
    symbols: List[str]
    trade_details: Optional[Dict]
    created_at: datetime
    likes: int = 0
    comments: List[Dict] = field(default_factory=list)
    shares: int = 0
    reactions: Dict[str, int] = field(default_factory=dict)

@dataclass
class UserProfile:
    """ملف المستخدم الاجتماعي"""
    user_id: str
    username: str
    bio: str
    followers_count: int
    following_count: int
    posts_count: int
    reputation_score: float
    success_rate: float
    total_profit: float
    followers: List[str] = field(default_factory=list)
    following: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)

class SocialTradingPlatform:
    """منصة التداول الاجتماعية"""
    
    def __init__(self, trading_agent, market_data):
        self.trading_agent = trading_agent
        self.market_data = market_data
        self.posts: Dict[str, SocialPost] = {}
        self.profiles: Dict[str, UserProfile] = {}
        self.feed_cache: Dict[str, List[SocialPost]] = {}
        
    async def initialize(self):
        """تهيئة المنصة الاجتماعية"""
        await self._load_profiles()
        await self._load_posts()
        logger.info("✅ تم تهيئة منصة التداول الاجتماعية")
    
    async def create_post(
        self,
        user_id: str,
        type: PostType,
        content: str,
        symbols: List[str] = None,
        trade_details: Dict = None
    ) -> SocialPost:
        """إنشاء منشور جديد"""
        try:
            post = SocialPost(
                id=self._generate_post_id(),
                user_id=user_id,
                username=await self._get_username(user_id),
                type=type,
                content=content,
                symbols=symbols or [],
                trade_details=trade_details,
                created_at=datetime.now()
            )
            
            self.posts[post.id] = post
            
            # تحديث إحصائيات المستخدم
            if user_id in self.profiles:
                self.profiles[user_id].posts_count += 1
            
            # نشر في الـ feed
            await self._broadcast_to_followers(post)
            
            # إذا كان منشور صفقة، مشاركته مع المتابعين
            if type == PostType.TRADE_ALERT and trade_details:
                await self._notify_followers_of_trade(user_id, trade_details)
            
            logger.info(f"📝 تم إنشاء منشور جديد بواسطة {user_id}")
            return post
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء المنشور: {e}")
            return None
    
    async def like_post(self, user_id: str, post_id: str) -> bool:
        """الإعجاب بمنشور"""
        try:
            if post_id not in self.posts:
                return False
            
            post = self.posts[post_id]
            post.likes += 1
            
            # تحديث سمعة المستخدم صاحب المنشور
            if post.user_id in self.profiles:
                self.profiles[post.user_id].reputation_score += 0.5
            
            return True
            
        except Exception as e:
            logger.error(f"خطأ في الإعجاب: {e}")
            return False
    
    async def add_comment(self, user_id: str, post_id: str, comment: str) -> bool:
        """إضافة تعليق على منشور"""
        try:
            if post_id not in self.posts:
                return False
            
            post = self.posts[post_id]
            post.comments.append({
                'user_id': user_id,
                'username': await self._get_username(user_id),
                'comment': comment,
                'timestamp': datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"خطأ في إضافة تعليق: {e}")
            return False
    
    async def follow_user(self, follower_id: str, following_id: str) -> bool:
        """متابعة مستخدم آخر"""
        try:
            # تحديث متابع
            if follower_id not in self.profiles:
                await self._create_profile(follower_id)
            if following_id not in self.profiles:
                await self._create_profile(following_id)
            
            if following_id not in self.profiles[follower_id].following:
                self.profiles[follower_id].following.append(following_id)
                self.profiles[follower_id].following_count += 1
            
            if follower_id not in self.profiles[following_id].followers:
                self.profiles[following_id].followers.append(follower_id)
                self.profiles[following_id].followers_count += 1
            
            logger.info(f"👥 {follower_id} يتابع الآن {following_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في المتابعة: {e}")
            return False
    
    async def get_feed(self, user_id: str, limit: int = 50) -> List[SocialPost]:
        """الحصول على الـ feed المخصص للمستخدم"""
        try:
            if user_id not in self.profiles:
                return []
            
            # التحقق من الكاش
            if user_id in self.feed_cache:
                return self.feed_cache[user_id][:limit]
            
            following = self.profiles[user_id].following
            
            # جمع منشورات المستخدمين الذين يتابعهم
            feed_posts = []
            for post in self.posts.values():
                if post.user_id in following or post.user_id == user_id:
                    feed_posts.append(post)
            
            # ترتيب حسب التاريخ
            feed_posts.sort(key=lambda x: x.created_at, reverse=True)
            
            # تخزين في الكاش
            self.feed_cache[user_id] = feed_posts
            
            return feed_posts[:limit]
            
        except Exception as e:
            logger.error(f"خطأ في جلب الـ feed: {e}")
            return []
    
    async def share_trade_signal(self, user_id: str, signal: Dict) -> SocialPost:
        """مشاركة إشارة تداول مع المجتمع"""
        try:
            analysis = await self.trading_agent._analyze_single_stock(signal['symbol'])
            
            content = f"""
            📊 **إشارة تداول لـ {signal['symbol']}**
            
            🎯 **الإجراء:** {signal['action']}
            💰 **السعر الحالي:** {signal['current_price']}
            📈 **الهدف:** {signal.get('target', 'غير محدد')}
            🛑 **وقف الخسارة:** {signal.get('stop_loss', 'غير محدد')}
            
            🔍 **التحليل:**
            {analysis.reasons[0] if analysis and analysis.reasons else 'تحليل مفصل في التعليقات'}
            """
            
            post = await self.create_post(
                user_id=user_id,
                type=PostType.TRADE_ALERT,
                content=content,
                symbols=[signal['symbol']],
                trade_details=signal
            )
            
            return post
            
        except Exception as e:
            logger.error(f"خطأ في مشاركة الإشارة: {e}")
            return None
    
    async def get_top_traders(self, limit: int = 10) -> List[UserProfile]:
        """الحصول على أفضل المتداولين في المجتمع"""
        sorted_profiles = sorted(
            self.profiles.values(),
            key=lambda x: (x.success_rate, x.total_profit),
            reverse=True
        )
        return sorted_profiles[:limit]
    
    async def get_trending_topics(self) -> List[Dict]:
        """الحصول على المواضيع الرائجة"""
        topics = {}
        
        for post in self.posts.values():
            for symbol in post.symbols:
                if symbol not in topics:
                    topics[symbol] = 0
                topics[symbol] += 1
        
        # ترتيب حسب الشعبية
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"symbol": symbol, "mentions": count}
            for symbol, count in sorted_topics[:10]
        ]
    
    async def _broadcast_to_followers(self, post: SocialPost):
        """نشر المنشور لمتابعي المستخدم"""
        if post.user_id in self.profiles:
            followers = self.profiles[post.user_id].followers
            
            for follower_id in followers:
                # تحديث الكاش لكل متابع
                if follower_id in self.feed_cache:
                    self.feed_cache[follower_id].insert(0, post)
    
    async def _notify_followers_of_trade(self, user_id: str, trade_details: Dict):
        """إشعار المتابعين بصفقة جديدة"""
        # يمكن إرسال إشعارات WebSocket للمتابعين
        pass
    
    async def _get_username(self, user_id: str) -> str:
        """الحصول على اسم المستخدم"""
        if user_id in self.profiles:
            return self.profiles[user_id].username
        return f"مستخدم_{user_id[:8]}"
    
    async def _create_profile(self, user_id: str):
        """إنشاء ملف مستخدم جديد"""
        self.profiles[user_id] = UserProfile(
            user_id=user_id,
            username=f"trader_{user_id[:8]}",
            bio="متداول في منصة التحليل الذكية",
            followers_count=0,
            following_count=0,
            posts_count=0,
            reputation_score=100.0,
            success_rate=0.0,
            total_profit=0.0
        )
    
    def _generate_post_id(self) -> str:
        """توليد معرف فريد للمنشور"""
        return f"POST_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    async def _load_profiles(self):
        """تحميل الملفات الشخصية"""
        # بيانات تجريبية
        pass
    
    async def _load_posts(self):
        """تحميل المنشورات"""
        pass
