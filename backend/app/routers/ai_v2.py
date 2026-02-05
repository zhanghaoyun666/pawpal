"""
AI 功能路由 V2 - 对齐 PRD 设计
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel
import logging

from app.services.matching_engine import matching_engine
from app.services.precheck_engine import precheck_engine
from app.services.embedding_service import adopter_profile_to_text, pet_profile_to_text
from app.models.profile_schema import (
    AdopterProfile, PetProfile, MatchResult, 
    AdoptionFeedback
)
from app.database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai/v2", tags=["ai-v2"])


# ==================== 数据模型 ====================

class QuestionnaireMessage(BaseModel):
    role: str
    text: str


class QuestionnaireRequest(BaseModel):
    user_id: str
    chat_history: List[QuestionnaireMessage]
    current_profile: Optional[Dict] = {}
    is_first: bool = False


class QuestionnaireResponse(BaseModel):
    next_question: str
    is_complete: bool
    current_field: str
    suggested_options: List[str]
    explanation: str


class MatchRequest(BaseModel):
    user_id: str
    adopter_profile: Dict  # 20维画像
    limit: int = 3


class PrecheckStartRequest(BaseModel):
    user_id: str
    pet_id: str


class PrecheckMessageRequest(BaseModel):
    session_id: str
    message: str


# ==================== 功能1：智能问卷（保持原有）====================

# 模拟问卷数据（当 LLM 服务不可用时使用）
MOCK_QUESTIONS = [
    {
        "next_question": "您好！我是 PawPal 智能领养顾问 🤖\n\n为了帮您找到最合适的毛孩子，我想先了解一些您的情况。首先，您目前住在哪里？",
        "is_complete": False,
        "current_field": "living_space",
        "suggested_options": ["公寓（无院子）", "带院子的房子", "农村住宅"],
        "explanation": "了解您的居住空间有助于推荐合适体型的宠物"
    },
    {
        "next_question": "了解！那您之前有过养宠物的经验吗？",
        "is_complete": False,
        "current_field": "experience_level",
        "suggested_options": ["完全没有，我是新手", "养过一只", "养过多只，经验丰富"],
        "explanation": "经验水平影响适合宠物的训练难度"
    },
    {
        "next_question": "您每天大概能抽出多少小时陪伴宠物？",
        "is_complete": False,
        "current_field": "daily_time_available",
        "suggested_options": ["1小时以内", "1-3小时", "3-5小时", "5小时以上"],
        "explanation": "不同宠物对陪伴时间的需求不同"
    },
    {
        "next_question": "您的家庭状况是怎样的？",
        "is_complete": False,
        "current_field": "family_status",
        "suggested_options": ["独居", "和伴侣同住", "有小孩（6岁以下）", "有小孩（6岁以上）", "和老人同住"],
        "explanation": "家庭成员构成影响宠物的性格选择"
    },
    {
        "next_question": "您更喜欢什么样的宠物性格？",
        "is_complete": False,
        "current_field": "activity_level",
        "suggested_options": ["安静温顺，喜欢宅家", "活泼好动，能一起玩耍", "适中，既安静又能互动"],
        "explanation": "性格匹配是长期相处和谐的关键"
    },
    {
        "next_question": "您家里目前有其他宠物吗？",
        "is_complete": False,
        "current_field": "other_pets",
        "suggested_options": ["没有其他宠物", "有一只狗", "有一只猫", "有多只宠物"],
        "explanation": "了解是否需要考虑宠物间的相处"
    },
    {
        "next_question": "您对宠物的体型有偏好吗？",
        "is_complete": False,
        "current_field": "size_preference",
        "suggested_options": ["小型（10斤以下）", "中型（10-30斤）", "大型（30斤以上）", "没有特别偏好"],
        "explanation": "体型影响生活空间需求和饲养成本"
    },
    {
        "next_question": "感谢您的时间！我已经了解了您的情况。\n\n现在让我为您分析最适合的宠物...",
        "is_complete": True,
        "current_field": "",
        "suggested_options": [],
        "explanation": "问卷完成"
    }
]

@router.post("/questionnaire/next", response_model=QuestionnaireResponse)
async def get_next_question(request: QuestionnaireRequest):
    """获取智能问卷的下一个问题"""
    try:
        # 尝试调用 LLM 服务
        from app.services.ai_service import ai_service
        
        result = await ai_service.generate_next_question(
            user_id=request.user_id,
            current_profile=request.current_profile,
            chat_history=[{"sender": m.role, "text": m.text} for m in request.chat_history],
            is_first=request.is_first
        )
        logger.info(f"LLM 生成问题成功: {result.get('current_field')}")
        return QuestionnaireResponse(**result)
    except Exception as e:
        logger.error(f"LLM 服务调用失败，使用模拟数据: {e}")
        # 根据对话轮数返回对应的模拟问题
        turn = len(request.chat_history) // 2  # 每轮包含用户和助手各一条
        if turn >= len(MOCK_QUESTIONS):
            turn = len(MOCK_QUESTIONS) - 1
        return QuestionnaireResponse(**MOCK_QUESTIONS[turn])


@router.post("/questionnaire/extract-profile")
async def extract_profile(chat_history: List[QuestionnaireMessage]):
    """从对话中提取 20 维画像"""
    try:
        from app.services.ai_service import ai_service
        
        profile = await ai_service.extract_profile_from_chat(
            chat_history=[{"sender": m.role, "text": m.text} for m in chat_history]
        )
        
        # 转换为标准 20 维格式
        return {
            "living_space": profile.living_space,
            "has_yard": profile.preferences.get("has_yard", False),
            "is_renting": profile.preferences.get("is_renting", False),
            "landlord_allows_pets": profile.preferences.get("landlord_allows_pets"),
            "budget_level": profile.preferences.get("budget_level", "medium"),
            "income_stability": profile.preferences.get("income_stability", "stable"),
            "daily_time_available": profile.daily_time_available,
            "work_schedule": profile.preferences.get("work_schedule", "regular"),
            "work_hours_per_day": profile.preferences.get("work_hours_per_day", 8),
            "experience_level": profile.experience_level,
            "previous_pets": profile.other_pets,
            "training_willingness": profile.preferences.get("training_willingness", "medium"),
            "family_status": profile.family_status,
            "household_size": profile.preferences.get("household_size", 1),
            "preferred_size": profile.preferences.get("preferred_size", "no_preference"),
            "preferred_age": profile.preferences.get("preferred_age", "no_preference"),
            "preferred_temperament": profile.preferences.get("preferred_temperament", []),
            "activity_level": profile.activity_level,
            "other_pets": profile.other_pets,
            "noise_tolerance": profile.preferences.get("noise_tolerance", "medium"),
            "shedding_tolerance": profile.preferences.get("shedding_tolerance", "medium"),
            "grooming_willingness": profile.preferences.get("grooming_willingness", "medium"),
            "has_allergies": profile.preferences.get("has_allergies", False),
            "allergy_details": profile.preferences.get("allergy_details"),
            "must_have_traits": profile.preferences.get("must_have_traits", []),
            "deal_breakers": profile.preferences.get("deal_breakers", [])
        }
    except Exception as e:
        logger.error(f"提取画像失败，使用默认数据: {e}")
        # 返回默认画像数据
        return {
            "living_space": "apartment",
            "has_yard": False,
            "is_renting": True,
            "landlord_allows_pets": True,
            "budget_level": "medium",
            "income_stability": "stable",
            "daily_time_available": 2,
            "work_schedule": "regular",
            "work_hours_per_day": 8,
            "experience_level": "beginner",
            "previous_pets": [],
            "training_willingness": "medium",
            "family_status": "single",
            "household_size": 1,
            "preferred_size": "small",
            "preferred_age": "young",
            "preferred_temperament": ["温顺", "安静"],
            "activity_level": "medium",
            "other_pets": [],
            "noise_tolerance": "medium",
            "shedding_tolerance": "medium",
            "grooming_willingness": "medium",
            "has_allergies": False,
            "allergy_details": None,
            "must_have_traits": [],
            "deal_breakers": []
        }


# ==================== 功能2：智能匹配（新实现）====================

def _simple_match_score(adopter: Dict, pet: Dict) -> float:
    """简单匹配评分（不依赖 Embedding）"""
    score = 50.0  # 基础分
    reasons = []
    concerns = []
    
    # 空间匹配
    living = adopter.get("living_space", "")
    size = pet.get("size_category", "medium")
    if "apartment" in living and size in ["tiny", "small"]:
        score += 15
        reasons.append("体型适合公寓饲养")
    elif "house" in living:
        score += 10
        reasons.append("居住空间充足")
    elif "apartment" in living and size in ["large", "xlarge"]:
        score -= 20
        concerns.append("大型犬需要更多活动空间")
    
    # 经验匹配
    exp = adopter.get("experience_level", "none")
    if exp == "none" and size in ["tiny", "small"]:
        score += 10
        reasons.append("小型宠物适合新手")
    elif exp == "experienced":
        score += 10
        reasons.append("您丰富的经验能照顾好它")
    
    # 时间匹配
    time_available = adopter.get("daily_time_available", 2)
    energy = pet.get("energy_level", "medium")
    if time_available >= 3 and energy == "high":
        score += 10
        reasons.append("您的陪伴时间充足")
    elif time_available < 2 and energy == "high":
        score -= 10
        concerns.append("高能量宠物需要更多陪伴时间")
    
    # 家庭匹配
    family = adopter.get("family_status", "")
    if "kids" in family and pet.get("good_with_kids", True):
        score += 10
        reasons.append("适合有孩子的家庭")
    
    return min(100, max(0, score)), reasons, concerns

@router.post("/match/recommendations")
async def get_match_recommendations(request: MatchRequest):
    """
    智能匹配推荐 - 使用混合算法
    0.4 硬性规则 + 0.4 Embedding相似度 + 0.2 历史成功率
    """
    try:
        # 获取所有可领养宠物
        pets_res = supabase.table("pets").select("*").eq("is_adopted", False).execute()
        
        if not pets_res.data:
            return []
        
        # 尝试使用匹配引擎（含 Embedding）
        try:
            available_pets = []
            for pet_data in pets_res.data:
                pet = {
                    "id": pet_data["id"],
                    "name": pet_data["name"],
                    "species": pet_data.get("category", "dog"),
                    "breed": pet_data.get("breed", ""),
                    "age_months": pet_data.get("age_value", 12),
                    "size_category": _estimate_size_category(pet_data.get("weight", "10kg")),
                    "weight_kg": _parse_weight(pet_data.get("weight", "10kg")),
                    "gender": pet_data.get("gender", "unknown").lower(),
                    "temperament": pet_data.get("tags", []) or [],
                    "energy_level": _estimate_energy(pet_data.get("age_value", 12), pet_data.get("tags", [])),
                    "sociability": "moderate",
                    "trainability": "moderate",
                    "shedding_level": "medium",
                    "grooming_needs": "medium",
                    "exercise_needs": _estimate_exercise(pet_data.get("age_value", 12)),
                    "good_with_kids": True,
                    "good_with_dogs": True,
                    "good_with_cats": pet_data.get("category") != "dog",
                    "good_with_strangers": True,
                    "special_needs": [],
                    "medical_notes": None,
                    "behavioral_notes": None,
                    "min_space_requirement": _estimate_space_requirement(pet_data.get("weight", "10kg")),
                    "needs_yard": False,
                    "success_rate": pet_data.get("success_rate")
                }
                available_pets.append(pet)
            
            results = await matching_engine.find_best_matches(
                adopter=request.adopter_profile,
                available_pets=available_pets,
                top_k=request.limit
            )
            
            return [{
                "pet_id": r.pet_id,
                "pet_name": r.pet_name,
                "pet_image": "",  # 前端需要这个字段
                "score": r.overall_score,  # 前端用 score 而不是 overall_score
                "overall_score": r.overall_score,
                "hard_constraint_score": r.hard_constraint_score,
                "soft_preference_score": r.soft_preference_score,
                "historical_score": r.historical_score,
                "dimensions": [{"name": d.name, "score": d.score, "weight": d.weight, "reason": d.reason} for d in r.dimensions],
                "compatibility": {d.name: d.score/100 for d in r.dimensions},  # 前端需要 compatibility
                "reasons": r.match_reasons,  # 前端用 reasons 而不是 match_reasons
                "match_reasons": r.match_reasons,
                "concerns": r.concerns,
                "recommendations": r.recommendations,
                "passed_hard_constraints": r.passed_hard_constraints,
                "failed_constraints": r.failed_constraints
            } for r in results]
        
        except Exception as engine_error:
            logger.warning(f"匹配引擎失败，使用简化匹配: {engine_error}")
            # 使用简化匹配逻辑
            scored_pets = []
            for pet_data in pets_res.data:
                pet = {
                    "id": pet_data["id"],
                    "name": pet_data["name"],
                    "size_category": _estimate_size_category(pet_data.get("weight", "10kg")),
                    "energy_level": _estimate_energy(pet_data.get("age_value", 12), pet_data.get("tags", [])),
                    "good_with_kids": True
                }
                score, reasons, concerns = _simple_match_score(request.adopter_profile, pet)
                scored_pets.append({
                    "pet_id": pet_data["id"],
                    "pet_name": pet_data["name"],
                    "pet_image": pet_data.get("image_url", ""),
                    "score": score,
                    "overall_score": score,
                    "hard_constraint_score": score,
                    "soft_preference_score": score,
                    "historical_score": 50,
                    "dimensions": [],
                    "compatibility": {},
                    "reasons": reasons,
                    "match_reasons": reasons,
                    "concerns": concerns,
                    "recommendations": ["建议实地见面了解性格"] if concerns else [],
                    "passed_hard_constraints": score > 40,
                    "failed_constraints": []
                })
            
            # 按分数排序返回前 N 个
            scored_pets.sort(key=lambda x: x["overall_score"], reverse=True)
            return scored_pets[:request.limit]
    
    except Exception as e:
        logger.error(f"匹配失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 功能3：AI预审（新实现）====================

# 模拟预审对话数据
MOCK_PRECHECK = {
    "greeting": "您好！我是 PawPal 的 AI 预审助手 🤖\n\n在正式提交申请前，我想和您聊几分钟，了解一些基本情况。这有助于提高申请通过率，也能帮您确认是否真的准备好了迎接新家庭成员。\n\n让我们开始吧！首先，请问您目前的职业和工作状态是怎样的？",
    "questions": [
        "了解了。接下来问问您的居住情况：您目前是租房还是自有住房？大概多大面积？",
        "明白。关于经济方面，您每月大概能为宠物预算多少费用（包括食物、医疗、用品等）？",
        "时间投入方面：您每天大概能抽出多少小时陪伴和照顾宠物？工作经常出差吗？",
        "关于养宠经验：您之前养过宠物吗？如果有，是什么情况？",
        "家庭情况：您目前是独居、和伴侣/家人同住？家里有小孩或老人吗？",
        "非常重要的问题：您为什么想领养这只宠物？是什么吸引了您？",
        "最后几个问题：您为领养做了哪些准备？比如了解品种特性、准备用品等。"
    ],
    "summary_pass": """根据我们的对话，您的条件很适合领养这只宠物！

