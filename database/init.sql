-- Fitmealor Database Schema
-- Generated for multilingual meal recommendation platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    preferred_language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Health profiles
CREATE TABLE health_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    age INTEGER,
    gender VARCHAR(20),
    height_cm DECIMAL(5,2),
    weight_kg DECIMAL(5,2),
    target_weight_kg DECIMAL(5,2),
    activity_level VARCHAR(50), -- sedentary, light, moderate, active, very_active
    health_goal VARCHAR(50), -- lose_weight, maintain, gain_muscle, bulk_up
    tdee INTEGER, -- Total Daily Energy Expenditure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Allergies and dietary restrictions
CREATE TABLE allergies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    allergen_name VARCHAR(100) NOT NULL,
    allergen_name_ko VARCHAR(100),
    allergen_name_en VARCHAR(100),
    severity VARCHAR(20), -- mild, moderate, severe, life_threatening
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Common allergen reference table
CREATE TABLE allergen_reference (
    id SERIAL PRIMARY KEY,
    name_en VARCHAR(100) NOT NULL,
    name_ko VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100),
    name_ja VARCHAR(100),
    keywords_en TEXT[], -- array of synonyms/related terms
    keywords_ko TEXT[],
    category VARCHAR(50) -- dairy, nuts, seafood, grains, etc.
);

-- Dietary restrictions
CREATE TABLE dietary_restrictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    restriction_type VARCHAR(50) NOT NULL, -- vegetarian, vegan, halal, kosher, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meals/Foods database
CREATE TABLE meals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name_ko VARCHAR(255) NOT NULL,
    name_en VARCHAR(255),
    name_zh VARCHAR(255),
    name_ja VARCHAR(255),
    description_ko TEXT,
    description_en TEXT,
    category VARCHAR(50), -- korean, western, japanese, chinese, etc.
    meal_type VARCHAR(50), -- breakfast, lunch, dinner, snack
    calories INTEGER,
    protein_g DECIMAL(6,2),
    carbs_g DECIMAL(6,2),
    fat_g DECIMAL(6,2),
    fiber_g DECIMAL(6,2),
    sodium_mg DECIMAL(8,2),
    sugar_g DECIMAL(6,2),
    image_url TEXT,
    ingredients_ko TEXT,
    ingredients_en TEXT,
    is_vegetarian BOOLEAN DEFAULT FALSE,
    is_vegan BOOLEAN DEFAULT FALSE,
    is_halal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meal allergens (junction table)
CREATE TABLE meal_allergens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meal_id UUID REFERENCES meals(id) ON DELETE CASCADE,
    allergen_id INTEGER REFERENCES allergen_reference(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OCR Scan History
CREATE TABLE ocr_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    extracted_text TEXT,
    detected_allergens TEXT[],
    warning_level VARCHAR(20), -- safe, caution, danger
    language VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Recommendations
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    meal_id UUID REFERENCES meals(id) ON DELETE CASCADE,
    recommendation_score DECIMAL(5,2),
    reason_en TEXT,
    reason_ko TEXT,
    nutrition_analysis JSONB, -- detailed nutritional breakdown
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User favorites
CREATE TABLE favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    meal_id UUID REFERENCES meals(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, meal_id)
);

-- Meal logs (eating history)
CREATE TABLE meal_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    meal_id UUID REFERENCES meals(id) ON DELETE CASCADE,
    consumed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    portion_size DECIMAL(3,2) DEFAULT 1.0, -- 0.5 = half portion, 1.0 = full, etc.
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User events (for analytics)
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- view, click, favorite, order, etc.
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert common allergens
INSERT INTO allergen_reference (name_en, name_ko, name_zh, name_ja, keywords_en, keywords_ko, category) VALUES
('Peanuts', '땅콩', '花生', 'ピーナッツ', ARRAY['peanut', 'groundnut', 'goober'], ARRAY['땅콩', '낙화생'], 'nuts'),
('Tree Nuts', '견과류', '坚果', 'ナッツ', ARRAY['almond', 'walnut', 'cashew', 'pistachio'], ARRAY['아몬드', '호두', '캐슈넛', '피스타치오'], 'nuts'),
('Milk', '우유', '牛奶', '牛乳', ARRAY['dairy', 'lactose', 'milk', 'cheese', 'butter'], ARRAY['우유', '유제품', '유당', '치즈', '버터'], 'dairy'),
('Eggs', '계란', '鸡蛋', '卵', ARRAY['egg', 'albumin'], ARRAY['계란', '달걀', '난류'], 'eggs'),
('Fish', '생선', '鱼', '魚', ARRAY['fish', 'salmon', 'tuna', 'cod'], ARRAY['생선', '어류', '연어', '참치'], 'seafood'),
('Shellfish', '갑각류', '贝类', '甲殻類', ARRAY['shrimp', 'crab', 'lobster', 'clam'], ARRAY['새우', '게', '랍스터', '조개'], 'seafood'),
('Wheat', '밀', '小麦', '小麦', ARRAY['wheat', 'gluten', 'flour'], ARRAY['밀', '밀가루', '글루텐'], 'grains'),
('Soy', '콩', '大豆', '大豆', ARRAY['soy', 'soybean', 'tofu'], ARRAY['콩', '대두', '두부'], 'legumes'),
('Sesame', '참깨', '芝麻', 'ゴマ', ARRAY['sesame'], ARRAY['참깨', '깨'], 'seeds');

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_health_profiles_user_id ON health_profiles(user_id);
CREATE INDEX idx_allergies_user_id ON allergies(user_id);
CREATE INDEX idx_meals_category ON meals(category);
CREATE INDEX idx_meal_allergens_meal_id ON meal_allergens(meal_id);
CREATE INDEX idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX idx_favorites_user_id ON favorites(user_id);
CREATE INDEX idx_meal_logs_user_id ON meal_logs(user_id);
CREATE INDEX idx_ocr_scans_user_id ON ocr_scans(user_id);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_health_profiles_updated_at BEFORE UPDATE ON health_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meals_updated_at BEFORE UPDATE ON meals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
