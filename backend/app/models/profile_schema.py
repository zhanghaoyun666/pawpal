"""
20维领养人画像体系 + 宠物档案体系
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ==================== 枚举定义 ====================

class LivingSpace(str, Enum):
    """居住空间"""
    SMALL_APARTMENT = "small_apartment"  # <50平公寓
    MEDIUM_APARTMENT = "medium_apartment"  # 50-90平公寓
    LARGE_APARTMENT = "large_apartment"  # >90平公寓
    HOUSE_WITH_YARD = "house_with_yard"  # 带院子的房子
    RURAL = "rural"  # 农村/别墅


class ExperienceLevel(str, Enum):
    """养宠经验"""
    NONE = "none"  # 完全新手
    BEGINNER = "beginner"  # 养过1只，经验<2年
    INTERMEDIATE = "intermediate"  # 养过2-3只，经验2-5年
    EXPERIENCED = "experienced"  # 养过3只以上，经验>5年


class FamilyStatus(str, Enum):
    """家庭状况"""
    SINGLE = "single"  # 单身独居
    COUPLE = "couple"  # 夫妻/情侣同居
    WITH_KIDS_YOUNG = "with_kids_young"  # 有小孩（<6岁）
    WITH_KIDS_OLD = "with_kids_old"  # 有小孩（>6岁）
    WITH_ELDERLY = "with_elderly"  # 有老人同住
    MULTI_GEN = "multi_gen"  # 三代同堂


class ActivityLevel(str, Enum):
    """活动量偏好"""
    LOW = "low"  # 喜欢安静，很少运动
    MEDIUM = "medium"  # 适度活动，每天散步
    HIGH = "high"  # 喜欢户外运动，经常跑步/爬山


class NoiseTolerance(str, Enum):
    """噪音容忍度"""
    LOW = "low"  # 需要安静环境
    MEDIUM = "medium"  # 可以接受正常宠物叫声
    HIGH = "high"  # 不介意吵闹


class SheddingTolerance(str, Enum):
    """掉毛接受度"""
    NONE = "none"  # 完全不接受掉毛
    LOW = "low"  # 接受少量掉毛
    MEDIUM = "medium"  # 接受正常掉毛
    HIGH = "high"  # 完全不在意


class GroomingWillingness(str, Enum):
    """护理意愿"""
    LOW = "low"  # 希望低维护，每周<1小时
    MEDIUM = "medium"  # 可以接受每周1-3小时护理
    HIGH = "high"  # 愿意花大量时间护理


class TrainingWillingness(str, Enum):
    """训练意愿"""
    LOW = "low"  # 希望宠物已经训练好
    MEDIUM = "medium"  # 愿意基础训练
    HIGH = "high"  # 愿意专业训练


class BudgetLevel(str, Enum):
    """预算水平"""
    LOW = "low"  # <500元/月
    MEDIUM = "medium"  # 500-1500元/月
    HIGH = "high"  # >1500元/月


class WorkSchedule(str, Enum):
    """工作节奏"""
    REGULAR = "regular"  # 朝九晚五，规律
    FLEXIBLE = "flexible"  # 弹性工作
    SHIFT = "shift"  # 轮班制
    FREQUENT_TRAVEL = "frequent_travel"  # 经常出差
    REMOTE = "remote"  # 居家办公


class PetSizePreference(str, Enum):
    """宠物体型偏好"""
    TINY = "tiny"  # 迷你型（<5kg）
    SMALL = "small"  # 小型（5-10kg）
    MEDIUM = "medium"  # 中型（10-25kg）
    LARGE = "large"  # 大型（25-40kg）
    XLARGE = "xlarge"  # 超大型（>40kg）
    NO_PREFERENCE = "no_preference"  # 无偏好


class PetAgePreference(str, Enum):
    """宠物年龄偏好"""
    BABY = "baby"  # 幼年（<6个月）
    YOUNG = "young"  # 青年（6个月-2岁）
    ADULT = "adult"  # 成年（2-7岁）
    SENIOR = "senior"  # 老年（>7岁）
    NO_PREFERENCE = "no_preference"


class TemperamentPreference(str, Enum):
    """性格偏好（多选）"""
    CALM = "calm"  # 安静温顺
    PLAYFUL = "playful"  # 活泼好动
    AFFECTIONATE = "affectionate"  # 粘人亲人
    INDEPENDENT = "independent"  # 独立自主
    PROTECTIVE = "protective"  # 警觉护主
    SOCIAL = "social"  # 社交达人


# ==================== 20维领养人画像 ====================

class AdopterProfile(BaseModel):
    """
    领养人画像 - 20维度
    """
    # === 基础信息（3维）===
    living_space: LivingSpace = Field(..., description="居住空间")
    has_yard: bool = Field(False, description="是否有院子")
    is_renting: bool = Field(..., description="是否租房")
    landlord_allows_pets: Optional[bool] = Field(None, description="房东是否允许养宠")
    
    # === 经济能力（2维）===
    budget_level: BudgetLevel = Field(..., description="预算水平")
    income_stability: str = Field(..., description="收入稳定性：stable/unstable/student")
    
    # === 时间投入（3维）===
    daily_time_available: int = Field(..., ge=0, le=24, description="每日可用时间（小时）")
    work_schedule: WorkSchedule = Field(..., description="工作节奏")
    work_hours_per_day: int = Field(..., ge=0, le=16, description="每日工作时长")
    
    # === 经验能力（3维）===
    experience_level: ExperienceLevel = Field(..., description="养宠经验")
    previous_pets: List[str] = Field(default=[], description="曾养过的宠物种类")
    training_willingness: TrainingWillingness = Field(..., description="训练意愿")
    
    # === 家庭状况（2维）===
    family_status: FamilyStatus = Field(..., description="家庭状况")
    household_size: int = Field(..., ge=1, le=10, description="家庭人数")
    
    # === 偏好匹配（5维）===
    preferred_size: PetSizePreference = Field(..., description="偏好体型")
    preferred_age: PetAgePreference = Field(..., description="偏好年龄")
    preferred_temperament: List[TemperamentPreference] = Field(default=[], description="偏好性格")
    activity_level: ActivityLevel = Field(..., description="活动量偏好")
    other_pets: List[str] = Field(default=[], description="家中现有宠物")
    
    # === 容忍度（2维）===
    noise_tolerance: NoiseTolerance = Field(..., description="噪音容忍度")
    shedding_tolerance: SheddingTolerance = Field(..., description="掉毛接受度")
    grooming_willingness: GroomingWillingness = Field(..., description="护理意愿")
    
    # === 特殊需求（可选）===
    has_allergies: bool = Field(False, description="是否有过敏")
    allergy_details: Optional[str] = Field(None, description="过敏详情")
    must_have_traits: List[str] = Field(default=[], description="必须具备的特征")
    deal_breakers: List[str] = Field(default=[], description="绝对不能接受的特征")
    
    class Config:
        use_enum_values = True


# ==================== 宠物档案体系 ====================

class PetProfile(BaseModel):
    """
    宠物档案 - 结构化标签
    """
    id: str
    name: str
    species: str  # dog/cat/rabbit/other
    breed: str
    
    # === 基础属性 ===
    age_months: int = Field(..., ge=0)
    size_category: str = Field(..., description="tiny/small/medium/large/xlarge")
    weight_kg: float
    gender: str  # male/female
    
    # === 性格标签 ===
    temperament: List[str] = Field(default=[], description="性格特点")
    energy_level: str = Field(..., description="low/medium/high")
    sociability: str = Field(..., description="shy/moderate/outgoing")
    trainability: str = Field(..., description="easy/moderate/difficult")
    
    # === 护理需求 ===
    shedding_level: str = Field(..., description="none/low/medium/high")
    grooming_needs: str = Field(..., description="low/medium/high")
    exercise_needs: str = Field(..., description="low/medium/high")
    
    # === 适应性 ===
    good_with_kids: bool
    good_with_dogs: bool
    good_with_cats: bool
    good_with_strangers: bool
    
    # === 特殊需求 ===
    special_needs: List[str] = Field(default=[])
    medical_notes: Optional[str] = None
    behavioral_notes: Optional[str] = None
    
    # === 空间需求 ===
    min_space_requirement: str = Field(..., description="small_apartment/medium_apartment/large_apartment/house")
    needs_yard: bool = False
    
    # === 历史数据 ===
    adoption_history: Optional[Dict] = None  # 历史领养反馈
    success_rate: Optional[float] = None  # 相似画像成功率


# ==================== 匹配结果 ====================

class MatchDimension(BaseModel):
    """单个匹配维度得分"""
    name: str
    score: float = Field(..., ge=0, le=100)
    weight: float
    reason: str


class MatchResult(BaseModel):
    """匹配结果"""
    pet_id: str
    pet_name: str
    overall_score: float = Field(..., ge=0, le=100)
    
    # 三大部分得分
    hard_constraint_score: float  # 硬性条件（0.4权重）
    soft_preference_score: float  # 软性偏好（0.4权重）
    historical_score: float  # 历史成功率（0.2权重）
    
    # 详细维度
    dimensions: List[MatchDimension]
    
    # 可解释性
    match_reasons: List[str]  # 匹配理由
    concerns: List[str]  # 潜在顾虑
    recommendations: List[str]  # 建议
    
    # 是否通过硬性筛选
    passed_hard_constraints: bool
    failed_constraints: List[str]  # 未通过的硬性条件


# ==================== 历史反馈数据 ====================

class AdoptionFeedback(BaseModel):
    """领养后反馈"""
    application_id: str
    pet_id: str
    adopter_profile_summary: Dict  # 领养人画像摘要
    outcome: str  # success/returned/issue
    duration_days: int  # 领养持续天数
    feedback_text: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    issues: List[str] = Field(default=[])
    
    # 用于计算相似度
    profile_embedding: Optional[List[float]] = None