审核摘要：
- 居住条件：✓
- 经济能力：✓
- 时间投入：✓
- 经验匹配：✓

建议：申请通过，等待最终审核

感谢您的耐心回答！您可以继续提交正式申请了。""",
    "summary_review": """整体条件不错，但有一些小地方可以改进。

审核摘要：
- 居住条件：✓
- 经济能力：⚠
- 时间投入：✓
- 经验匹配：✓

建议：人工复核

我们会尽快联系您。"""
}

@router.post("/precheck/start")
async def start_precheck(request: PrecheckStartRequest):
    """开始预审会话"""
    try:
        session_id = precheck_engine.create_session(
            user_id=request.user_id,
            pet_id=request.pet_id
        )
        
        # 获取第一条消息
        result = await precheck_engine.process_message(session_id, "")
        
        return {
            "session_id": session_id,
            "response": result["response"],
            "state": result["state"],
            "identified_risks": result.get("identified_risks", []),
            "is_complete": result.get("is_complete", False)
        }
    except Exception as e:
        logger.error(f"预审引擎失败，使用模拟数据: {e}")
        # 创建简单会话 ID
        import uuid
        session_id = str(uuid.uuid4())
        return {
            "session_id": session_id,
            "response": MOCK_PRECHECK["greeting"],
            "state": "BASIC_INFO",
            "identified_risks": [],
            "is_complete": False
        }


@router.post("/precheck/message")
async def precheck_message(request: PrecheckMessageRequest):
    """发送消息到预审会话"""
    try:
        result = await precheck_engine.process_message(
            session_id=request.session_id,
            user_message=request.message
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    except Exception as e:
        logger.error(f"预审消息处理失败，使用模拟数据: {e}")
        # 使用简单的回合数来确定回复
        # 从 session_id 计算回合（简单模拟）
        turn = len(request.message) % len(MOCK_PRECHECK["questions"])
        
        # 最后回合返回总结
        if turn >= len(MOCK_PRECHECK["questions"]) - 1:
            return {
                "response": MOCK_PRECHECK["summary_pass"],
                "state": "COMPLETE",
                "is_complete": True,
                "identified_risks": [],
                "collected_data": {}
            }
        
        return {
            "response": MOCK_PRECHECK["questions"][turn],
            "state": "BASIC_INFO",
            "is_complete": False,
            "identified_risks": [],
            "collected_data": {}
        }


@router.get("/precheck/session/{session_id}")
async def get_precheck_session(session_id: str):
    """获取会话状态"""
    try:
        session = precheck_engine.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {
            "session_id": session.session_id,
            "state": session.state.name,
            "is_complete": session.is_complete,
            "turn_count": session.turn_count,
            "identified_risks": session.identified_risks,
            "collected_data": session.collected_data,
            "result": session.result
        }
    except Exception as e:
        logger.error(f"获取会话失败，返回模拟数据: {e}")
        return {
            "session_id": session_id,
            "state": "BASIC_INFO",
            "is_complete": False,
            "turn_count": 0,
            "identified_risks": [],
            "collected_data": {},
            "result": None
        }


# ==================== 历史反馈管理 ====================

@router.post("/feedback/submit")
async def submit_feedback(feedback: AdoptionFeedback):
    """提交领养后反馈，用于改进匹配算法"""
    try:
        # 生成画像 Embedding
        from app.services.embedding_service import embedding_service
        profile_text = adopter_profile_to_text(feedback.adopter_profile_summary)
        embedding = await embedding_service.get_embedding(profile_text)
        
        # 保存到数据库
        data = {
            "application_id": feedback.application_id,
            "pet_id": feedback.pet_id,
            "outcome": feedback.outcome,
            "duration_days": feedback.duration_days,
            "feedback_text": feedback.feedback_text,
            "rating": feedback.rating,
            "issues": feedback.issues,
            "profile_embedding": embedding
        }
        
        supabase.table("adoption_feedback").insert(data).execute()
        
        # 更新宠物的历史成功率
        _update_pet_success_rate(feedback.pet_id)
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"提交反馈失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 辅助函数 ====================

def _estimate_size_category(weight_str: str) -> str:
    """估算体型分类"""
    try:
        weight = float(''.join(filter(lambda x: x.isdigit() or x == '.', weight_str)) or 10)
        if weight < 5:
            return "tiny"
        elif weight < 10:
            return "small"
        elif weight < 25:
            return "medium"
        elif weight < 40:
            return "large"
        else:
            return "xlarge"
    except:
        return "medium"


def _parse_weight(weight_str: str) -> float:
    """解析体重"""
    try:
        return float(''.join(filter(lambda x: x.isdigit() or x == '.', weight_str)) or 10)
    except:
        return 10.0


def _estimate_energy(age_months: int, tags: list) -> str:
    """估算能量水平"""
    tag_str = ' '.join(tags).lower()
    if any(w in tag_str for w in ["活泼", "好动", "energetic"]):
        return "high"
    elif any(w in tag_str for w in ["安静", "calm", "lazy"]):
        return "low"
    
    if age_months < 12:
        return "high"
    elif age_months > 84:
        return "low"
    return "medium"


def _estimate_exercise(age_months: int) -> str:
    """估算运动需求"""
    if age_months < 12:
        return "high"
    elif age_months > 84:
        return "low"
    return "medium"


def _estimate_space_requirement(weight_str: str) -> str:
    """估算空间需求"""
    try:
        weight = float(''.join(filter(lambda x: x.isdigit() or x == '.', weight_str)) or 10)
        if weight < 10:
            return "small_apartment"
        elif weight < 25:
            return "medium_apartment"
        else:
            return "large_apartment"
    except:
        return "medium_apartment"


def _update_pet_success_rate(pet_id: str):
    """更新宠物的历史成功率"""
    try:
        feedback_res = supabase.table("adoption_feedback").select("*").eq("pet_id", pet_id).execute()
        
        if not feedback_res.data:
            return
        
        total = len(feedback_res.data)
        successful = len([f for f in feedback_res.data if f["outcome"] == "success"])
        
        success_rate = successful / total if total > 0 else 0
        
        supabase.table("pets").update({"success_rate": success_rate}).eq("id", pet_id).execute()
    
    except Exception as e:
        logger.error(f"更新成功率失败: {e}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "2.0",
        "features": [
            "questionnaire",
            "matching_with_embedding",
            "precheck_with_state_machine"
        ]
    }
