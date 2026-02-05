-- AI 功能数据库迁移脚本
-- 创建支持 20维画像、Embedding 向量、历史反馈的表结构

-- ============================================
-- 1. 领养人画像表（20维）
-- ============================================
CREATE TABLE IF NOT EXISTS adopter_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- 基础信息（3维）
    living_space VARCHAR(50) CHECK (living_space IN ('small_apartment', 'medium_apartment', 'large_apartment', 'house_with_yard', 'rural')),
    has_yard BOOLEAN DEFAULT FALSE,
    is_renting BOOLEAN,
    landlord_allows_pets BOOLEAN,
    
    -- 经济能力（2维）
    budget_level VARCHAR(20) CHECK (budget_level IN ('low', 'medium', 'high')),
    income_stability VARCHAR(20) CHECK (income_stability IN ('stable', 'unstable', 'student')),
    
    -- 时间投入（3维）
    daily_time_available INTEGER CHECK (daily_time_available >= 0 AND daily_time_available <= 24),
    work_schedule VARCHAR(50) CHECK (work_schedule IN ('regular', 'flexible', 'shift', 'frequent_travel', 'remote')),
    work_hours_per_day INTEGER CHECK (work_hours_per_day >= 0 AND work_hours_per_day <= 16),
    
    -- 经验能力（3维）
    experience_level VARCHAR(50) CHECK (experience_level IN ('none', 'beginner', 'intermediate', 'experienced')),
    previous_pets TEXT[], -- 曾养过的宠物种类
    training_willingness VARCHAR(20) CHECK (training_willingness IN ('low', 'medium', 'high')),
    
    -- 家庭状况（2维）
    family_status VARCHAR(50) CHECK (family_status IN ('single', 'couple', 'with_kids_young', 'with_kids_old', 'with_elderly', 'multi_gen')),
    household_size INTEGER CHECK (household_size >= 1 AND household_size <= 10),
    
    -- 偏好匹配（5维）
    preferred_size VARCHAR(20) CHECK (preferred_size IN ('tiny', 'small', 'medium', 'large', 'xlarge', 'no_preference')),
    preferred_age VARCHAR(20) CHECK (preferred_age IN ('baby', 'young', 'adult', 'senior', 'no_preference')),
    preferred_temperament TEXT[], -- 偏好性格标签
    activity_level VARCHAR(20) CHECK (activity_level IN ('low', 'medium', 'high')),
    other_pets TEXT[], -- 家中现有宠物
    
    -- 容忍度（3维）
    noise_tolerance VARCHAR(20) CHECK (noise_tolerance IN ('low', 'medium', 'high')),
    shedding_tolerance VARCHAR(20) CHECK (shedding_tolerance IN ('none', 'low', 'medium', 'high')),
    grooming_willingness VARCHAR(20) CHECK (grooming_willingness IN ('low', 'medium', 'high')),
    
    -- 特殊需求
    has_allergies BOOLEAN DEFAULT FALSE,
    allergy_details TEXT,
    must_have_traits TEXT[],
    deal_breakers TEXT[],
    
    -- Embedding 向量（用于相似度搜索）
    profile_embedding VECTOR(1024),
    
    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- 创建索引
CREATE INDEX idx_adopter_profiles_user_id ON adopter_profiles(user_id);
CREATE INDEX idx_adopter_profiles_embedding ON adopter_profiles USING ivfflat (profile_embedding vector_cosine_ops);

