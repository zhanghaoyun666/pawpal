-- Users (Coordinators and Regular Users)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT, -- Stored securely
    name TEXT,
    avatar_url TEXT,
    role TEXT DEFAULT 'user' -- 'user' or 'coordinator'
);

-- Pets
CREATE TABLE pets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    breed TEXT,
    age_text TEXT, -- e.g., "2岁"
    age_value INTEGER, -- for sorting
    image_url TEXT,
    category TEXT,
    price TEXT,
    gender TEXT,
    weight TEXT,
    tags TEXT[],
    description TEXT,
    location TEXT,
    owner_id UUID REFERENCES users(id),
    health_info JSONB, -- {vaccinated: bool, ...}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Favorites
CREATE TABLE favorites (
    user_id UUID NOT NULL, -- Simplified for MVP, can reference users(id) if auth is strict
    pet_id UUID REFERENCES pets(id),
    PRIMARY KEY (user_id, pet_id)
);

-- Chat Sessions (Conversation)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL, 
    pet_id UUID REFERENCES pets(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Adoption Applications
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL, -- Pet being applied for (frontend should pass this)
    user_id UUID NOT NULL, -- Applicant
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    occupation TEXT,
    housing TEXT, -- apartment, house, etc.
    has_experience BOOLEAN,
    reason TEXT,
    status TEXT DEFAULT 'pending', -- pending, approved, rejected
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    sender_id UUID NOT NULL,
    content TEXT,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert Dummy Data
INSERT INTO users (id, email, name, avatar_url, role) VALUES 
('00000000-0000-0000-0000-000000000000', 'test@example.com', 'Test User', '', 'user'),
('11111111-1111-1111-1111-111111111111', 'sarah@example.com', 'Sarah Wilson', 'https://lh3.googleusercontent.com/aida-public/AB6AXuDPVpLiTvjm3XOaQwsBrF6Qrltmi8yr7_fSnxcOTBNe2iwxvEZ5IuLrtEkD4T9Yp1mDiX9wrRVzH2a6zzTeUKoAaP90CdNTbpDLpEQkqFQEBBF6iUbvMGFj93CvOllMZo9jdmXquulhZY1umcQKVWu4jIoBn3UPTzlGRCZ_XdXxzRAFA5XtDAy0MhFV4I_rIX2m8SoMWjPToqk63I5x780gfOc3R7hWC3Nf0iOC70HGXlInN7XjLA0fgq5W7LX8ERxXPJ2YAkeIIjw', 'coordinator');

INSERT INTO pets (name, breed, age_text, age_value, image_url, category, location, owner_id, description) VALUES
('Max', '金毛寻回犬', '2岁', 24, 'https://images.unsplash.com/photo-1552053831-71594a27632d?q=80&w=1262&auto=format&fit=crop', 'dog', '上海, 浦东新区', '11111111-1111-1111-1111-111111111111', 'Max 是一只无比可爱的金毛寻回犬...'),
('Luna', '波斯猫', '1岁', 12, 'https://images.unsplash.com/photo-1573865526739-10659fec78a5?q=80&w=1315&auto=format&fit=crop', 'cat', '上海, 静安区', '11111111-1111-1111-1111-111111111111', 'Luna 是一只优雅安静的波斯猫。'),
('Charlie', '比格犬', '4个月', 4, 'https://images.unsplash.com/photo-1537151625747-768eb6cf92b2?q=80&w=1285&auto=format&fit=crop', 'dog', '上海, 黄浦区', '11111111-1111-1111-1111-111111111111', 'Charlie 是一只精力充沛的小狗。'),
('Bella', '拉布拉多', '3岁', 36, 'https://images.unsplash.com/photo-1591769225440-811ad7d6eca6?q=80&w=1287&auto=format&fit=crop', 'dog', '上海, 闵行区', '11111111-1111-1111-1111-111111111111', 'Bella 非常温顺，是完美的家庭伴侣犬。'),
('Coco', '泰迪', '2岁', 24, 'https://images.unsplash.com/photo-1583511655826-05700d52f4d9?q=80&w=1288&auto=format&fit=crop', 'dog', '上海, 徐汇区', '11111111-1111-1111-1111-111111111111', 'Coco 活泼可爱，喜欢粘人。'),
('Milo', '英国短毛猫', '1.5岁', 18, 'https://images.unsplash.com/photo-1513245543132-31f507417b26?q=80&w=1275&auto=format&fit=crop', 'cat', '上海, 长宁区', '11111111-1111-1111-1111-111111111111', 'Milo 性格独立，但也喜欢被抚摸。'),
('Rocky', '哈士奇', '1岁', 12, 'https://images.unsplash.com/photo-1605568427561-40dd23c2acea?q=80&w=1287&auto=format&fit=crop', 'dog', '上海, 普陀区', '11111111-1111-1111-1111-111111111111', 'Rocky 精力旺盛，需要有经验的主人。'),
('Oreo', '边境牧羊犬', '2岁', 24, 'https://images.unsplash.com/photo-1503256207526-0d5d80fa2f47?q=80&w=1286&auto=format&fit=crop', 'dog', '上海, 松江区', '11111111-1111-1111-1111-111111111111', 'Oreo 非常聪明，已经学会了很多指令。');
