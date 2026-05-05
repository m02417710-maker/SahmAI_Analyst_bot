"""
ملف: backend/education/learning_platform.py
المسار: /trading_platform/backend/education/learning_platform.py
الوظيفة: منصة تعليمية متكاملة مع فيديوهات واختبارات
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from loguru import logger

class CourseLevel(Enum):
    BEGINNER = "مبتدئ"
    INTERMEDIATE = "متوسط"
    ADVANCED = "متقدم"
    EXPERT = "خبير"

class QuizType(Enum):
    MULTIPLE_CHOICE = "اختيار من متعدد"
    TRUE_FALSE = "صح/خطأ"
    PRACTICAL = "تطبيقي"

@dataclass
class Lesson:
    """درس تعليمي"""
    id: str
    title: str
    content: str
    video_url: str
    duration_minutes: int
    order: int
    quiz_id: Optional[str] = None

@dataclass
class Course:
    """دورة تعليمية"""
    id: str
    title: str
    description: str
    level: CourseLevel
    lessons: List[Lesson]
    price: float
    required_subscription: str
    total_duration: int
    enrolled_count: int
    rating: float
    created_at: datetime

@dataclass
class Quiz:
    """اختبار"""
    id: str
    title: str
    type: QuizType
    questions: List[Dict]
    passing_score: int
    time_limit_minutes: int

@dataclass
class UserProgress:
    """تقدم المستخدم"""
    user_id: str
    course_id: str
    completed_lessons: List[str]
    quiz_scores: List[Dict]
    certificate_earned: bool
    last_accessed: datetime
    completion_percentage: float

class LearningPlatform:
    """منصة التعلم المتكاملة"""
    
    def __init__(self, subscription_manager):
        self.subscription_manager = subscription_manager
        self.courses: Dict[str, Course] = {}
        self.quizzes: Dict[str, Quiz] = {}
        self.user_progress: Dict[str, UserProgress] = {}
        
    async def initialize(self):
        """تهيئة المنصة"""
        await self._load_courses()
        await self._load_quizzes()
        logger.info("✅ تم تهيئة المنصة التعليمية")
    
    async def get_courses(self, level: Optional[CourseLevel] = None) -> List[Course]:
        """الحصول على قائمة الدورات"""
        courses = list(self.courses.values())
        
        if level:
            courses = [c for c in courses if c.level == level]
        
        return sorted(courses, key=lambda x: x.level.value)
    
    async def get_course_details(self, course_id: str) -> Optional[Course]:
        """الحصول على تفاصيل الدورة"""
        return self.courses.get(course_id)
    
    async def enroll_user(self, user_id: str, course_id: str) -> bool:
        """تسجيل مستخدم في دورة"""
        try:
            if course_id not in self.courses:
                logger.warning(f"الدورة {course_id} غير موجودة")
                return False
            
            course = self.courses[course_id]
            
            # التحقق من صلاحية المستخدم
            subscription = await self.subscription_manager.get_user_subscription(user_id)
            if not subscription:
                logger.warning(f"المستخدم {user_id} ليس لديه اشتراك")
                return False
            
            # إنشاء تقدم جديد
            progress_key = f"{user_id}_{course_id}"
            if progress_key not in self.user_progress:
                self.user_progress[progress_key] = UserProgress(
                    user_id=user_id,
                    course_id=course_id,
                    completed_lessons=[],
                    quiz_scores=[],
                    certificate_earned=False,
                    last_accessed=datetime.now(),
                    completion_percentage=0
                )
                
                course.enrolled_count += 1
                logger.info(f"✅ تم تسجيل المستخدم {user_id} في دورة {course.title}")
            
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تسجيل المستخدم: {e}")
            return False
    
    async def complete_lesson(self, user_id: str, course_id: str, lesson_id: str) -> bool:
        """إكمال درس"""
        try:
            progress_key = f"{user_id}_{course_id}"
            
            if progress_key not in self.user_progress:
                return False
            
            progress = self.user_progress[progress_key]
            
            if lesson_id not in progress.completed_lessons:
                progress.completed_lessons.append(lesson_id)
                
                # تحديث نسبة الإكمال
                course = self.courses[course_id]
                progress.completion_percentage = (len(progress.completed_lessons) / len(course.lessons)) * 100
                progress.last_accessed = datetime.now()
                
                logger.info(f"✅ أكمل المستخدم {user_id} الدرس {lesson_id}")
                
                # التحقق من إكمال الدورة بالكامل
                if progress.completion_percentage == 100 and not progress.certificate_earned:
                    await self._issue_certificate(user_id, course_id)
            
            return True
            
        except Exception as e:
            logger.error(f"خطأ في إكمال الدرس: {e}")
            return False
    
    async def take_quiz(self, user_id: str, quiz_id: str, answers: List[Dict]) -> Dict:
        """إجراء اختبار"""
        try:
            if quiz_id not in self.quizzes:
                return {"success": False, "message": "الاختبار غير موجود"}
            
            quiz = self.quizzes[quiz_id]
            
            # تصحيح الاختبار
            score = 0
            results = []
            
            for i, question in enumerate(quiz.questions):
                user_answer = answers[i] if i < len(answers) else None
                is_correct = user_answer == question.get('correct_answer')
                
                if is_correct:
                    score += 1
                
                results.append({
                    'question': question['text'],
                    'user_answer': user_answer,
                    'correct_answer': question.get('correct_answer'),
                    'is_correct': is_correct,
                    'explanation': question.get('explanation', '')
                })
            
            percentage = (score / len(quiz.questions)) * 100
            passed = percentage >= quiz.passing_score
            
            # حفظ النتيجة
            quiz_result = {
                'quiz_id': quiz_id,
                'score': percentage,
                'passed': passed,
                'date': datetime.now().isoformat(),
                'answers': results
            }
            
            # تحديث تقدم المستخدم
            for progress in self.user_progress.values():
                if progress.user_id == user_id:
                    progress.quiz_scores.append(quiz_result)
                    break
            
            logger.info(f"📝 أجرى المستخدم {user_id} اختبار {quiz.title} - النتيجة: {percentage}%")
            
            return {
                "success": True,
                "score": percentage,
                "passed": passed,
                "results": results,
                "message": "اجتياز!" if passed else "حاول مرة أخرى"
            }
            
        except Exception as e:
            logger.error(f"خطأ في إجراء الاختبار: {e}")
            return {"success": False, "message": str(e)}
    
    async def _issue_certificate(self, user_id: str, course_id: str):
        """إصدار شهادة إتمام"""
        try:
            course = self.courses[course_id]
            progress_key = f"{user_id}_{course_id}"
            progress = self.user_progress[progress_key]
            
            progress.certificate_earned = True
            
            # توليد شهادة PDF
            certificate = await self._generate_certificate_pdf(user_id, course)
            
            # إرسال للمستخدم
            await self._send_certificate_email(user_id, certificate)
            
            logger.info(f"🎓 تم إصدار شهادة للمستخدم {user_id} في دورة {course.title}")
            
        except Exception as e:
            logger.error(f"خطأ في إصدار الشهادة: {e}")
    
    async def get_user_learning_path(self, user_id: str) -> Dict:
        """الحصول على مسار التعلم المخصص للمستخدم"""
        try:
            # تحليل مستوى المستخدم بناءً على اختبارات سابقة
            user_level = await self._assess_user_level(user_id)
            
            # اقتراح دورات مناسبة
            recommended_courses = [
                course for course in self.courses.values()
                if course.level.value <= user_level.value
            ]
            
            # دورات متقدمة للإكمال
            advanced_courses = [
                course for course in self.courses.values()
                if course.level.value > user_level.value
            ]
            
            return {
                "current_level": user_level.value,
                "completed_courses": await self._get_completed_courses(user_id),
                "in_progress": await self._get_in_progress_courses(user_id),
                "recommended": recommended_courses[:5],
                "next_level_courses": advanced_courses[:3]
            }
            
        except Exception as e:
            logger.error(f"خطأ في مسار التعلم: {e}")
            return {}
    
    async def _load_courses(self):
        """تحميل الدورات التعليمية"""
        # دورات المستوى المبتدئ
        beginner_course = Course(
            id="course_001",
            title="مقدمة في تحليل الأسهم",
            description="تعلم أساسيات تحليل الأسهم والمؤشرات المالية",
            level=CourseLevel.BEGINNER,
            lessons=[
                Lesson(
                    id="lesson_001",
                    title="ما هي الأسهم؟",
                    content="فهم أساسيات سوق الأسهم...",
                    video_url="https://youtube.com/watch?v=xxx",
                    duration_minutes=15,
                    order=1
                ),
                Lesson(
                    id="lesson_002",
                    title="كيف تقرأ الرسوم البيانية",
                    content="تعلم قراءة الشموع اليابانية...",
                    video_url="https://youtube.com/watch?v=yyy",
                    duration_minutes=25,
                    order=2
                ),
                Lesson(
                    id="lesson_003",
                    title="المؤشرات الأساسية",
                    content="RSI, MACD, المتوسطات المتحركة...",
                    video_url="https://youtube.com/watch?v=zzz",
                    duration_minutes=30,
                    order=3
                )
            ],
            price=0,
            required_subscription="free",
            total_duration=70,
            enrolled_count=1523,
            rating=4.8,
            created_at=datetime.now()
        )
        
        # دورات المستوى المتوسط
        intermediate_course = Course(
            id="course_002",
            title="التحليل الفني المتقدم",
            description="استراتيجيات متقدمة لتحليل الأسهم",
            level=CourseLevel.INTERMEDIATE,
            lessons=[
                Lesson(
                    id="lesson_004",
                    title="أنماط الشموع اليابانية",
                    content="تعلم أنماط الانعكاس والاستمرار...",
                    video_url="https://youtube.com/watch?v=aaa",
                    duration_minutes=35,
                    order=1
                ),
                Lesson(
                    id="lesson_005",
                    title="نظرية موجات إليوت",
                    content="فهم موجات السوق...",
                    video_url="https://youtube.com/watch?v=bbb",
                    duration_minutes=45,
                    order=2
                ),
                Lesson(
                    id="lesson_006",
                    title="إدارة المخاطر",
                    content="كيف تحمي رأس مالك...",
                    video_url="https://youtube.com/watch?v=ccc",
                    duration_minutes=40,
                    order=3
                )
            ],
            price=299,
            required_subscription="basic",
            total_duration=120,
            enrolled_count=892,
            rating=4.9,
            created_at=datetime.now()
        )
        
        # دورات المستوى المتقدم
        advanced_course = Course(
            id="course_003",
            title="التداول بالذكاء الاصطناعي",
            description="استخدام AI في تحليل وتداول الأسهم",
            level=CourseLevel.ADVANCED,
            lessons=[
                Lesson(
                    id="lesson_007",
                    title="مقدمة في ML للتداول",
                    content="أساسيات تعلم الآلة...",
                    video_url="https://youtube.com/watch?v=ddd",
                    duration_minutes=50,
                    order=1
                ),
                Lesson(
                    id="lesson_008",
                    title="بناء نماذج التنبؤ",
                    content="كيف تبني نموذج LSTM...",
                    video_url="https://youtube.com/watch?v=eee",
                    duration_minutes=60,
                    order=2
                ),
                Lesson(
                    id="lesson_009",
