"""
AI预审助手 - 多轮对话式审核（状态机实现）
替代人工审核中的"基础资质核实"环节（占70%工作量）
"""
import logging
from typing import List, Dict, Optional, Callable
from enum import Enum, auto
from dataclasses import dataclass, field
import json

from app.services.longcat_service import longcat_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 20个高频风险点 ====================

RISK_POINTS = {
    # 经济风险
    "unstable_income": {
        "id": "R001",
        "name": "收入不稳定",
        "description": "学生/自由职业/频繁换工作",
        "severity": "high",
        "check": lambda data: data.get("income_stability") == "unstable" or data.get("occupation") in ["学生", "自由职业"]
    },
    "low_budget": {
        "id": "R002",
        "name": "预算不足",
        "description": "预算<500元/月但想养大型犬",
        "severity": "medium",
        "check": lambda data: data.get("budget_level") == "low" and data.get("preferred_size") in ["large", "xlarge"]
    },
    
    # 住房风险
    "renting_no_permission": {
        "id": "R003",
        "name": "租房无许可",
        "description": "租房且未确认房东同意",
        "severity": "high",
        "check": lambda data: data.get("is_renting") and not data.get("landlord_allows_pets")
    },
    "small_space_large_pet": {
        "id": "R004",
        "name": "空间不足",
        "description": "小公寓想养大型犬",
        "severity": "high",
        "check": lambda data: data.get("living_space") == "small_apartment" and data.get("preferred_size") in ["large", "xlarge"]
    },
    "frequent_moving": {
        "id": "R005",
        "name": "频繁搬家",
        "description": "每年搬家超过1次",
        "severity": "medium",
        "check": lambda data: data.get("move_frequency", 0) > 1
    },
    
    # 时间风险
    "long_work_hours": {
        "id": "R006",
        "name": "工作时间长",
        "description": "每天工作>10小时且无人照顾",
        "severity": "high",
        "check": lambda data: data.get("work_hours_per_day", 0) > 10 and not data.get("has_caretaker")
    },
    "frequent_travel": {
        "id": "R007",
        "name": "经常出差",
        "description": "每月出差>5天且无照顾方案",
        "severity": "high",
        "check": lambda data: data.get("work_schedule") == "frequent_travel" and not data.get("travel_care_plan")
    },
    "low_time_availability": {
        "id": "R008",
        "name": "时间不足",
        "description": "每天<1小时陪伴时间",
        "severity": "medium",
        "check": lambda data: data.get("daily_time_available", 0) < 1
    },
    
    # 经验风险
    "no_exp_high_maintenance": {
        "id": "R009",
        "name": "新手养高维护宠物",
        "description": "无经验但想养困难品种",
        "severity": "medium",
        "check": lambda data: data.get("experience_level") == "none" and data.get("preferred_difficulty") == "high"
    },
    "unrealistic_expectations": {
        "id": "R010",
        "name": "期望不切实际",
        "description": "期望宠物完全不叫/不掉毛/不破坏",
        "severity": "low",
        "check": lambda data: any(word in str(data.get("expectations", "")) for word in ["完全不", "从不", "绝对不"])
    },
    
    # 家庭风险
    "young_kids_high_energy": {
        "id": "R011",
        "name": "幼儿+高能量宠物",
        "description": "有<6岁孩子想养高能量大型犬",
        "severity": "high",
        "check": lambda data: data.get("family_status") == "with_kids_young" and data.get("preferred_energy") == "high"
    },
    "family_disagreement": {
        "id": "R012",
        "name": "家庭意见不一致",
        "description": "未确认所有家庭成员同意",
        "severity": "high",
        "check": lambda data: not data.get("family_agrees", True)
    },
    "elderly_no_assistance": {
        "id": "R013",
        "name": "老人独自养宠",
        "description": "老人独居且无协助",
        "severity": "medium",
        "check": lambda data: data.get("family_status") == "with_elderly" and data.get("household_size", 1) == 1
    },
    
    # 动机风险
    "impulsive_adoption": {
        "id": "R014",
        "name": "冲动领养",
        "description": "决定时间<1周，未充分准备",
        "severity": "medium",
        "check": lambda data: data.get("decision_duration", "1个月") in ["1天内", "1周内"]
    },
    "gift_for_others": {
        "id": "R015",
        "name": "为他人代领",
        "description": "礼物/代朋友领养",
        "severity": "high",
        "check": lambda data: any(word in str(data.get("reason", "")) for word in ["礼物", "送人", "代", "朋友要"])
    },
    "wrong_motivation": {
        "id": "R016",
        "name": "动机不当",
        "description": "为了看门/繁殖/拍照好看",
        "severity": "high",
        "check": lambda data: any(word in str(data.get("reason", "")) for word in ["看门", "繁殖", "生小狗", "拍照", "网红"])
    },
    
    # 准备度风险
    "no_preparation": {
        "id": "R017",
        "name": "未做准备",
        "description": "未准备用品，未了解品种特性",
        "severity": "medium",
        "check": lambda data: not data.get("has_prepared_supplies") and not data.get("has_researched_breed")
    },
    "no_contingency_plan": {
        "id": "R018",
        "name": "无应急预案",
        "description": "未考虑生病/出差/怀孕等情况",
        "severity": "medium",
        "check": lambda data: not data.get("has_contingency_plan")
    },
    
    # 健康风险
    "allergies_not_considered": {
        "id": "R019",
        "name": "未考虑过敏",
        "description": "有过敏史但未确认对宠物过敏",
        "severity": "high",
        "check": lambda data: data.get("has_allergies") and not data.get("allergy_tested")
    },
    "health_issues": {
        "id": "R020",
        "name": "健康问题",
        "description": "领养人健康问题可能影响养宠",
        "severity": "medium",
        "check": lambda data: any(word in str(data.get("health_issues", "")) for word in ["行动不便", "严重疾病", "长期卧床"])
    }
}