-- ============================================
-- 2. 宠物档案增强表
-- ============================================
-- 在现有 pets 表基础上添加字段
ALTER TABLE pets ADD COLUMN IF NOT EXISTS size_category VARCHAR(20) CHECK (size_category IN ('tiny', 'small', 'medium', 'large', 'xlarge'));
ALTER TABLE pets ADD COLUMN IF NOT EXISTS energy_level VARCHAR(20) CHECK (energy_level IN ('low', 'medium', 'high'));
ALTER TABLE pets ADD COLUMN IF NOT EXISTS sociability VARCHAR(20) CHECK (sociability IN ('shy', 'moderate', 'outgoing'));
ALTER TABLE pets ADD COLUMN IF NOT EXISTS trainability VARCHAR(20) CHECK (trainability IN ('easy', 'moderate', 'difficult'));
ALTER TABLE pets ADD COLUMN IF NOT EXISTS shedding_level VARCHAR(20) CHECK (shedding_level IN ('none', 'low', 'medium', 'high'));
ALTER TABLE pets ADD COLUMN IF NOT EXISTS grooming_needs VARCHAR(20) CHECK (grooming_needs IN ('low', 'medium', 'high'));
ALTER TABLE pets ADD COLUMN IF NOT EXISTS exercise_needs VARCHAR(20) CHECK (exercise_needs IN ('low', 'medium', 'high'));
ALTER TABLE pets ADD COLUMN IF NOT EXISTS good_with_kids BOOLEAN DEFAULT TRUE;
ALTER TABLE pets ADD COLUMN IF NOT EXISTS good_with_dogs BOOLEAN DEFAULT TRUE;
ALTER TABLE pets ADD COLUMN IF NOT EXISTS good_with_cats BOOLEAN DEFAULT TRUE;
ALTER TABLE pets ADD COLUMN IF NOT EXISTS good_with_strangers BOOLEAN DEFAULT TRUE;
ALTER TABLE pets ADD COLUMN IF NOT EXISTS special_needs TEXT[];
ALTER TABLE pets ADD COLUMN IF NOT EXISTS min_space_requirement VARCHAR(50);
ALTER TABLE pets ADD COLUMN IF NOT EXISTS needs_yard BOOLEAN DEFAULT FALSE;
ALTER TABLE pets ADD COLUMN IF NOT EXISTS pet_embedding VECTOR(1024); -- 宠物档案向量
ALTER TABLE pets ADD COLUMN IF NOT EXISTS success_rate DECIMAL(3,2); -- 历史成功率 0-1

-- 创建索引
CREATE INDEX idx_pets_embedding ON pets USING ivfflat (pet_embedding vector_cosine_ops);
CREATE INDEX idx_pets_success_rate ON pets(success_rate);

-- ============================================
-- 3. 领养后反馈表（用于计算历史成功率）
-- ============================================
CREATE TABLE IF NOT EXISTS adoption_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    pet_id UUID REFERENCES pets(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- 领养结果
    outcome VARCHAR(20) CHECK (outcome IN ('success', 'returned', 'issue', 'ongoing')),
    duration_days INTEGER, -- 领养持续天数
    
    -- 反馈内容
    feedback_text TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    issues TEXT[], -- 出现的问题
    
    -- 画像摘要（用于相似度计算）
    adopter_profile_summary JSONB,
    profile_embedding VECTOR(1024),
    
    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_adoption_feedback_pet_id ON adoption_feedback(pet_id);
CREATE INDEX idx_adoption_feedback_user_id ON adoption_feedback(user_id);
CREATE INDEX idx_adoption_feedback_outcome ON adoption_feedback(outcome);
CREATE INDEX idx_adoption_feedback_embedding ON adoption_feedback USING ivfflat (profile_embedding vector_cosine_ops);

-- ============================================
-- 4. AI 预审会话表
-- ============================================
CREATE TABLE IF NOT EXISTS precheck_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    pet_id UUID REFERENCES pets(id) ON DELETE CASCADE,
    
    -- 会话状态
    state VARCHAR(50) NOT NULL,
    is_complete BOOLEAN DEFAULT FALSE,
    turn_count INTEGER DEFAULT 0,
    
    -- 收集的数据
    collected_data JSONB DEFAULT '{}',
    confirmed_info JSONB DEFAULT '{}',
    identified_risks JSONB DEFAULT '[]',
    clarified_risks JSONB DEFAULT '[]',
    
    -- 对话历史
    chat_history JSONB DEFAULT '[]',
    
    -- 最终结果
    result JSONB,
    
    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 hours')
);

-- 创建索引
CREATE INDEX idx_precheck_sessions_session_id ON precheck_sessions(session_id);
CREATE INDEX idx_precheck_sessions_user_id ON precheck_sessions(user_id);
CREATE INDEX idx_precheck_sessions_expires ON precheck_sessions(expires_at);

