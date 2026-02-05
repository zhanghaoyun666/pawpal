"""
AI 功能路由
提供智能问卷、匹配推荐、预审助手 API
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from pydantic import BaseModel
import logging

from app.services.ai_service import ai_service, UserProfile, PetProfile
from app.database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


# ==================== 数据模型 ====================

class QuestionnaireMessage(BaseModel):
    """问卷消息"""
    role: str  # "user" | "assistant"
    text: str


class QuestionnaireRequest(BaseModel):
    """智能问卷请求"""
    user_id: str
    chat_history: List[QuestionnaireMessage]
    current_profile: Optional[Dict] = {}
    is_first: bool = False


class QuestionnaireResponse(BaseModel):
    """智能问卷响应"""
    next_question: str
    is_complete: bool
    current_field: str
    suggested_options: List[str]
    explanation: str


class ProfileExtractRequest(BaseModel):
    """提取画像请求"""
    chat_history: List[QuestionnaireMessage]


class MatchRequest(BaseModel):
    """匹配请求"""
    user_id: str
    user_profile: Dict
    limit: int = 3


class MatchResponse(BaseModel):
    """匹配响应"""
    pet_id: str
    pet_name: str
    pet_image: str
    score: float
    reasons: List[str]
    concerns: List[str]
    compatibility: Dict[str, float]


class PreCheckRequest(BaseModel):
    """预审请求"""
    application_id: str
    application_data: Dict
    user_profile: Dict
    pet_id: str


class PreCheckResponse(BaseModel):
    """预审响应"""
    passed: bool
    score: float
    risk_level: str
    risk_points: List[Dict[str, str]]
    suggestions: List[str]
    auto_approved: bool
    review_report: str


# ==================== 功能1：智能问卷 API ====================

@router.post("/questionnaire/next", response_model=QuestionnaireResponse)
async def get_next_question(request: QuestionnaireRequest):
    """
    获取智能问卷的下一个问题
    
    示例请求：
    {
        "user_id": "user_123",
        "chat_history": [
            {"role": "assistant", "text": "您好！我是您的领养顾问..."},
            {"role": "user", "text": "我住在公寓里"}
        ],
        "current_profile": {"living_space": "apartment"},
        "is_first": false
    }
    """
    try:
        result = await ai_service.generate_next_question(
            user_id=request.user_id,
            current_profile=request.current_profile,
            chat_history=[{"sender": m.role, "text": m.text} for m in request.chat_history],
            is_first=request.is_first
        )
        return QuestionnaireResponse(**result)
    except Exception as e:
        logger.error(f"生成问卷问题失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI 服务错误: {str(e)}")


@router.post("/questionnaire/extract-profile")
async def extract_user_profile(request: ProfileExtractRequest):
    """
    从对话历史中提取用户画像
    """
    try:
        profile = await ai_service.extract_profile_from_chat(
            chat_history=[{"sender": m.role, "text": m.text} for m in request.chat_history]
        )
        return {
            "living_space": profile.living_space,
            "experience_level": profile.experience_level,
            "daily_time_available": profile.daily_time_available,
            "family_status": profile.family_status,
            "other_pets": profile.other_pets,
            "activity_level": profile.activity_level,
            "preferences": profile.preferences
        }
    except Exception as e:
        logger.error(f"提取用户画像失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI 服务错误: {str(e)}")


# ==================== 功能2：智能匹配推荐 API ====================

@router.post("/match/recommendations", response_model=List[MatchResponse])
async def get_match_recommendations(request: MatchRequest):
    """
    获取智能匹配推荐
    
    根据用户画像推荐最适合的宠物
    """
    try:
        # 获取所有可领养宠物
        pets_res = supabase.table("pets").select("*").eq("is_adopted", False).execute()
        
        if not pets_res.data:
            return []
        
        # 转换为 PetProfile
        available_pets = []
        for pet_data in pets_res.data:
            # 解析标签获取更多信息
            tags = pet_data.get("tags", []) or []
            temperament = []
            special_needs = []
            
            for tag in tags:
                if any(word in tag for word in ["温顺", "活泼", "安静", "友好", "独立"]):
                    temperament.append(tag)
                elif any(word in tag for word in ["需要", "注意", "特殊"]):
                    special_needs.append(tag)
            
            pet = PetProfile(
                id=pet_data["id"],
                name=pet_data["name"],
                species=pet_data.get("category", "dog"),
                breed=pet_data.get("breed", ""),
                age_months=pet_data.get("age_value", 12),
                size=_estimate_size(pet_data.get("weight", "10kg")),
                energy_level=_estimate_energy_level(pet_data.get("age_value", 12), tags),
                temperament=temperament,
                special_needs=special_needs,
                good_with_kids="小孩" not in str(tags) or "适合家庭" in str(tags),
                good_with_pets=True,  # 默认假设
                training_level="basic"
            )
            available_pets.append(pet)
        
        # 创建用户画像
        user_profile = UserProfile(
            living_space=request.user_profile.get("living_space", ""),
            experience_level=request.user_profile.get("experience_level", ""),
            daily_time_available=request.user_profile.get("daily_time_available", 2),
            family_status=request.user_profile.get("family_status", ""),
            other_pets=request.user_profile.get("other_pets", []),
            activity_level=request.user_profile.get("activity_level", ""),
            preferences=request.user_profile.get("preferences", {})
        )
        
        # 获取推荐
        recommendations = await ai_service.get_top_recommendations(
            user_profile=user_profile,
            available_pets=available_pets,
            top_n=request.limit
        )
        
        # 构建响应
        results = []
        for match in recommendations:
            # 获取宠物详情
            pet_data = next((p for p in pets_res.data if p["id"] == match.pet_id), None)
            if pet_data:
                results.append(MatchResponse(
                    pet_id=match.pet_id,
                    pet_name=pet_data["name"],
                    pet_image=pet_data.get("image_url", ""),
                    score=match.score,
                    reasons=match.reasons,
                    concerns=match.concerns,
                    compatibility=match.compatibility_breakdown
                ))
        
        return results
    
    except Exception as e:
        logger.error(f"获取推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI 服务错误: {str(e)}")


@router.post("/match/single")
async def calculate_single_match(
    user_profile: Dict,
    pet_id: str
):
    """
    计算单个宠物的匹配度
    """
    try:
        # 获取宠物信息
        pet_res = supabase.table("pets").select("*").eq("id", pet_id).execute()
        if not pet_res.data:
            raise HTTPException(status_code=404, detail="宠物不存在")
        
        pet_data = pet_res.data[0]
        tags = pet_data.get("tags", []) or []
        
        pet = PetProfile(
            id=pet_data["id"],
            name=pet_data["name"],
            species=pet_data.get("category", "dog"),
            breed=pet_data.get("breed", ""),
            age_months=pet_data.get("age_value", 12),
            size=_estimate_size(pet_data.get("weight", "10kg")),
            energy_level=_estimate_energy_level(pet_data.get("age_value", 12), tags),
            temperament=tags,
            special_needs=[],
            good_with_kids=True,
            good_with_pets=True,
            training_level="basic"
        )
        
        user_prof = UserProfile(
            living_space=user_profile.get("living_space", ""),
            experience_level=user_profile.get("experience_level", ""),
            daily_time_available=user_profile.get("daily_time_available", 2),
            family_status=user_profile.get("family_status", ""),
            other_pets=user_profile.get("other_pets", []),
            activity_level=user_profile.get("activity_level", ""),
            preferences=user_profile.get("preferences", {})
        )
        
        match = await ai_service.calculate_match_score(user_prof, pet)
        
        return {
            "pet_id": match.pet_id,
            "score": match.score,
            "reasons": match.reasons,
            "concerns": match.concerns,
            "compatibility": match.compatibility_breakdown
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算匹配度失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI 服务错误: {str(e)}")


# ==================== 功能3：AI 预审助手 API ====================

@router.post("/precheck", response_model=PreCheckResponse)
async def precheck_application(request: PreCheckRequest):
    """
    AI 自动预审申请
    
    返回审核结果、风险等级和建议
    """
    try:
        # 获取宠物信息
        pet_res = supabase.table("pets").select("*").eq("id", request.pet_id).execute()
        if not pet_res.data:
            raise HTTPException(status_code=404, detail="宠物不存在")
        
        pet_data = pet_res.data[0]
        tags = pet_data.get("tags", []) or []
        
        pet = PetProfile(
            id=pet_data["id"],
            name=pet_data["name"],
            species=pet_data.get("category", "dog"),
            breed=pet_data.get("breed", ""),
            age_months=pet_data.get("age_value", 12),
            size=_estimate_size(pet_data.get("weight", "10kg")),
            energy_level=_estimate_energy_level(pet_data.get("age_value", 12), tags),
            temperament=tags,
            special_needs=[],
            good_with_kids=True,
            good_with_pets=True,
            training_level="basic"
        )
        
        # 创建用户画像
        user_profile = UserProfile(
            living_space=request.user_profile.get("living_space", ""),
            experience_level=request.user_profile.get("experience_level", ""),
            daily_time_available=request.user_profile.get("daily_time_available", 2),
            family_status=request.user_profile.get("family_status", ""),
            other_pets=request.user_profile.get("other_pets", []),
            activity_level=request.user_profile.get("activity_level", ""),
            preferences=request.user_profile.get("preferences", {})
        )
        
        # 获取用户历史申请
        history_res = supabase.table("applications").select("*").eq("user_id", request.application_data.get("user_id")).execute()
        user_history = history_res.data if history_res.data else []
        
        # 执行预审
        precheck_result = await ai_service.precheck_application(
            application_data=request.application_data,
            user_profile=user_profile,
            pet=pet,
            user_history=user_history
        )
        
        # 生成审核报告
        review_report = await ai_service.generate_review_report(
            application_id=request.application_id,
            precheck_result=precheck_result
        )
        
        return PreCheckResponse(
            passed=precheck_result.passed,
            score=precheck_result.score,
            risk_level=precheck_result.risk_level,
            risk_points=precheck_result.risk_points,
            suggestions=precheck_result.suggestions,
            auto_approved=precheck_result.auto_approved,
            review_report=review_report
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预审失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI 服务错误: {str(e)}")


@router.get("/precheck/status/{application_id}")
async def get_precheck_status(application_id: str):
    """
    获取预审状态
    """
    try:
        # 从数据库获取预审结果
        result_res = supabase.table("ai_precheck_results").select("*").eq("application_id", application_id).execute()
        
        if not result_res.data:
            return {"status": "pending", "message": "预审尚未完成"}
        
        return result_res.data[0]
    
    except Exception as e:
        logger.error(f"获取预审状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ==================== 辅助函数 ====================

def _estimate_size(weight_str: str) -> str:
    """根据体重估算体型"""
    try:
        # 提取数字
        weight = float(''.join(filter(lambda x: x.isdigit() or x == '.', weight_str)) or 10)
        
        if weight < 10:
            return "small"
        elif weight < 25:
            return "medium"
        else:
            return "large"
    except:
        return "medium"


def _estimate_energy_level(age_months: int, tags: List[str]) -> str:
    """估算能量水平"""
    # 根据标签判断
    tag_str = ' '.join(tags).lower()
    if any(word in tag_str for word in ["活泼", "好动", "energetic", "active"]):
        return "high"
    elif any(word in tag_str for word in ["安静", "calm", "lazy", " mellow"]):
        return "low"
    
    # 根据年龄判断
    if age_months < 12:  # 幼年
        return "high"
    elif age_months > 84:  # 老年（7岁以上）
        return "low"
    
    return "medium"


# ==================== 健康检查 ====================

@router.get("/health")
async def ai_health_check():
    """AI 服务健康检查"""
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    
    return {
        "status": "healthy" if api_key else "mock_mode",
        "model": ai_service.model,
        "api_configured": bool(api_key)
    }