# ==================== 状态机定义 ====================

class PrecheckState(Enum):
    """预审状态"""
    INIT = auto()  # 初始状态
    BASIC_INFO = auto()  # 收集基础信息
    HOUSING_CHECK = auto()  # 住房条件核实
    INCOME_CHECK = auto()  # 收入情况核实
    TIME_COMMITMENT = auto()  # 时间投入核实
    EXPERIENCE_CHECK = auto()  # 经验评估
    FAMILY_CHECK = auto()  # 家庭状况核实
    MOTIVATION_CHECK = auto()  # 动机评估
    PREPARATION_CHECK = auto()  # 准备度检查
    RISK_CLARIFICATION = auto()  # 风险点澄清
    SUMMARY = auto()  # 总结
    COMPLETE = auto()  # 完成


@dataclass
class PrecheckSession:
    """预审会话状态"""
    session_id: str
    user_id: str
    pet_id: str
    state: PrecheckState = PrecheckState.INIT
    
    # 已收集的数据
    collected_data: Dict = field(default_factory=dict)
    
    # 已确认的信息
    confirmed_info: Dict = field(default_factory=dict)
    
    # 待核实的问题
    pending_questions: List[str] = field(default_factory=list)
    
    # 发现的风险点
    identified_risks: List[Dict] = field(default_factory=list)
    
    # 已澄清的风险
    clarified_risks: List[str] = field(default_factory=list)
    
    # 对话历史
    chat_history: List[Dict] = field(default_factory=list)
    
    # 轮数计数
    turn_count: int = 0
    
    # 是否完成
    is_complete: bool = False
    
    # 最终结果
    result: Optional[Dict] = None