-- ============================================
-- 5. AI 预审结果表（与申请关联）
-- ============================================
CREATE TABLE IF NOT EXISTS ai_precheck_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    
    -- 预审结果
    passed BOOLEAN NOT NULL,
    score INTEGER CHECK (score >= 0 AND score <= 100),
    risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high')),
    risk_points JSONB DEFAULT '[]',
    suggestions JSONB DEFAULT '[]',
    auto_approved BOOLEAN DEFAULT FALSE,
    
    -- 审核报告
    review_report TEXT,
    
    -- 关联的会话
    session_id VARCHAR(255) REFERENCES precheck_sessions(session_id),
    
    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(application_id)
);

-- 创建索引
CREATE INDEX idx_ai_precheck_results_application_id ON ai_precheck_results(application_id);
CREATE INDEX idx_ai_precheck_results_risk_level ON ai_precheck_results(risk_level);

-- ============================================
-- 6. 触发器：自动更新时间戳
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为所有表添加自动更新时间戳触发器
CREATE TRIGGER update_adopter_profiles_updated_at BEFORE UPDATE ON adopter_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_adoption_feedback_updated_at BEFORE UPDATE ON adoption_feedback
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_precheck_sessions_updated_at BEFORE UPDATE ON precheck_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_precheck_results_updated_at BEFORE UPDATE ON ai_precheck_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 7. RLS 策略（行级安全）
-- ============================================

-- 领养人画像：用户只能看到自己的
ALTER TABLE adopter_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON adopter_profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile" ON adopter_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" ON adopter_profiles
    FOR UPDATE USING (auth.uid() = user_id);

-- 领养反馈：用户只能看到自己的，协调员可以看到所有
ALTER TABLE adoption_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own feedback" ON adoption_feedback
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Coordinators can view all feedback" ON adoption_feedback
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users WHERE id = auth.uid() AND role = 'coordinator'
        )
    );

-- 预审会话：用户只能看到自己的
ALTER TABLE precheck_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own sessions" ON precheck_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions" ON precheck_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 预审结果：用户只能看到自己的，协调员可以看到所有
ALTER TABLE ai_precheck_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own results" ON ai_precheck_results
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM applications WHERE id = application_id AND user_id = auth.uid()
        )
    );

CREATE POLICY "Coordinators can view all results" ON ai_precheck_results
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users WHERE id = auth.uid() AND role = 'coordinator'
        )
    );

-- ============================================
-- 8. 初始化数据：为现有宠物生成默认标签
-- ============================================

-- 根据现有数据推断标签
UPDATE pets SET
    size_category = CASE
        WHEN weight LIKE '%kg%' THEN 
            CASE 
                WHEN CAST(REPLACE(REPLACE(weight, 'kg', ''), ' ', '') AS DECIMAL) < 5 THEN 'tiny'
                WHEN CAST(REPLACE(REPLACE(weight, 'kg', ''), ' ', '') AS DECIMAL) < 10 THEN 'small'
                WHEN CAST(REPLACE(REPLACE(weight, 'kg', ''), ' ', '') AS DECIMAL) < 25 THEN 'medium'
                WHEN CAST(REPLACE(REPLACE(weight, 'kg', ''), ' ', '') AS DECIMAL) < 40 THEN 'large'
                ELSE 'xlarge'
            END
        ELSE 'medium'
    END,
    energy_level = CASE
        WHEN age_value < 12 THEN 'high'
        WHEN age_value > 84 THEN 'low'
        ELSE 'medium'
    END,
    exercise_needs = CASE
        WHEN age_value < 12 THEN 'high'
        WHEN age_value > 84 THEN 'low'
        ELSE 'medium'
    END,
    shedding_level = 'medium',
    grooming_needs = 'medium',
    trainability = 'moderate',
    sociability = 'moderate',
    min_space_requirement = 'medium_apartment',
    success_rate = 0.5; -- 冷启动默认值

-- 注释说明
COMMENT ON TABLE adopter_profiles IS '领养人20维画像表';
COMMENT ON TABLE adoption_feedback IS '领养后反馈表，用于计算历史成功率';
COMMENT ON TABLE precheck_sessions IS 'AI预审会话状态表';
COMMENT ON TABLE ai_precheck_results IS 'AI预审结果表';
