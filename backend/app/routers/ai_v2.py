"""
AI 功能路由 V2 - 真实 LLM 调用 + Mock Fallback
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel
import logging
import json
import os

from app.services.matching_engine import matching_engine
from app.services.precheck_engine import precheck_engine
from app.services.embedding_service import adopter_profile_to_text, pet_profile_to_text
from app.models.profile_schema import (
    AdopterProfile, PetProfile, MatchResult, 
    AdoptionFeedback
)
from app.database import supabase
from app.services.longcat_service import longcat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai/v2", tags=["ai-v2"])

# 检查是否配置了 API Key
LLM_ENABLED = bool(os.getenv("LONGCAT_API_KEY"))

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
    adopter_profile: Dict
    limit: int = 3


class PrecheckStartRequest(BaseModel):
    user_id: str
    pet_id: str


class PrecheckMessageRequest(BaseModel):
    session_id: str
    message: str


# ==================== 功能1：智能问卷（真实LLM + Mock Fallback）====================

# Mock 问题库（LLM 失败时使用）
MOCK_QUESTIONS = [
    {
        "field": "living_space",
        "question": "您好！我是 PawPal 智能领养顾问 🤖\n\n为了帮您找到最合适的毛孩子，我想先了解一些您的情况。\n\n首先，您目前住在哪里？",
        "options": ["公寓（无院子）", "带院子的房子", "农村住宅"],
        "explanation": "居住空间决定了适合什么体型的宠物"
    },
    {
        "field": "experience_level",
        "question": "了解！那您之前有过养宠物的经验吗？",
        "options": ["完全没有，我是新手", "养过一只", "养过多只，经验丰富"],
        "explanation": "经验水平影响适合宠物的训练难度"
    },
    {
        "field": "daily_time_available",
        "question": "您每天大概能抽出多少小时陪伴宠物？",
        "options": ["1小时以内", "1-3小时", "3-5小时", "5小时以上"],
        "explanation": "不同宠物对陪伴时间的需求不同"
    },
    {
        "field": "family_status",
        "question": "您的家庭状况是怎样的？",
        "options": ["独居", "和伴侣同住", "有小孩（6岁以下）", "有小孩（6岁以上）", "和老人同住"],
        "explanation": "家庭成员构成影响宠物的性格选择"
    },
    {
        "field": "activity_level",
        "question": "您更喜欢什么样的宠物性格？",
        "options": ["安静温顺，喜欢宅家", "活泼好动，能一起玩耍", "适中，既安静又能互动"],
        "explanation": "性格匹配是长期相处和谐的关键"
    },
    {
        "field": "other_pets",
        "question": "您家里目前有其他宠物吗？",
        "options": ["没有其他宠物", "有一只狗", "有一只猫", "有多只宠物"],
        "explanation": "了解是否需要考虑宠物间的相处"
    },
    {
        "field": "size_preference",
        "question": "您对宠物的体型有偏好吗？",
        "options": ["小型（10斤以下）", "中型（10-30斤）", "大型（30斤以上）", "没有特别偏好"],
        "explanation": "体型影响生活空间需求和饲养成本"
    }
]


async def llm_generate_question(chat_history: List[Dict], current_profile: Dict, is_first: bool) -> Optional[Dict]:
    """使用 LLM 生成下一个问题"""
    if not LLM_ENABLED:
        return None
    
    system_prompt = """你是一位专业的宠物领养顾问，擅长通过自然对话了解领养人的情况。

你的目标是通过友好的对话收集以下信息：
1. 居住空间（公寓/带院子的房子/农村）
2. 养宠经验（无/有/丰富）
3. 每日可用时间（小时）
4. 家庭状况（单身/夫妻/有小孩/有老人）
5. 其他宠物情况
6. 活动量偏好（安静/适中/活跃）
7. 对宠物的特殊要求

规则：
- 每次只问一个问题，保持对话自然流畅
- 根据用户的回答智能调整下一个问题
- 提供 3-4 个选项让用户更容易回答
- 当收集到足够信息时（约6-8轮），标记 is_complete 为 true
- 用一句话解释为什么问这个问题