class PrecheckEngine:
    """预审引擎 - 多轮对话实现"""
    
    def __init__(self):
        self.sessions: Dict[str, PrecheckSession] = {}
        self.llm = longcat_service
    
    def create_session(self, user_id: str, pet_id: str) -> str:
        """创建新的预审会话"""
        import uuid
        session_id = str(uuid.uuid4())
        
        session = PrecheckSession(
            session_id=session_id,
            user_id=user_id,
            pet_id=pet_id
        )
        
        self.sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[PrecheckSession]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    async def process_message(
        self,
        session_id: str,
        user_message: str
    ) -> Dict:
        """
        处理用户消息，返回下一轮对话
        
        Returns:
            {
                "response": "AI回复",
                "state": "当前状态",
                "is_complete": False,
                "identified_risks": [],
                "next_question": "下一个问题"
            }
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "会话不存在"}
        
        # 记录用户消息
        session.chat_history.append({"role": "user", "text": user_message})
        session.turn_count += 1
        
        # 状态机处理
        if session.state == PrecheckState.INIT:
            await self._handle_init(session)
        elif session.state == PrecheckState.BASIC_INFO:
            await self._handle_basic_info(session, user_message)
        elif session.state == PrecheckState.HOUSING_CHECK:
            await self._handle_housing_check(session, user_message)
        elif session.state == PrecheckState.INCOME_CHECK:
            await self._handle_income_check(session, user_message)
        elif session.state == PrecheckState.TIME_COMMITMENT:
            await self._handle_time_commitment(session, user_message)
        elif session.state == PrecheckState.EXPERIENCE_CHECK:
            await self._handle_experience_check(session, user_message)
        elif session.state == PrecheckState.FAMILY_CHECK:
            await self._handle_family_check(session, user_message)
        elif session.state == PrecheckState.MOTIVATION_CHECK:
            await self._handle_motivation_check(session, user_message)
        elif session.state == PrecheckState.PREPARATION_CHECK:
            await self._handle_preparation_check(session, user_message)
        elif session.state == PrecheckState.RISK_CLARIFICATION:
            await self._handle_risk_clarification(session, user_message)
        elif session.state == PrecheckState.SUMMARY:
            await self._handle_summary(session)
        
        # 检查风险点
        self._check_risks(session)
        
        # 构建响应
        return {
            "response": session.chat_history[-1]["text"] if session.chat_history else "",
            "state": session.state.name,
            "is_complete": session.is_complete,
            "identified_risks": session.identified_risks,
            "collected_data": session.collected_data,
            "turn_count": session.turn_count
        }
    
    async def _handle_init(self, session: PrecheckSession):
        """初始化 - 开场白"""
        greeting = """您好！我是 PawPal 的 AI 预审助手 🤖

在正式提交申请前，我想和您聊几分钟，了解一些基本情况。这有助于提高申请通过率，也能帮您确认是否真的准备好了迎接新家庭成员。

