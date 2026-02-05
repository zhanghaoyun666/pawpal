"""
智能匹配引擎
混合架构：0.4硬性规则 + 0.4 Embedding相似度 + 0.2历史成功率
"""
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json

from app.services.embedding_service import (
    embedding_service, 
    adopter_profile_to_text, 
    pet_profile_to_text
)
from app.models.profile_schema import MatchResult, MatchDimension

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 硬性规则配置 ====================

HARD_CONSTRAINTS = {
    # 居住空间 vs 宠物体型
    "space_size": {
        "small_apartment": ["tiny", "small"],  # 小公寓只能养小型
        "medium_apartment": ["tiny", "small", "medium"],
        "large_apartment": ["tiny", "small", "medium", "large"],
        "house_with_yard": ["tiny", "small", "medium", "large", "xlarge"],
        "rural": ["tiny", "small", "medium", "large", "xlarge"]
    },
    
    # 经验 vs 训练难度
    "experience_trainability": {
        "none": ["easy"],  # 新手只能养容易训练的
        "beginner": ["easy", "moderate"],
        "intermediate": ["easy", "moderate", "difficult"],
        "experienced": ["easy", "moderate", "difficult"]
    },
    
    # 时间 vs 运动需求
    "time_exercise": {
        # 每日可用时间 vs 宠物运动需求
        "low": {"min_hours": 0, "max_hours": 1},
        "medium": {"min_hours": 1, "max_hours": 3},
        "high": {"min_hours": 2, "max_hours": 24}
    },
    
    # 家庭状况 vs 宠物适应性
    "family_compatibility": {
        "with_kids_young": {"requires": ["good_with_kids"]},
        "with_elderly": {"requires": ["calm", "low_energy"]},
    },
    
    # 容忍度硬性筛选
    "tolerance": {
        "shedding": {
            "none": ["none"],  # 不接受掉毛 → 只能养不掉毛的
            "low": ["none", "low"],
            "medium": ["none", "low", "medium"],
            "high": ["none", "low", "medium", "high"]
        },
        "noise": {
            "low": ["low"],  # 需要安静 → 只能养安静的
            "medium": ["low", "medium"],
            "high": ["low", "medium", "high"]
        }
    }
}


@dataclass
class HardConstraintCheck:
    """硬性规则检查结果"""
    passed: bool
    score: float  # 0-100
    failed_rules: List[str]
    passed_rules: List[str]