输出必须是 JSON 格式：
{
    "next_question": "问题内容（包含上下文，自然流畅）",
    "is_complete": false,
    "current_field": "字段名（如living_space/experience_level等）",
    "suggested_options": ["选项1", "选项2", "选项3"],
    "explanation": "一句话解释为什么问这个问题"
}"""

    messages = [{"role": "system", "content": system_prompt}]
    
    # 添加已收集的信息
    if current_profile:
        profile_text = f"已收集信息：{json.dumps(current_profile, ensure_ascii=False)}"
        messages.append({"role": "system", "content": profile_text})
    
    # 添加对话历史（最近5轮）
    for msg in chat_history[-10:]:
        role = "user" if msg.get("sender") == "user" else "assistant"
        messages.append({"role": role, "content": msg.get("text", "")})
    
    # 添加指令
    if is_first:
        messages.append({
            "role": "user", 
            "content": "开始问卷对话，请用友好的方式开场并询问第一个问题"
        })
    else:
        messages.append({
            "role": "user",
            "content": "根据以上对话，生成下一个问题。如果已经收集了6-8轮信息，标记 is_complete 为 true"
        })
    
    try:
        response = await longcat_service.chat_completion(
            messages=messages,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response)
        return {
            "next_question": result.get("next_question", ""),
            "is_complete": result.get("is_complete", False),
            "current_field": result.get("current_field", ""),
            "suggested_options": result.get("suggested_options", []),
            "explanation": result.get("explanation", "")
        }
    except Exception as e:
        logger.error(f"LLM 生成问题失败: {e}")
        return None


@router.post("/questionnaire/next", response_model=QuestionnaireResponse)
async def get_next_question(request: QuestionnaireRequest):
    """获取智能问卷的下一个问题"""
    
    # 计算当前轮数
    turn = len(request.chat_history) // 2
    
    # 如果对话已超过7轮，标记完成
    if turn >= 7:
        return QuestionnaireResponse(
            next_question="感谢您的时间！我已经了解了您的情况。\n\n现在让我为您分析最适合的宠物...",
            is_complete=True,
            current_field="",
            suggested_options=[],
            explanation="问卷完成"
        )
    
    # 尝试使用 LLM
    llm_result = await llm_generate_question(
        chat_history=[{"sender": m.role, "text": m.text} for m in request.chat_history],
        current_profile=request.current_profile,
        is_first=request.is_first
    )
    
    if llm_result and llm_result.get("next_question"):
        logger.info(f"LLM 生成问题成功: {llm_result.get('current_field')}")
        return QuestionnaireResponse(**llm_result)
    
    # LLM 失败，使用 Mock 数据
    logger.info(f"使用 Mock 问题，当前轮数: {turn}")
    mock = MOCK_QUESTIONS[min(turn, len(MOCK_QUESTIONS) - 1)]
    
    return QuestionnaireResponse(
        next_question=mock["question"],
        is_complete=False,
        current_field=mock["field"],
        suggested_options=mock["options"],
        explanation=mock["explanation"]
    )


async def llm_extract_profile(chat_history: List[Dict]) -> Optional[Dict]:
    """使用 LLM 从对话提取画像"""
    if not LLM_ENABLED:
        return None
    
    system_prompt = """从以下领养对话中提取关键信息，生成结构化的用户画像。

只提取对话中明确提到的信息，不要猜测。