让我们开始吧！首先，请问您目前的职业和工作状态是怎样的？"""
        
        session.chat_history.append({"role": "assistant", "text": greeting})
        session.state = PrecheckState.BASIC_INFO
    
    async def _handle_basic_info(self, session: PrecheckSession, message: str):
        """处理基础信息"""
        # 提取职业、工作状态
        session.collected_data["occupation"] = message
        
        # 使用 LLM 分析收入稳定性
        prompt = f"根据描述'{message}'，判断收入稳定性：stable/unstable/student。只返回一个词。"
        stability = await self.llm.chat_completion([{"role": "user", "content": prompt}], temperature=0.3)
        session.collected_data["income_stability"] = stability.strip().lower()
        
        # 进入住房检查
        response = "了解了。接下来问问您的居住情况：您目前是租房还是自有住房？大概多大面积？"
        session.chat_history.append({"role": "assistant", "text": response})
        session.state = PrecheckState.HOUSING_CHECK
    
    async def _handle_housing_check(self, session: PrecheckSession, message: str):
        """处理住房检查"""
        session.collected_data["housing_raw"] = message
        
        # 分析住房情况
        if "租" in message:
            session.collected_data["is_renting"] = True
            response = "明白，您是租房。非常重要的一点：您的房东允许养宠物吗？有书面确认吗？"
        else:
            session.collected_data["is_renting"] = False
            response = "好的。您的房子大概多大面积？有院子或阳台吗？"
        
        session.chat_history.append({"role": "assistant", "text": response})
        
        # 如果已收集足够信息，进入下一步
        if session.collected_data.get("is_renting") and ("允许" in message or "同意" in message):
            session.collected_data["landlord_allows_pets"] = True
            session.state = PrecheckState.INCOME_CHECK
            response += "\n\n好的。关于经济方面，您每月大概能为宠物预算多少费用（包括食物、医疗、用品等）？"
        elif not session.collected_data.get("is_renting"):
            session.state = PrecheckState.INCOME_CHECK
            response += "\n\n关于经济方面，您每月大概能为宠物预算多少费用？"
        
        session.chat_history[-1]["text"] = response
    
    async def _handle_income_check(self, session: PrecheckSession, message: str):
        """处理收入检查"""
        # 解析预算
        import re
        numbers = re.findall(r'\d+', message)
        if numbers:
            budget = int(numbers[0])
            session.collected_data["monthly_budget"] = budget
            session.collected_data["budget_level"] = "high" if budget > 1500 else "medium" if budget > 500 else "low"
        
        response = "了解了。时间投入方面：您每天大概能抽出多少小时陪伴和照顾宠物？工作经常出差吗？"
        session.chat_history.append({"role": "assistant", "text": response})
        session.state = PrecheckState.TIME_COMMITMENT
    
    async def _handle_time_commitment(self, session: PrecheckSession, message: str):
        """处理时间投入"""
        import re
        numbers = re.findall(r'\d+', message)
        if numbers:
            session.collected_data["daily_time_available"] = int(numbers[0])
        
        if "出差" in message:
            session.collected_data["work_schedule"] = "frequent_travel"
            response = "明白。出差时您有可靠的照顾方案吗（比如家人、朋友或宠物寄养）？"
        else:
            session.collected_data["work_schedule"] = "regular"
            response = "好的。关于养宠经验：您之前养过宠物吗？如果有，是什么情况？"
            session.state = PrecheckState.EXPERIENCE_CHECK
        
        session.chat_history.append({"role": "assistant", "text": response})
    
    async def _handle_experience_check(self, session: PrecheckSession, message: str):
        """处理经验检查"""
        if any(word in message for word in ["没", "无", "第一次"]):
            session.collected_data["experience_level"] = "none"
        elif any(word in message for word in ["一只", "一点", "小时候"]):
            session.collected_data["experience_level"] = "beginner"
        else:
            session.collected_data["experience_level"] = "experienced"
        
        response = "了解了。家庭情况：您目前是独居、和伴侣/家人同住？家里有小孩或老人吗？"
        session.chat_history.append({"role": "assistant", "text": response})
        session.state = PrecheckState.FAMILY_CHECK
    
    async def _handle_family_check(self, session: PrecheckSession, message: str):
        """处理家庭检查"""
        if "孩" in message and ("小" in message or "岁" in message):
            session.collected_data["family_status"] = "with_kids_young"
        elif "老人" in message or "父母" in message:
            session.collected_data["family_status"] = "with_elderly"
        elif "伴侣" in message or "夫妻" in message or "男" in message or "女" in message:
            session.collected_data["family_status"] = "couple"
        else:
            session.collected_data["family_status"] = "single"
        
        response = "好的。非常重要的问题：您为什么想领养这只宠物？是什么吸引了您？"
        session.chat_history.append({"role": "assistant", "text": response})
        session.state = PrecheckState.MOTIVATION_CHECK
    
    async def _handle_motivation_check(self, session: PrecheckSession, message: str):
        """处理动机检查"""
        session.collected_data["adoption_reason"] = message
        
        response = "明白了。最后几个问题：您为领养做了哪些准备？比如了解品种特性、准备用品、考虑应急方案等。"
        session.chat_history.append({"role": "assistant", "text": response})
        session.state = PrecheckState.PREPARATION_CHECK
    
    async def _handle_preparation_check(self, session: PrecheckSession, message: str):
        """处理准备度检查"""
        session.collected_data["preparation"] = message
        
        # 检查是否有风险点需要澄清
        self._check_risks(session)
        
        if session.identified_risks:
            # 有需要澄清的风险点
            risk = session.identified_risks[0]
            response = f"我注意到一个可能需要进一步确认的点：{risk['description']}\n\n能详细说说情况吗？"
            session.state = PrecheckState.RISK_CLARIFICATION
        else:
            # 无风险，直接总结
            await self._handle_summary(session)
            return
        
        session.chat_history.append({"role": "assistant", "text": response})
    
    async def _handle_risk_clarification(self, session: PrecheckSession, message: str):
        """处理风险澄清"""
        # 记录澄清
        if session.identified_risks:
            clarified_risk = session.identified_risks.pop(0)
            session.clarified_risks.append({
                "risk_id": clarified_risk["id"],
                "clarification": message
            })
            
            # 评估澄清是否充分
            prompt = f"风险：{clarified_risk['description']}\n用户解释：{message}\n\n评估是否充分化解了风险？返回：resolved/partial/unresolved"
            assessment = await self.llm.chat_completion([{"role": "user", "content": prompt}], temperature=0.3)
            
            if "resolved" in assessment.lower():
                session.collected_data[f"risk_{clarified_risk['id']}_resolved"] = True
        
        # 检查是否还有风险
        if session.identified_risks:
            # 继续澄清下一个
            risk = session.identified_risks[0]
            response = f"还有一个问题想确认：{risk['description']}"
            session.chat_history.append({"role": "assistant", "text": response})
        else:
            # 所有风险已澄清，进入总结
            await self._handle_summary(session)
    
    async def _handle_summary(self, session: PrecheckSession):
        """生成总结"""
        # 计算最终评分
        risk_score = self._calculate_risk_score(session)
        
        if risk_score >= 80:
            conclusion = "根据我们的对话，您的条件很适合领养这只宠物！"
            recommendation = "approve"
        elif risk_score >= 60:
            conclusion = "整体条件不错，但有一些小地方可以改进。"
            recommendation = "review"
        else:
            conclusion = "目前条件可能还不太适合领养这只宠物，建议再做一些准备。"
            recommendation = "reject"
        
        summary = f"""{conclusion}

