"""
AI 服务核心模块 - 使用美团 LongCat 模型
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# 导入 LongCat 服务
from .longcat_service import longcat_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 从环境变量获取配置
AI_PROVIDER = os.getenv("AI_PROVIDER", "longcat")  # longcat / openai


@dataclass
class UserProfile:
    """用户画像数据类"""
    living_space: str = ""  # 居住空间
    experience_level: str = ""  # 经验
    daily_time_available: int = 0  # 每日可用时间
    family_status: str = ""  # 家庭状况
    other_pets: List[str] = None
    activity_level: str = ""  # 活动量
    preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.other_pets is None:
            self.other_pets = []
        if self.preferences is None:
            self.preferences = {}


@dataclass
class PetProfile:
    """宠物档案数据类"""
    id: str
    name: str
    species: str
    breed: str
    age_months: int
    size: str
    energy_level: str
    temperament: List[str] = None
    special_needs: List[str] = None
    good_with_kids: bool = True
    good_with_pets: bool = True
    training_level: str = "basic"
    
    def __post_init__(self):
        if self.temperament is None:
            self.temperament = []
        if self.special_needs is None:
            self.special_needs = []


@dataclass
class MatchResult:
    """匹配结果"""
    pet_id: str
    score: float
    reasons: List[str]
    concerns: List[str]
    compatibility_breakdown: Dict[str, float]


@dataclass
class PreCheckResult:
    """预审结果"""
    passed: bool
    score: float
    risk_level: str
    risk_points: List[Dict[str, str]]
    suggestions: List[str]
    auto_approved: bool


class AIService:
    """AI 服务类 - 统一封装，底层使用 LongCat"""
    
    def __init__(self):
        self.provider = AI_PROVIDER
        self.service = longcat_service  # 默认使用 LongCat
        logger.info(f"AI 服务初始化完成，使用提供商: {self.provider}")
    
    async def _call_llm(self, messages: List[Dict], temperature: float = 0.7, response_format: Optional[Dict] = None) -> str:
        """调用大模型 API"""
        return await self.service.chat_completion(
            messages=messages,
            temperature=temperature,
            response_format=response_format
        )
    
    # ==================== 功能1：智能问卷 ====================
    
    async def generate_next_question(
        self,
        user_id: str,
        current_profile: Dict,
        chat_history: List[Dict],
        is_first: bool = False
    ) -> Dict:
        """生成下一个问卷问题"""
        
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
- 提供选项让用户更容易回答
- 当收集到足够信息时，标记 is_complete 为 true
- 解释为什么问这个问题，增加用户信任

输出必须是 JSON 格式：
{
    "next_question": "问题内容",
    "is_complete": false,
    "current_field": "字段名",
    "suggested_options": ["选项1", "选项2"],
    "explanation": "为什么问这个问题"
}"""

        messages = [{"role": "system", "content": system_prompt}]
        
        profile_text = f"当前已收集的信息：{json.dumps(current_profile, ensure_ascii=False)}"
        messages.append({"role": "system", "content": profile_text})
        
        for msg in chat_history[-5:]:
            role = "user" if msg.get("sender") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("text", "")})
        
        if is_first:
            messages.append({
                "role": "user", 
                "content": "开始问卷对话，请用友好的方式开场并询问第一个问题"
            })
        else:
            messages.append({
                "role": "user",
                "content": "根据以上对话，生成下一个问题。如果信息已收集完整，标记 is_complete 为 true"
            })
        
        response = await self._call_llm(
            messages,
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        
        try:
            result = json.loads(response)
            return {
                "next_question": result.get("next_question", "请告诉我更多关于您的情况"),
                "is_complete": result.get("is_complete", False),
                "current_field": result.get("current_field", ""),
                "suggested_options": result.get("suggested_options", []),
                "explanation": result.get("explanation", "")
            }
        except json.JSONDecodeError:
            return {
                "next_question": "您家里目前的居住情况是怎样的？",
                "is_complete": False,
                "current_field": "living_space",
                "suggested_options": ["公寓", "带院子的房子", "农村住宅"],
                "explanation": ""
            }
    
    async def extract_profile_from_chat(self, chat_history: List[Dict]) -> UserProfile:
        """从对话历史中提取用户画像"""
        
        system_prompt = """从以下领养对话中提取关键信息，生成结构化的用户画像。
只提取明确提到的信息，不要猜测。

输出 JSON 格式：
{
    "living_space": "apartment/house_with_yard/rural",
    "experience_level": "none/beginner/experienced",
    "daily_time_available": 数字,
    "family_status": "single/couple/with_kids/with_elderly",
    "other_pets": ["狗", "猫"],
    "activity_level": "low/medium/high",
    "preferences": {}
}"""

        chat_text = "\n".join([f"{'用户' if m.get('sender') == 'user' else '顾问'}: {m.get('text', '')}" 
                              for m in chat_history])
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"对话内容：\n{chat_text}\n\n请提取用户画像，返回JSON格式"}
        ]
        
        response = await self._call_llm(
            messages,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        try:
            data = json.loads(response)
            return UserProfile(
                living_space=data.get("living_space", ""),
                experience_level=data.get("experience_level", ""),
                daily_time_available=data.get("daily_time_available", 0),
                family_status=data.get("family_status", ""),
                other_pets=data.get("other_pets", []),
                activity_level=data.get("activity_level", ""),
                preferences=data.get("preferences", {})
            )
        except:
            return UserProfile()
    
    # ==================== 功能2：智能匹配推荐 ====================
    
    async def calculate_match_score(
        self,
        user_profile: UserProfile,
        pet: PetProfile
    ) -> MatchResult:
        """计算用户与宠物的匹配度"""
        
        system_prompt = """你是一位专业的宠物匹配专家。请分析用户画像和宠物档案，计算匹配度。

评分维度（每项0-100分）：
1. 空间匹配度：居住空间是否适合宠物体型和活动需求
2. 经验匹配度：用户经验是否能应对宠物的训练难度
3. 时间匹配度：用户可用时间是否能满足宠物的陪伴和运动需求
4. 家庭匹配度：宠物性格是否适合用户家庭状况
5. 活动量匹配度：用户活动偏好与宠物能量水平是否匹配

输出 JSON 格式：
{
    "score": 85,
    "reasons": ["理由1", "理由2"],
    "concerns": ["顾虑1"],
    "compatibility": {"activity": 0.9, "space": 0.8, "experience": 0.95}
}"""

        user_text = f"""用户画像：
- 居住空间：{user_profile.living_space}
- 养宠经验：{user_profile.experience_level}
- 每日可用时间：{user_profile.daily_time_available}小时
- 家庭状况：{user_profile.family_status}
- 其他宠物：{', '.join(user_profile.other_pets) if user_profile.other_pets else '无'}
- 活动量偏好：{user_profile.activity_level}"""

        pet_text = f"""宠物档案：
- 名字：{pet.name}
- 品种：{pet.breed}
- 年龄：{pet.age_months}个月
- 体型：{pet.size}
- 能量水平：{pet.energy_level}
- 性格：{', '.join(pet.temperament)}
- 特殊需求：{', '.join(pet.special_needs) if pet.special_needs else '无'}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_text}\n\n{pet_text}\n\n请分析匹配度，返回JSON格式"}
        ]
        
        response = await self._call_llm(
            messages,
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        
        try:
            data = json.loads(response)
            return MatchResult(
                pet_id=pet.id,
                score=data.get("score", 50),
                reasons=data.get("reasons", []),
                concerns=data.get("concerns", []),
                compatibility_breakdown=data.get("compatibility", {})
            )
        except:
            return MatchResult(
                pet_id=pet.id,
                score=50,
                reasons=["基础匹配"],
                concerns=["需要更多信息"],
                compatibility_breakdown={}
            )
    
    async def get_top_recommendations(
        self,
        user_profile: UserProfile,
        available_pets: List[PetProfile],
        top_n: int = 3
    ) -> List[MatchResult]:
        """获取 Top-N 推荐"""
        import asyncio
        tasks = [self.calculate_match_score(user_profile, pet) for pet in available_pets]
        results = await asyncio.gather(*tasks)
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
        return sorted_results[:top_n]
    
    # ==================== 功能3：AI 预审助手 ====================
    
    async def precheck_application(
        self,
        application_data: Dict,
        user_profile: UserProfile,
        pet: PetProfile,
        user_history: List[Dict] = None
    ) -> PreCheckResult:
        """AI 自动预审申请"""
        
        system_prompt = """你是一位严格的宠物领养审核专家。请根据申请信息、用户画像和宠物需求进行自动预审。

审核维度：
1. 居住条件是否适合该宠物
2. 经济能力（根据职业推断）
3. 时间投入是否足够
4. 养宠动机是否合理
5. 是否有弃养风险
6. 是否适合该宠物的特殊需求

风险等级：low/medium/high

输出 JSON 格式：
{
    "passed": true,
    "score": 85,
    "risk_level": "low",
    "risk_points": [{"field": "居住条件", "reason": "原因"}],
    "suggestions": ["建议1"],
    "auto_approved": true
}"""

        app_text = f"""申请信息：
{json.dumps(application_data, ensure_ascii=False, indent=2)}"""

        profile_text = f"""用户画像：
- 居住空间：{user_profile.living_space}
- 经验水平：{user_profile.experience_level}
- 每日可用时间：{user_profile.daily_time_available}小时
- 家庭状况：{user_profile.family_status}
- 其他宠物：{', '.join(user_profile.other_pets) if user_profile.other_pets else '无'}"""

        pet_text = f"""宠物需求：
- 名字：{pet.name}
- 品种：{pet.breed}
- 特殊需求：{', '.join(pet.special_needs) if pet.special_needs else '无'}
- 能量水平：{pet.energy_level}"""

        history_text = ""
        if user_history:
            history_text = f"""历史申请记录：
{json.dumps(user_history, ensure_ascii=False, indent=2)}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{app_text}\n\n{profile_text}\n\n{pet_text}\n\n{history_text}\n\n请进行预审，返回JSON格式"}
        ]
        
        response = await self._call_llm(
            messages,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        try:
            data = json.loads(response)
            return PreCheckResult(
                passed=data.get("passed", False),
                score=data.get("score", 0),
                risk_level=data.get("risk_level", "high"),
                risk_points=data.get("risk_points", []),
                suggestions=data.get("suggestions", []),
                auto_approved=data.get("auto_approved", False)
            )
        except:
            return PreCheckResult(
                passed=False,
                score=0,
                risk_level="high",
                risk_points=[{"field": "system", "reason": "审核系统异常"}],
                suggestions=["请人工审核"],
                auto_approved=False
            )
    
    async def generate_review_report(
        self,
        application_id: str,
        precheck_result: PreCheckResult
    ) -> str:
        """生成审核报告"""
        
        system_prompt = """根据 AI 预审结果，生成一份简洁的审核报告供人工复核。"""
        
        result_text = f"""申请ID：{application_id}
AI预审结果：
- 通过状态：{'通过' if precheck_result.passed else '未通过'}
- 评分：{precheck_result.score}/100
- 风险等级：{precheck_result.risk_level}
- 风险点：{json.dumps(precheck_result.risk_points, ensure_ascii=False)}
- 建议：{json.dumps(precheck_result.suggestions, ensure_ascii=False)}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": result_text}
        ]
        
        return await self._call_llm(messages, temperature=0.5)


# 全局 AI 服务实例
ai_service = AIService()