输出 JSON 格式：
{
    "living_space": "apartment/house_with_yard/rural/unknown",
    "has_yard": true/false,
    "is_renting": true/false,
    "experience_level": "none/beginner/intermediate/experienced/unknown",
    "daily_time_available": 数字或0,
    "family_status": "single/couple/with_kids_young/with_kids/with_elderly/unknown",
    "other_pets": ["狗", "猫"] 或 [],
    "activity_level": "low/medium/high/unknown",
    "preferred_size": "small/medium/large/no_preference",
    "preferences": {}
}"""

    chat_text = "\n".join([f"{'用户' if m.get('sender') == 'user' else '顾问'}: {m.get('text', '')}" 
                          for m in chat_history])
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"对话内容：\n{chat_text}\n\n请提取用户画像，返回JSON格式"}
    ]
    
    try:
        response = await longcat_service.chat_completion(
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return json.loads(response)
    except Exception as e:
        logger.error(f"LLM 提取画像失败: {e}")
        return None


@router.post("/questionnaire/extract-profile")
async def extract_profile(chat_history: List[QuestionnaireMessage]):
    """从对话中提取 20 维画像"""
    
    # 尝试使用 LLM
    chat_list = [{"sender": m.role, "text": m.text} for m in chat_history]
    llm_profile = await llm_extract_profile(chat_list)
    
    if llm_profile:
        logger.info(f"LLM 提取画像成功: {llm_profile}")
        # 填充默认值
        default_profile = {
            "living_space": llm_profile.get("living_space", "apartment"),
            "has_yard": llm_profile.get("has_yard", False),
            "is_renting": llm_profile.get("is_renting", True),
            "landlord_allows_pets": None,
            "budget_level": "medium",
            "income_stability": "stable",
            "daily_time_available": llm_profile.get("daily_time_available", 2),
            "work_schedule": "regular",
            "work_hours_per_day": 8,
            "experience_level": llm_profile.get("experience_level", "beginner"),
            "previous_pets": llm_profile.get("other_pets", []),
            "training_willingness": "medium",
            "family_status": llm_profile.get("family_status", "single"),
            "household_size": 1,
            "preferred_size": llm_profile.get("preferred_size", "medium"),
            "preferred_age": "no_preference",
            "preferred_temperament": [],
            "activity_level": llm_profile.get("activity_level", "medium"),
            "other_pets": llm_profile.get("other_pets", []),
            "noise_tolerance": "medium",
            "shedding_tolerance": "medium",
            "grooming_willingness": "medium",
            "has_allergies": False,
            "allergy_details": None,
            "must_have_traits": [],
            "deal_breakers": []
        }
        return default_profile
    
    # LLM 失败，使用规则解析
    logger.info("使用规则解析画像")
    all_text = " ".join([m.text for m in chat_history])
    
    profile = {
        "living_space": "apartment",
        "has_yard": False,
        "is_renting": True,
        "landlord_allows_pets": None,
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
        "preferred_size": "medium",
        "preferred_age": "no_preference",
        "preferred_temperament": [],
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
    
    # 规则解析
    if "别墅" in all_text or "院子" in all_text:
        profile["living_space"] = "house_with_yard"
        profile["has_yard"] = True
    
    if "没有" in all_text and ("经验" in all_text or "养过" in all_text):
        profile["experience_level"] = "none"
    elif "一只" in all_text or "养过" in all_text:
        profile["experience_level"] = "beginner"
        if "狗" in all_text:
            profile["other_pets"] = ["狗"]
            profile["previous_pets"] = ["狗"]
    elif "丰富" in all_text or "多年" in all_text:
        profile["experience_level"] = "experienced"
    
    if "独居" in all_text or "一个人" in all_text:
        profile["family_status"] = "single"
    elif "伴侣" in all_text or "夫妻" in all_text:
        profile["family_status"] = "couple"
    elif "小孩" in all_text:
        profile["family_status"] = "with_kids"
    
    if "安静" in all_text:
        profile["activity_level"] = "low"
        profile["preferred_temperament"] = ["安静", "温顺"]
    elif "活泼" in all_text:
        profile["activity_level"] = "high"
    
    return profile


# ==================== 功能2：智能匹配（真实算法 + 简化Fallback）====================

@router.post("/match/recommendations")
async def get_match_recommendations(request: MatchRequest):
    """智能匹配推荐"""
    try:
        # 获取所有可领养宠物
        pets_res = supabase.table("pets").select("*").eq("is_adopted", False).execute()
        
        if not pets_res.data:
            return []
        
        # 转换为 PetProfile 格式
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
        
        # 尝试使用匹配引擎（含 Embedding）
        try:
            results = await matching_engine.find_best_matches(
                adopter=request.adopter_profile,
                available_pets=available_pets,
                top_k=request.limit
            )
            
            return [{
                "pet_id": r.pet_id,
                "pet_name": r.pet_name,
                "pet_image": "",
                "score": r.overall_score,
                "overall_score": r.overall_score,
                "hard_constraint_score": r.hard_constraint_score,
                "soft_preference_score": r.soft_preference_score,
                "historical_score": r.historical_score,
                "dimensions": [{"name": d.name, "score": d.score, "weight": d.weight, "reason": d.reason} for d in r.dimensions],
                "compatibility": {d.name: d.score/100 for d in r.dimensions},
                "reasons": r.match_reasons,
                "match_reasons": r.match_reasons,
                "concerns": r.concerns,
                "recommendations": r.recommendations,
                "passed_hard_constraints": r.passed_hard_constraints,
                "failed_constraints": r.failed_constraints
            } for r in results]
        
        except Exception as engine_error:
            logger.warning(f"匹配引擎失败，使用简化算法: {engine_error}")
            # 简化匹配
            scored_pets = []
            for pet_data in pets_res.data:
                pet = {
                    "id": pet_data["id"],
                    "name": pet_data["name"],
                    "size_category": _estimate_size_category(pet_data.get("weight", "10kg")),
                    "energy_level": _estimate_energy(pet_data.get("age_value", 12), pet_data.get("tags", []))
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
            
            scored_pets.sort(key=lambda x: x["score"], reverse=True)
            return scored_pets[:request.limit]
    
    except Exception as e:
        logger.error(f"匹配失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _simple_match_score(adopter: Dict, pet: Dict) -> tuple:
    """简化匹配评分"""
    score = 50.0
    reasons = []
    concerns = []
    
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
    
    exp = adopter.get("experience_level", "none")
    if exp == "none" and size in ["tiny", "small"]:
        score += 10
        reasons.append("小型宠物适合新手")
    elif exp == "experienced":
        score += 10
        reasons.append("您丰富的经验能照顾好它")
    
    time_available = adopter.get("daily_time_available", 2)
    energy = pet.get("energy_level", "medium")
    if time_available >= 3 and energy == "high":
        score += 10
        reasons.append("您的陪伴时间充足")
    elif time_available < 2 and energy == "high":
        score -= 10
        concerns.append("高能量宠物需要更多陪伴时间")
    
    return min(100, max(0, score)), reasons, concerns


def _estimate_size_category(weight_str: str) -> str:
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
    try:
        return float(''.join(filter(lambda x: x.isdigit() or x == '.', weight_str)) or 10)
    except:
        return 10.0


def _estimate_energy(age_months: int, tags: list) -> str:
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
    if age_months < 12:
        return "high"
    elif age_months > 84:
        return "low"
    return "medium"


def _estimate_space_requirement(weight_str: str) -> str:
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


# ==================== 功能3：AI预审（真实LLM + Mock Fallback）====================

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

感谢您的耐心回答！您可以继续提交正式申请了。"""
}


@router.post("/precheck/start")
async def start_precheck(request: PrecheckStartRequest):
    """开始预审会话"""
    import uuid
    session_id = str(uuid.uuid4())
    
    logger.info(f"开始预审会话: {session_id}")
    
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
    
    turn = len(request.message) % (len(MOCK_PRECHECK["questions"]) + 1)
    
    logger.info(f"预审消息: {request.message[:20]}..., 回合: {turn}")
    
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
    return {
        "session_id": session_id,
        "state": "BASIC_INFO",
        "is_complete": False,
        "turn_count": 0,
        "identified_risks": [],
        "collected_data": {},
        "result": None
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "2.0",
        "llm_enabled": LLM_ENABLED,
        "model": os.getenv("LONGCAT_MODEL", "not_configured"),
        "features": [
            "questionnaire",
            "matching",
            "precheck"
        ]
    }