class MatchingEngine:
    """匹配引擎"""
    
    def __init__(self):
        self.embedding = embedding_service
        self.weights = {
            "hard_constraints": 0.4,
            "soft_preferences": 0.4,
            "historical": 0.2
        }
    
    # ==================== 硬性规则检查（0.4权重）====================
    
    def check_hard_constraints(
        self,
        adopter: Dict,
        pet: Dict
    ) -> HardConstraintCheck:
        """
        检查硬性条件是否满足
        
        Returns:
            HardConstraintCheck 包含是否通过、得分、失败规则
        """
        passed_rules = []
        failed_rules = []
        
        # 1. 居住空间 vs 宠物体型
        living = adopter.get("living_space", "medium_apartment")
        pet_size = pet.get("size_category", "medium")
        allowed_sizes = HARD_CONSTRAINTS["space_size"].get(living, ["small"])
        
        if pet_size in allowed_sizes:
            passed_rules.append(f"空间匹配：{living} 适合 {pet_size}")
        else:
            failed_rules.append(f"空间不匹配：{living} 不适合 {pet_size}")
        
        # 2. 经验 vs 训练难度
        experience = adopter.get("experience_level", "none")
        trainability = pet.get("trainability", "moderate")
        allowed_difficulty = HARD_CONSTRAINTS["experience_trainability"].get(
            experience, ["easy"]
        )
        
        if trainability in allowed_difficulty:
            passed_rules.append(f"经验匹配：{experience} 可以应对 {trainability}")
        else:
            failed_rules.append(f"经验不足：{experience} 难以应对 {trainability}")
        
        # 3. 时间 vs 运动需求
        daily_time = adopter.get("daily_time_available", 2)
        exercise_need = pet.get("exercise_needs", "medium")
        time_req = HARD_CONSTRAINTS["time_exercise"][exercise_need]
        
        if time_req["min_hours"] <= daily_time <= time_req["max_hours"]:
            passed_rules.append(f"时间匹配：每天{daily_time}小时满足运动需求")
        else:
            if daily_time < time_req["min_hours"]:
                failed_rules.append(f"时间不足：需要每天至少{time_req['min_hours']}小时")
            else:
                passed_rules.append(f"时间充裕：每天{daily_time}小时")
        
        # 4. 家庭状况 vs 宠物适应性
        family = adopter.get("family_status", "single")
        if family == "with_kids_young":
            if pet.get("good_with_kids", True):
                passed_rules.append("适合有年幼孩子的家庭")
            else:
                failed_rules.append("不适合有年幼孩子的家庭")
        
        # 5. 掉毛容忍度
        shedding_tol = adopter.get("shedding_tolerance", "medium")
        shedding_level = pet.get("shedding_level", "medium")
        allowed_shedding = HARD_CONSTRAINTS["tolerance"]["shedding"].get(
            shedding_tol, ["low", "medium"]
        )
        
        if shedding_level in allowed_shedding:
            passed_rules.append(f"掉毛接受度匹配")
        else:
            failed_rules.append(f"掉毛水平超出接受范围")
        
        # 6. 噪音容忍度
        noise_tol = adopter.get("noise_tolerance", "medium")
        energy = pet.get("energy_level", "medium")
        # 高能量宠物通常更吵
        if noise_tol == "low" and energy == "high":
            failed_rules.append("高能量宠物可能太吵")
        else:
            passed_rules.append("噪音水平可接受")
        
        # 7. 租房检查
        if adopter.get("is_renting"):
            if adopter.get("landlord_allows_pets") is False:
                failed_rules.append("房东不允许养宠物")
            else:
                passed_rules.append("租房养宠条件满足")
        
        # 计算得分
        total_rules = len(passed_rules) + len(failed_rules)
        if total_rules == 0:
            score = 100
        else:
            score = (len(passed_rules) / total_rules) * 100
        
        # 硬性规则：只要有失败就不通过
        passed = len(failed_rules) == 0
        
        return HardConstraintCheck(
            passed=passed,
            score=score,
            failed_rules=failed_rules,
            passed_rules=passed_rules
        )
    
    # ==================== 软性偏好匹配（0.4权重）====================
    
    async def calculate_soft_preference_match(
        self,
        adopter: Dict,
        pet: Dict
    ) -> Tuple[float, List[MatchDimension]]:
        """
        计算软性偏好匹配度（使用 Embedding 相似度）
        
        Returns:
            (得分, 维度详情)
        """
        dimensions = []
        
        # 1. 整体画像 Embedding 相似度（主要）
        adopter_text = adopter_profile_to_text(adopter)
        pet_text = pet_profile_to_text(pet)
        
        adopter_emb = await self.embedding.get_embedding(adopter_text)
        pet_emb = await self.embedding.get_embedding(pet_text)
        
        overall_similarity = self.embedding.cosine_similarity(adopter_emb, pet_emb)
        # 将 -1~1 映射到 0~100
        overall_score = (overall_similarity + 1) / 2 * 100
        
        dimensions.append(MatchDimension(
            name="整体画像匹配",
            score=overall_score,
            weight=0.5,
            reason=f"基于{len(adopter_text)}字画像文本的语义相似度"
        ))
        
        # 2. 性格匹配
        temperament_score = self._match_temperament(
            adopter.get("preferred_temperament", []),
            pet.get("temperament", [])
        )
        dimensions.append(MatchDimension(
            name="性格匹配",
            score=temperament_score,
            weight=0.3,
            reason="偏好的性格特点与宠物实际性格的匹配度"
        ))
        
        # 3. 活动量匹配
        activity_score = self._match_activity(
            adopter.get("activity_level", "medium"),
            pet.get("energy_level", "medium")
        )
        dimensions.append(MatchDimension(
            name="活动量匹配",
            score=activity_score,
            weight=0.2,
            reason="用户活动偏好与宠物能量水平的匹配度"
        ))
        
        # 计算加权得分
        total_weight = sum(d.weight for d in dimensions)
        weighted_score = sum(d.score * d.weight for d in dimensions) / total_weight
        
        return weighted_score, dimensions
    
    def _match_temperament(
        self,
        preferred: List[str],
        actual: List[str]
    ) -> float:
        """匹配性格标签"""
        if not preferred:
            return 80  # 无偏好默认中等匹配
        
        if not actual:
            return 50
        
        # 计算匹配的标签数
        matched = set(preferred) & set(actual)
        total = set(preferred) | set(actual)
        
        if not total:
            return 80
        
        return (len(matched) / len(total)) * 100
    
    def _match_activity(
        self,
        adopter_level: str,
        pet_level: str
    ) -> float:
        """匹配活动量"""
        levels = ["low", "medium", "high"]
        
        try:
            adopter_idx = levels.index(adopter_level)
            pet_idx = levels.index(pet_level)
        except ValueError:
            return 70
        
        # 差距越小越匹配
        diff = abs(adopter_idx - pet_idx)
        
        if diff == 0:
            return 100
        elif diff == 1:
            return 70
        else:
            return 40
    
    # ==================== 历史成功率（0.2权重）====================
    
    def calculate_historical_score(
        self,
        pet: Dict,
        adopter: Dict
    ) -> Tuple[float, str]:
        """
        计算历史成功率得分
        
        MVP阶段数据不足，使用以下策略：
        1. 如果有该宠物的历史数据，使用实际成功率
        2. 否则使用品种平均成功率
        3. 否则使用默认中等分数（50）
        """
        # 获取宠物历史成功率
        pet_success_rate = pet.get("success_rate")
        
        if pet_success_rate is not None:
            score = pet_success_rate * 100
            reason = f"该宠物历史成功率：{pet_success_rate:.1%}"
        else:
            # 冷启动：使用默认值，权重降低
            score = 50
            reason = "冷启动：暂无历史数据，使用默认值"
        
        return score, reason
    
    # ==================== 综合匹配 ====================
    
    async def calculate_match(
        self,
        adopter: Dict,
        pet: Dict
    ) -> MatchResult:
        """
        计算综合匹配得分
        
        公式：0.4 × 硬性条件 + 0.4 × 软性偏好 + 0.2 × 历史成功率
        """
        # 1. 硬性规则检查
        hard_check = self.check_hard_constraints(adopter, pet)
        
        # 2. 软性偏好匹配
        soft_score, dimensions = await self.calculate_soft_preference_match(adopter, pet)
        
        # 3. 历史成功率
        hist_score, hist_reason = self.calculate_historical_score(pet, adopter)
        
        # 计算加权总分
        if hard_check.passed:
            overall_score = (
                hard_check.score * self.weights["hard_constraints"] +
                soft_score * self.weights["soft_preferences"] +
                hist_score * self.weights["historical"]
            )
        else:
            # 硬性规则未通过，总分大幅降低
            overall_score = hard_check.score * 0.3  # 最高30分
        
        # 生成匹配理由
        match_reasons = hard_check.passed_rules[:3]  # 前3个通过的规则
        
        # 添加软性匹配理由
        if soft_score >= 80:
            match_reasons.append("性格和活动量高度匹配")
        elif soft_score >= 60:
            match_reasons.append("整体偏好较为匹配")
        
        # 添加历史理由
        if hist_score >= 70:
            match_reasons.append(hist_reason)
        
        # 顾虑
        concerns = hard_check.failed_rules
        if soft_score < 60:
            concerns.append("整体偏好匹配度较低，建议深入了解")
        
        # 建议
        recommendations = []
        if not hard_check.passed:
            recommendations.append("建议改善硬性条件后再申请")
        if soft_score < 70:
            recommendations.append("建议多与宠物互动，确认是否合适")
        if pet.get("special_needs"):
            recommendations.append(f"注意特殊需求：{', '.join(pet['special_needs'])}")
        
        return MatchResult(
            pet_id=pet["id"],
            pet_name=pet["name"],
            overall_score=round(overall_score, 1),
            hard_constraint_score=round(hard_check.score, 1),
            soft_preference_score=round(soft_score, 1),
            historical_score=round(hist_score, 1),
            dimensions=dimensions,
            match_reasons=match_reasons,
            concerns=concerns,
            recommendations=recommendations,
            passed_hard_constraints=hard_check.passed,
            failed_constraints=hard_check.failed_rules
        )
    
    async def find_best_matches(
        self,
        adopter: Dict,
        available_pets: List[Dict],
        top_k: int = 3
    ) -> List[MatchResult]:
        """
        找出最佳匹配
        
        策略：
        1. 先用硬性规则过滤（可选：保留未通过的但标记）
        2. 对通过的计算完整得分
        3. 按总分排序返回 Top K
        """
        import asyncio
        
        # 并行计算所有匹配
        tasks = [self.calculate_match(adopter, pet) for pet in available_pets]
        results = await asyncio.gather(*tasks)
        
        # 排序：硬性通过的优先，然后按总分
        results.sort(key=lambda x: (not x.passed_hard_constraints, -x.overall_score))
        
        return results[:top_k]


# 全局匹配引擎实例
matching_engine = MatchingEngine()
