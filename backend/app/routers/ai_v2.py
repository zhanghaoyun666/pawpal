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

@router.post("/questionnaire/next", response_model=QuestionnaireResponse)
async def get_next_question(request: QuestionnaireRequest):
    """获取智能问卷的下一个问题"""
    # 复用原有的 LLM 驱动问卷
    from app.services.ai_service import ai_service
    
    result = await ai_service.generate_next_question(
        user_id=request.user_id,
        current_profile=request.current_profile,
        chat_history=[{"sender": m.role, "text": m.text} for m in request.chat_history],
        is_first=request.is_first
    )
    return QuestionnaireResponse(**result)


@router.post("/questionnaire/extract-profile")
async def extract_profile(chat_history: List[QuestionnaireMessage]):
    """从对话中提取 20 维画像"""
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


# ==================== 功能2：智能匹配（新实现）====================

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
        
        # 转换为标准 PetProfile 格式
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
                "success_rate": pet_data.get("success_rate")  # 历史成功率
            }
            available_pets.append(pet)
        
        # 使用匹配引擎计算
        results = await matching_engine.find_best_matches(
            adopter=request.adopter_profile,
            available_pets=available_pets,
            top_k=request.limit
        )
        
        # 转换为响应格式
        return [{
            "pet_id": r.pet_id,
            "pet_name": r.pet_name,
            "overall_score": r.overall_score,
            "hard_constraint_score": r.hard_constraint_score,
            "soft_preference_score": r.soft_preference_score,
            "historical_score": r.historical_score,
            "dimensions": [{"name": d.name, "score": d.score, "weight": d.weight, "reason": d.reason} for d in r.dimensions],
            "match_reasons": r.match_reasons,
            "concerns": r.concerns,
            "recommendations": r.recommendations,
            "passed_hard_constraints": r.passed_hard_constraints,
            "failed_constraints": r.failed_constraints
        } for r in results]
    
    except Exception as e:
        logger.error(f"匹配失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 功能3：AI预审（新实现）====================

@router.post("/precheck/start")
async def start_precheck(request: PrecheckStartRequest):
    """开始预审会话"""
    session_id = precheck_engine.create_session(
        user_id=request.user_id,
        pet_id=request.pet_id
    )
    
    # 获取第一条消息
    result = await precheck_engine.process_message(session_id, "")
    
    return {
        "session_id": session_id,
        "response": result["response"],
        "state": result["state"]
    }


@router.post("/precheck/message")
async def precheck_message(request: PrecheckMessageRequest):
    """发送消息到预审会话"""
    result = await precheck_engine.process_message(
        session_id=request.session_id,
        user_message=request.message
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/precheck/session/{session_id}")
async def get_precheck_session(session_id: str):
    """获取会话状态"""
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
