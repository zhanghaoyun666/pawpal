# PawPal AI 技术规格文档

> **版本**: v1.5  
> **更新日期**: 2026-02-06  
> **技术栈**: FastAPI + LongCat LLM + BGE Embedding  
> **状态**: 已开发完成 | 测试验证阶段  

---

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (React)                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ AIQuestionnaire │  │AIRecommendations│  │   AIPrecheck    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/JSON
┌─────────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                         │
│              Base URL: /api/ai/v2/*                              │
│                                                                  │
│  POST /questionnaire/next        - 获取下一个问题                │
│  POST /questionnaire/extract-profile - 提取用户画像              │
│  POST /match/recommendations     - 获取匹配推荐                  │
│  POST /precheck/start            - 开始预审会话                  │
│  POST /precheck/message          - 发送预审消息                  │
│  GET  /precheck/session/{id}     - 获取会话状态                  │
│  GET  /health                    - 健康检查                      │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Questionnaire  │ │ MatchingEngine  │ │ PrecheckEngine  │
│     Service     │ │                 │ │                 │
│                 │ │                 │ │                 │
│ • llm_generate_ │ │ • check_hard_   │ │ • create_session│
│   question()    │ │   constraints() │ │ • process_msg() │
│ • llm_extract_  │ │ • calculate_soft│ │ • state_machine │
│   profile()     │ │   _preference() │ │ • risk_check()  │
│ • mock_fallback │ │ • calculate_    │ │ • score_calc()  │
│                 │ │   historical()  │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI Model Layer                              │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │  LongCat Service        │  │  Embedding Service          │  │
│  │  (美团大模型)            │  │  (BGE-Large-Zh)             │  │
│  │                         │  │                             │  │
│  │  Model: LongCat-Flash   │  │  Model: BAAI/bge-large-zh   │  │
│  │  -Thinking              │  │       -v1.5                 │  │
│  │  Mode: API              │  │  Mode: Local                │  │
│  │  Fallback: Mock         │  │  Fallback: Random Vector    │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 服务模块说明

| 模块 | 文件路径 | 职责 |
|------|----------|------|
| AI Router V2 | `backend/app/routers/ai_v2.py` | API路由定义、请求/响应模型 |
| AI Service | `backend/app/services/ai_service.py` | LLM调用封装、业务逻辑 |
| Matching Engine | `backend/app/services/matching_engine.py` | 匹配算法实现 |
| Precheck Engine | `backend/app/services/precheck_engine.py` | 预审状态机实现 |
| LongCat Service | `backend/app/services/longcat_service.py` | 美团大模型API封装 |
| Embedding Service | `backend/app/services/embedding_service.py` | 向量化服务 |

---

## 2. 数据模型

### 2.1 用户画像模型 (AdopterProfile)

```python
class AdopterProfile(BaseModel):
    # 居住环境 (3维)
    living_space: str           # apartment/house_with_yard/rural
    has_yard: bool              # 是否有院子
    is_renting: bool            # 是否租房
    landlord_allows_pets: Optional[bool]
    
    # 经济能力 (2维)
    budget_level: str           # low/medium/high
    income_stability: str       # stable/unstable/student
    
    # 时间投入 (3维)
    daily_time_available: float # 每日可用小时数
    work_schedule: str          # regular/flexible/frequent_travel
    work_hours_per_day: int     # 每日工作时长
    
    # 养宠经验 (3维)
    experience_level: str       # none/beginner/intermediate/experienced
    previous_pets: List[str]    # 过往养宠经历
    training_willingness: str   # low/medium/high
    
    # 家庭状况 (2维)
    family_status: str          # single/couple/with_kids/with_elderly
    household_size: int         # 家庭人数
    
    # 偏好设置 (3维)
    preferred_size: str         # small/medium/large/no_preference
    preferred_age: str          # puppy/adult/senior/no_preference
    preferred_temperament: List[str]  # 期望性格标签
    
    # 容忍度 (3维)
    activity_level: str         # low/medium/high
    noise_tolerance: str        # low/medium/high
    shedding_tolerance: str     # low/medium/high
    grooming_willingness: str   # low/medium/high
    
    # 特殊需求 (1维)
    has_allergies: bool
    allergy_details: Optional[str]
    must_have_traits: List[str]
    deal_breakers: List[str]
```

### 2.2 宠物档案模型 (PetProfile)

```python
class PetProfile(BaseModel):
    id: str
    name: str
    species: str              # dog/cat/rabbit/other
    breed: str
    age_months: int
    size_category: str        # tiny/small/medium/large/xlarge
    weight_kg: float
    gender: str
    
    # 性格特征
    temperament: List[str]    # 性格标签
    energy_level: str         # low/medium/high
    sociability: str          # shy/moderate/outgoing
    trainability: str         # easy/moderate/difficult
    
    # 护理需求
    shedding_level: str       # none/low/medium/high
    grooming_needs: str       # low/medium/high
    exercise_needs: str       # low/medium/high
    
    # 社交适应性
    good_with_kids: bool
    good_with_dogs: bool
    good_with_cats: bool
    good_with_strangers: bool
    
    # 特殊需求
    special_needs: List[str]
    medical_notes: Optional[str]
    behavioral_notes: Optional[str]
    
    # 空间需求
    min_space_requirement: str
    needs_yard: bool
    
    # 历史数据
    success_rate: Optional[float]  # 历史领养成功率
```

### 2.3 匹配结果模型 (MatchResult)

```python
class MatchDimension(BaseModel):
    name: str           # 维度名称
    score: float        # 0-100
    weight: float       # 权重
    reason: str         # 说明

class MatchResult(BaseModel):
    pet_id: str
    pet_name: str
    overall_score: float           # 总分 0-100
    hard_constraint_score: float   # 硬性条件分
    soft_preference_score: float   # 软性偏好分
    historical_score: float        # 历史成功率分
    dimensions: List[MatchDimension]
    match_reasons: List[str]       # 匹配理由
    concerns: List[str]            # 顾虑点
    recommendations: List[str]     # 建议
    passed_hard_constraints: bool  # 是否通过硬性条件
    failed_constraints: List[str]  # 未通过的约束
```

---

## 3. 核心算法

### 3.1 匹配算法

#### 3.1.1 算法公式

```
总体得分 = 0.4 × HardConstraintScore + 0.4 × SoftPreferenceScore + 0.2 × HistoricalScore

其中:
- HardConstraintScore = (通过规则数 / 总规则数) × 100
- SoftPreferenceScore = Σ(维度得分 × 维度权重) / Σ权重
- HistoricalScore = 宠物历史成功率 × 100 (默认50)
```

#### 3.1.2 硬性规则配置

```python
HARD_CONSTRAINTS = {
    # 居住空间 vs 宠物体型
    "space_size": {
        "small_apartment": ["tiny", "small"],
        "medium_apartment": ["tiny", "small", "medium"],
        "large_apartment": ["tiny", "small", "medium", "large"],
        "house_with_yard": ["tiny", "small", "medium", "large", "xlarge"],
    },
    
    # 经验 vs 训练难度
    "experience_trainability": {
        "none": ["easy"],
        "beginner": ["easy", "moderate"],
        "intermediate": ["easy", "moderate", "difficult"],
        "experienced": ["easy", "moderate", "difficult"]
    },
    
    # 时间 vs 运动需求 (小时)
    "time_exercise": {
        "low": {"min_hours": 0, "max_hours": 1},
        "medium": {"min_hours": 1, "max_hours": 3},
        "high": {"min_hours": 2, "max_hours": 24}
    }
}
```

#### 3.1.3 Embedding相似度计算

```python
async def calculate_embedding_similarity(adopter: Dict, pet: Dict) -> float:
    # 1. 文本化画像
    adopter_text = adopter_profile_to_text(adopter)
    pet_text = pet_profile_to_text(pet)
    
    # 2. 获取Embedding向量
    adopter_emb = await embedding_service.get_embedding(adopter_text)
    pet_emb = await embedding_service.get_embedding(pet_text)
    
    # 3. 计算余弦相似度
    similarity = cosine_similarity(adopter_emb, pet_emb)
    
    # 4. 映射到0-100分
    score = (similarity + 1) / 2 * 100
    return score
```

### 3.2 预审状态机

```python
class PrecheckState(Enum):
    INIT = auto()              # 初始状态
    BASIC_INFO = auto()        # 收集基础信息
    HOUSING_CHECK = auto()     # 住房条件核实
    INCOME_CHECK = auto()      # 收入情况核实
    TIME_COMMITMENT = auto()   # 时间投入核实
    EXPERIENCE_CHECK = auto()  # 经验评估
    FAMILY_CHECK = auto()      # 家庭状况核实
    MOTIVATION_CHECK = auto()  # 动机评估
    PREPARATION_CHECK = auto() # 准备度检查
    RISK_CLARIFICATION = auto()# 风险点澄清
    SUMMARY = auto()           # 总结
    COMPLETE = auto()          # 完成
```

#### 状态转换逻辑

```
INIT → BASIC_INFO: 发送开场白
BASIC_INFO → HOUSING_CHECK: 提取职业信息
HOUSING_CHECK → INCOME_CHECK: 确认住房情况
INCOME_CHECK → TIME_COMMITMENT: 解析预算
TIME_COMMITMENT → EXPERIENCE_CHECK: 确认时间安排
EXPERIENCE_CHECK → FAMILY_CHECK: 评估经验
FAMILY_CHECK → MOTIVATION_CHECK: 确认家庭状况
MOTIVATION_CHECK → PREPARATION_CHECK: 了解动机
PREPARATION_CHECK → [RISK_CLARIFICATION | SUMMARY]: 检查风险
RISK_CLARIFICATION → [RISK_CLARIFICATION | SUMMARY]: 澄清风险
SUMMARY → COMPLETE: 生成总结
```

---

## 4. API 接口规范

### 4.1 智能问卷

#### POST /api/ai/v2/questionnaire/next

**Request:**
```json
{
  "user_id": "uuid",
  "chat_history": [
    {"role": "assistant", "text": "..."},
    {"role": "user", "text": "..."}
  ],
  "current_profile": {},
  "is_first": false
}
```

**Response:**
```json
{
  "next_question": "您家里目前的居住情况是怎样的？",
  "is_complete": false,
  "current_field": "living_space",
  "suggested_options": ["公寓", "带院子的房子", "农村住宅"],
  "explanation": "居住空间决定了适合什么体型的宠物"
}
```

#### POST /api/ai/v2/questionnaire/extract-profile

**Request:**
```json
[
  {"role": "assistant", "text": "..."},
  {"role": "user", "text": "..."}
]
```

**Response:**
```json
{
  "living_space": "apartment",
  "has_yard": false,
  "experience_level": "beginner",
  "daily_time_available": 2,
  "family_status": "single",
  "other_pets": [],
  "activity_level": "medium",
  ...
}
```

### 4.2 智能匹配

#### POST /api/ai/v2/match/recommendations

**Request:**
```json
{
  "user_id": "uuid",
  "adopter_profile": {...},
  "limit": 3
}
```

**Response:**
```json
[
  {
    "pet_id": "uuid",
    "pet_name": "Max",
    "pet_image": "url",
    "score": 87.5,
    "overall_score": 87.5,
    "hard_constraint_score": 100,
    "soft_preference_score": 82.3,
    "historical_score": 75.0,
    "dimensions": [...],
    "compatibility": {"activity": 0.9, "space": 0.8},
    "reasons": ["空间匹配", "时间充足"],
    "match_reasons": ["空间匹配", "时间充足"],
    "concerns": ["新手养大型犬需要更多学习"],
    "recommendations": ["建议参加新手培训课程"],
    "passed_hard_constraints": true,
    "failed_constraints": []
  }
]
```

### 4.3 AI预审

#### POST /api/ai/v2/precheck/start

**Request:**
```json
{
  "user_id": "uuid",
  "pet_id": "uuid"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "response": "您好！我是 PawPal 的 AI 预审助手...",
  "state": "BASIC_INFO",
  "identified_risks": [],
  "is_complete": false
}
```

#### POST /api/ai/v2/precheck/message

**Request:**
```json
{
  "session_id": "uuid",
  "message": "我是软件工程师"
}
```

**Response:**
```json
{
  "response": "了解了。接下来问问您的居住情况...",
  "state": "HOUSING_CHECK",
  "is_complete": false,
  "identified_risks": [],
  "collected_data": {...}
}
```

---

## 5. 错误处理

### 5.1 错误码定义

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查请求体格式 |
| 401 | 未授权 | 检查登录状态 |
| 422 | 验证错误 | 检查字段类型 |
| 500 | 服务器内部错误 | 查看日志，联系开发 |
| 503 | LLM服务不可用 | 使用Mock Fallback |

### 5.2 Fallback策略

| 场景 | Fallback行为 | 用户体验 |
|------|--------------|----------|
| LLM超时 | 使用Mock问题库 | 无感知切换 |
| Embedding失败 | 使用规则匹配 | 匹配精度降低 |
| 数据库错误 | 返回空列表+错误提示 | 友好提示 |

---

## 6. 性能指标

### 6.1 响应时间目标

| 接口 | 目标P95 | 最大容忍 |
|------|---------|----------|
| /questionnaire/next | <500ms | <2s |
| /match/recommendations | <1s | <3s |
| /precheck/message | <500ms | <2s |

### 6.2 并发能力

- 单实例: 支持100并发
- 建议部署: 2-3实例 + 负载均衡

---

## 7. 部署配置

### 7.1 环境变量

```bash
# AI Provider
AI_PROVIDER=longcat

# LongCat配置
LONGCAT_API_KEY=your_api_key
LONGCAT_SECRET_KEY=your_secret
LONGCAT_BASE_URL=https://api.longcat.chat/openai
LONGCAT_MODEL=LongCat-Flash-Thinking

# Embedding配置
EMBEDDING_MODE=local
EMBEDDING_MODEL_NAME=BAAI/bge-large-zh-v1.5
EMBEDDING_DIMENSION=1024
```

### 7.2 依赖安装

```bash
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
sentence-transformers==2.2.2
numpy==1.24.3
httpx==0.25.2
```

---

## 8. 监控与日志

### 8.1 关键日志

```python
# 问卷模块
logger.info(f"LLM 生成问题成功: {current_field}")
logger.info(f"使用 Mock 问题，当前轮数: {turn}")

# 匹配模块
logger.info(f"匹配完成: 用户{user_id} -> 宠物{pet_id}, 得分{score}")

# 预审模块
logger.info(f"预审会话: {session_id}, 状态: {state}, 风险: {risks}")
```

### 8.2 监控指标

- API响应时间
- LLM调用成功率
- Fallback触发率
- 匹配结果点击率
- 预审完成率

---

**文档维护记录**

| 日期 | 版本 | 修改内容 | 作者 |
|------|------|----------|------|
| 2026-02-06 | v2.0 | 初始版本 | AI产品实习生 |