审核摘要：
- 居住条件：{'✓' if not self._has_housing_risk(session) else '⚠'}
- 经济能力：{'✓' if not self._has_income_risk(session) else '⚠'}
- 时间投入：{'✓' if not self._has_time_risk(session) else '⚠'}
- 经验匹配：{'✓' if not self._has_experience_risk(session) else '⚠'}

建议：{'申请通过，等待最终审核' if recommendation == 'approve' else '人工复核' if recommendation == 'review' else '建议改善后再申请'}

感谢您的耐心回答！{'您可以继续提交正式申请了。' if recommendation == 'approve' else '我们会尽快联系您。'}"""
        
        session.chat_history.append({"role": "assistant", "text": summary})
        session.is_complete = True
        session.state = PrecheckState.COMPLETE
        
        # 保存结果
        session.result = {
            "score": risk_score,
            "recommendation": recommendation,
            "risks": session.clarified_risks,
            "data": session.collected_data
        }
    
    def _check_risks(self, session: PrecheckSession):
        """检查风险点"""
        for risk_id, risk_config in RISK_POINTS.items():
            # 检查是否已识别或已澄清
            if any(r["id"] == risk_id for r in session.identified_risks):
                continue
            if any(r["risk_id"] == risk_id for r in session.clarified_risks):
                continue
            
            # 检查是否触发
            try:
                if risk_config["check"](session.collected_data):
                    session.identified_risks.append({
                        "id": risk_id,
                        "name": risk_config["name"],
                        "description": risk_config["description"],
                        "severity": risk_config["severity"]
                    })
            except:
                pass
    
    def _calculate_risk_score(self, session: PrecheckSession) -> float:
        """计算风险评分（0-100，越高越好）"""
        base_score = 100
        
        for risk in session.identified_risks:
            if risk["severity"] == "high":
                base_score -= 20
            elif risk["severity"] == "medium":
                base_score -= 10
            else:
                base_score -= 5
        
        # 根据澄清情况加分
        resolved_count = len(session.clarified_risks)
        base_score += resolved_count * 5
        
        return max(0, min(100, base_score))
    
    def _has_housing_risk(self, session: PrecheckSession) -> bool:
        """是否有住房风险"""
        return any(r["id"] in ["R003", "R004", "R005"] for r in session.identified_risks)
    
    def _has_income_risk(self, session: PrecheckSession) -> bool:
        """是否有收入风险"""
        return any(r["id"] in ["R001", "R002"] for r in session.identified_risks)
    
    def _has_time_risk(self, session: PrecheckSession) -> bool:
        """是否有时间风险"""
        return any(r["id"] in ["R006", "R007", "R008"] for r in session.identified_risks)
    
    def _has_experience_risk(self, session: PrecheckSession) -> bool:
        """是否有经验风险"""
        return any(r["id"] in ["R009", "R010"] for r in session.identified_risks)


# 全局预审引擎实例
precheck_engine = PrecheckEngine()
