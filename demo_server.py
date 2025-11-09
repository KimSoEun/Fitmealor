"""
Fitmealor Demo Server
With SQLite database persistence
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
import uvicorn
import hashlib
import secrets
from datetime import datetime
import os
import sqlite3
import json
from openai import OpenAI

app = FastAPI(
    title="Fitmealor AI Service (Demo)",
    description="AI-powered meal recommendation - Demo Mode",
    version="1.0.0-demo"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_PATH = "fitmealor.db"

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            height_cm REAL NOT NULL,
            weight_kg REAL NOT NULL,
            target_weight_kg REAL NOT NULL,
            activity_level TEXT NOT NULL,
            health_goal TEXT NOT NULL,
            allergies TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Create tokens table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE
        )
    """)

    # Create meals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            meal_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            name_en TEXT,
            brand TEXT,
            category TEXT,
            ingredients TEXT,
            allergens TEXT,
            calories INTEGER,
            protein_g REAL,
            carbs_g REAL,
            fat_g REAL,
            sodium_mg INTEGER,
            serving_size TEXT,
            origin TEXT,
            explanation_en TEXT,
            explanation_ko TEXT,
            score INTEGER DEFAULT 80
        )
    """)

    conn.commit()
    conn.close()

def get_all_meals_from_db():
    """Retrieve all meals from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM meals")
    rows = cursor.fetchall()

    meals = []
    for row in rows:
        meal = {
            "meal_id": row[0],
            "name": row[1],
            "name_en": row[2],
            "brand": row[3],
            "category": row[4],
            "ingredients": json.loads(row[5]) if row[5] else [],
            "allergens": json.loads(row[6]) if row[6] else [],
            "calories": row[7],
            "protein_g": row[8],
            "carbs_g": row[9],
            "fat_g": row[10],
            "sodium_mg": row[11],
            "serving_size": row[12],
            "origin": row[13],
            "explanation_en": row[14],
            "explanation_ko": row[15],
            "score": row[16]
        }
        meals.append(meal)

    conn.close()
    return meals

def import_meals_to_db(meals_data):
    """Import meal data into database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if meals already exist
    cursor.execute("SELECT COUNT(*) FROM meals")
    count = cursor.fetchone()[0]

    if count > 0:
        print(f"📊 Database already contains {count} meals. Skipping import.")
        conn.close()
        return count

    # Import meals
    imported = 0
    for meal in meals_data:
        try:
            cursor.execute("""
                INSERT INTO meals VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                meal["meal_id"],
                meal["name"],
                meal.get("name_en"),
                meal.get("brand"),
                meal.get("category"),
                json.dumps(meal.get("ingredients", [])),
                json.dumps(meal.get("allergens", [])),
                meal.get("calories"),
                meal.get("protein_g"),
                meal.get("carbs_g"),
                meal.get("fat_g"),
                meal.get("sodium_mg"),
                meal.get("serving_size"),
                meal.get("origin"),
                meal.get("explanation_en"),
                meal.get("explanation_ko"),
                meal.get("score", 80)
            ))
            imported += 1
        except Exception as e:
            print(f"❌ Error importing meal {meal.get('meal_id', 'unknown')}: {e}")

    conn.commit()
    conn.close()
    print(f"✅ Imported {imported} meals into database")
    return imported

# Initialize database on startup
init_database()

# Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    target_weight_kg: float
    activity_level: str
    health_goal: str
    allergies: List[str] = []

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class FindAccount(BaseModel):
    email: EmailStr

class ProfileUpdate(BaseModel):
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    target_weight_kg: float
    activity_level: str
    health_goal: str
    allergies: List[str] = []

class RecommendationRequest(BaseModel):
    user_id: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    target_weight_kg: float
    activity_level: str
    health_goal: str
    allergies: List[str] = []
    symptoms: Optional[List[str]] = None
    body_condition: Optional[str] = ""  # New field for chat input
    preferences: Optional[Dict] = {}  # ChatGPT-extracted food preferences

class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def generate_recommendation_reason(body_condition: str, health_goal: str, current_weight: float, target_weight: float, tdee: int, meal_count: int) -> str:
    """Generate a conversational explanation for why these meals were recommended"""

    goal_messages = {
        "lose_weight": {
            "en": "weight loss",
            "ko": "체중 감량"
        },
        "maintain": {
            "en": "weight maintenance",
            "ko": "체중 유지"
        },
        "gain_muscle": {
            "en": "muscle gain",
            "ko": "근육 증가"
        },
        "bulk_up": {
            "en": "bulking up",
            "ko": "벌크업"
        }
    }

    goal_info = goal_messages.get(health_goal, {"en": "your health goal", "ko": "건강 목표"})
    weight_diff = abs(target_weight - current_weight)

    # Base recommendation message
    reason = f"Based on your {goal_info['en']} goal ({goal_info['ko']} 목표), I've selected {meal_count} meals with around {tdee} kcal/day. "

    # Add body condition context if provided - HEALTH FIRST!
    if body_condition and body_condition.strip():
        condition_lower = body_condition.lower()

        # CRITICAL HEALTH CONDITIONS - Strong warnings!
        if any(word in condition_lower for word in ["단백뇨", "proteinuria", "신장", "kidney", "콩팥"]):
            reason += "⚠️ IMPORTANT: Due to kidney concerns, I selected LOW-PROTEIN and LOW-SODIUM meals to protect your kidney health. Please consult a doctor. 신장 건강을 고려하여 저단백, 저염 식단을 선택했습니다. 의사 상담을 권장합니다. "

        elif any(word in condition_lower for word in ["저단백", "low protein", "낮은 단백질"]):
            reason += "✅ As requested, I selected LOW-PROTEIN meals (less than 15g protein per serving). 요청하신 대로 저단백 식단(1회 제공량당 15g 이하)을 선택했습니다. "

        elif any(word in condition_lower for word in ["저탄수", "low carb", "낮은 탄수화물"]):
            reason += "✅ As requested, I selected LOW-CARB meals (less than 30g carbs per serving). 요청하신 대로 저탄수화물 식단(1회 제공량당 30g 이하)을 선택했습니다. "

        elif any(word in condition_lower for word in ["당뇨", "diabetes", "혈당", "blood sugar"]):
            reason += "⚠️ For blood sugar management, I chose LOW-CARB meals with complex carbohydrates to help stabilize your glucose levels. 혈당 관리를 위해 저탄수화물 식단을 선택했습니다. "

        elif any(word in condition_lower for word in ["저염", "low sodium", "낮은 나트륨", "low salt"]):
            reason += "✅ As requested, I selected LOW-SODIUM meals (less than 300mg per serving). 요청하신 대로 저염 식단(1회 제공량당 300mg 이하)을 선택했습니다. "

        elif any(word in condition_lower for word in ["고혈압", "hypertension", "blood pressure"]):
            reason += "⚠️ For blood pressure management, I selected LOW-SODIUM meals to support your cardiovascular health. 혈압 관리를 위해 저염 식단을 선택했습니다. "

        # NON-CRITICAL CONDITIONS
        elif any(word in condition_lower for word in ["고단백", "high protein", "높은 단백질", "단백질 많이"]):
            reason += "✅ As requested, I selected HIGH-PROTEIN meals (more than 20g protein per serving). 요청하신 대로 고단백 식단(1회 제공량당 20g 이상)을 선택했습니다. "

        elif any(word in condition_lower for word in ["피곤", "tired", "fatigue", "exhausted", "지침"]):
            reason += "Since you're feeling tired, I focused on moderate-protein and vitamin-rich meals for energy. 피곤하시다고 하셔서 에너지를 위한 적정 단백질, 비타민이 풍부한 식단을 선택했습니다. "

        elif any(word in condition_lower for word in ["소화", "digestion", "indigestion", "stomach", "배", "속"]):
            reason += "For your digestion concerns, I chose easily digestible and low-sodium meals. 소화 문제를 고려하여 소화가 잘 되고 저염 식단을 선택했습니다. "

        elif any(word in condition_lower for word in ["근육", "muscle", "pain", "sore", "아프", "통증"]):
            reason += "To help with muscle recovery, I selected moderate-protein meals with anti-inflammatory benefits. 근육 회복을 위해 적정 단백질 및 항염 효과가 있는 식단을 선택했습니다. "

        elif any(word in condition_lower for word in ["스트레스", "stress", "압박", "불안", "anxiety"]):
            reason += "To help manage stress, I picked balanced meals with complex carbs and calming nutrients. 스트레스 관리를 위해 복합 탄수화물과 안정 효과가 있는 균형잡힌 식단을 선택했습니다. "

        # General body condition mentioned
        else:
            reason += f"Considering your current condition ('{body_condition[:50]}...'), I customized these meals for your needs. 현재 몸 상태를 고려하여 맞춤 식단을 준비했습니다. "

    else:
        # No body condition provided
        if health_goal == "lose_weight":
            reason += "These meals are lower in calories but high in protein to keep you satisfied. 칼로리는 낮지만 단백질이 풍부하여 포만감을 유지합니다. "
        elif health_goal == "gain_muscle":
            reason += "These meals are protein-rich to support muscle growth and recovery. 근육 성장과 회복을 위한 고단백 식단입니다. "
        elif health_goal == "bulk_up":
            reason += "These meals have higher calories and protein for effective bulking. 효과적인 벌크업을 위한 고칼로리, 고단백 식단입니다. "
        else:
            reason += "These balanced meals will help you maintain your current weight. 현재 체중 유지를 위한 균형잡힌 식단입니다. "

    reason += "Enjoy your meals! 맛있게 드세요! 😊"

    return reason

def adjust_meal_score_for_condition(meal: dict, body_condition: str, health_goal: str, preferences: dict = None) -> int:
    """Adjust meal score based on body condition, health goal, and ChatGPT-extracted food preferences - HEALTH FIRST!"""
    base_score = meal.get("score", 80)
    bonus = 0

    # Helper function to safely get numeric values (handle None)
    def safe_get(key, default=0):
        value = meal.get(key, default)
        return value if value is not None else default

    # Apply ChatGPT-extracted food preferences FIRST (highest priority after health)
    if preferences:
        meal_name_lower = meal.get("name", "").lower()
        ingredients = meal.get("ingredients", [])
        ingredients_str = " ".join(ingredients).lower()

        # Check DISLIKED foods FIRST - VERY strong penalty!
        disliked_foods = preferences.get("disliked_foods", [])
        for disliked_food in disliked_foods:
            disliked_lower = disliked_food.lower()
            # Check both exact match and partial match (닭 in 닭가슴살)
            if disliked_lower in meal_name_lower or disliked_lower in ingredients_str:
                print(f"[DISLIKE MATCH] Meal '{meal.get('name')}' contains disliked food '{disliked_food}' - Applying -100 penalty")
                bonus -= 100  # MASSIVE penalty for disliked foods! Should push it to bottom
                break

        # Check LIKED foods - MASSIVE boost!
        liked_foods = preferences.get("liked_foods", [])
        for liked_food in liked_foods:
            liked_lower = liked_food.lower()
            if liked_lower in meal_name_lower or liked_lower in ingredients_str:
                print(f"[LIKE MATCH] Meal '{meal.get('name')}' contains liked food '{liked_food}' - Applying +100 bonus")
                bonus += 100  # MASSIVE boost for liked foods!
                break

    if not body_condition or not body_condition.strip():
        # No health concerns, apply general health goal adjustments
        if health_goal == "lose_weight":
            if safe_get("calories", 999) < 350:
                bonus += 5
            if safe_get("protein_g", 0) > 15:
                bonus += 5
        elif health_goal == "gain_muscle" or health_goal == "bulk_up":
            if safe_get("protein_g", 0) > 20:
                bonus += 10
            if safe_get("calories", 0) > 400:
                bonus += 5
        return max(base_score + bonus, 0)  # Remove upper cap - let preference bonuses work!

    condition_lower = body_condition.lower()
    meal_name_lower = meal.get("name", "").lower()
    ingredients = [ing.lower() for ing in meal.get("ingredients", [])]

    # CRITICAL HEALTH CONDITIONS - Override any fitness goals!

    # Low protein request OR Kidney issues (proteinuria/단백뇨) - AVOID high protein, AVOID high sodium
    if any(word in condition_lower for word in ["단백뇨", "proteinuria", "신장", "kidney", "콩팥", "저단백", "low protein", "낮은 단백질"]):
        # Penalize high protein heavily
        if safe_get("protein_g", 0) > 20:
            bonus -= 30  # Strong penalty
        elif safe_get("protein_g", 0) > 15:
            bonus -= 15
        # Penalize high sodium
        if safe_get("sodium_mg", 0) > 600:
            bonus -= 20
        elif safe_get("sodium_mg", 0) > 400:
            bonus -= 10
        # Prefer low protein, low sodium
        if safe_get("protein_g", 0) < 12 and safe_get("sodium_mg", 0) < 400:
            bonus += 25
        if any(ing in meal_name_lower or ing in str(ingredients) for ing in ["채소", "vegetable", "샐러드", "salad", "과일", "fruit"]):
            bonus += 15
        # Ignore fitness goals for kidney health!
        return max(base_score + bonus, 0)  # Remove upper cap - let preference bonuses work!

    # Low carb request OR Diabetes/High blood sugar - AVOID high carbs
    if any(word in condition_lower for word in ["당뇨", "diabetes", "혈당", "blood sugar", "저탄수", "low carb", "낮은 탄수화물"]):
        if safe_get("carbs_g", 0) > 60:
            bonus -= 25
        elif safe_get("carbs_g", 0) < 30:
            bonus += 15
        if any(ing in meal_name_lower or ing in str(ingredients) for ing in ["현미", "brown rice", "통곡물", "whole grain", "퀴노아", "quinoa"]):
            bonus += 10
        return max(base_score + bonus, 0)  # Remove upper cap - let preference bonuses work!

    # Low sodium request OR High blood pressure - AVOID sodium
    if any(word in condition_lower for word in ["고혈압", "hypertension", "blood pressure", "저염", "low sodium", "낮은 나트륨", "low salt"]):
        if safe_get("sodium_mg", 0) > 600:
            bonus -= 30
        elif safe_get("sodium_mg", 0) < 300:
            bonus += 20
        return max(base_score + bonus, 0)  # Remove upper cap - let preference bonuses work!

    # NON-CRITICAL CONDITIONS - Can consider fitness goals

    # High protein request - prefer high protein meals
    if any(word in condition_lower for word in ["고단백", "high protein", "높은 단백질", "단백질 많이"]):
        if safe_get("protein_g", 0) > 25:
            bonus += 20
        elif safe_get("protein_g", 0) > 20:
            bonus += 15
        if any(ing in meal_name_lower or ing in str(ingredients) for ing in ["닭", "chicken", "연어", "salmon", "참치", "tuna", "계란", "egg"]):
            bonus += 10
        # Don't return early, allow fitness goal adjustments too

    # Fatigue/Tiredness - prefer moderate protein, iron-rich foods
    elif any(word in condition_lower for word in ["피곤", "tired", "fatigue", "exhausted", "지침"]):
        if safe_get("protein_g", 0) > 15 and safe_get("protein_g", 0) < 25:
            bonus += 15
        if any(ing in meal_name_lower or ing in str(ingredients) for ing in ["연어", "salmon", "닭", "chicken"]):
            bonus += 10
        if any(ing in meal_name_lower or ing in str(ingredients) for ing in ["시금치", "spinach", "브로콜리", "broccoli"]):
            bonus += 5

    # Digestion issues - prefer low sodium, fiber-rich, easy to digest
    elif any(word in condition_lower for word in ["소화", "digestion", "indigestion", "stomach", "배", "속"]):
        if safe_get("sodium_mg", 999) < 500:
            bonus += 15
        if any(ing in meal_name_lower or ing in str(ingredients) for ing in ["퀴노아", "quinoa", "렌틸", "lentil", "채소", "vegetable", "샐러드", "salad"]):
            bonus += 10
        if any(ing in meal_name_lower or ing in str(ingredients) for ing in ["요거트", "yogurt", "프로바이오틱", "probiotic"]):
            bonus += 10
        if safe_get("fat_g", 0) > 15:
            bonus -= 10

    # Muscle pain - prefer moderate protein, anti-inflammatory
    elif any(word in condition_lower for word in ["근육", "muscle", "pain", "sore", "아프", "통증"]):
        if safe_get("protein_g", 0) > 18:
            bonus += 15
        if any(ing in meal_name_lower or ing in str(ingredients) for ing in ["연어", "salmon", "참치", "tuna", "고등어", "mackerel"]):
            bonus += 10
        if any(ing in meal_name_lower or ing in str(ingredients) for ing in ["베리", "berry", "견과", "nuts", "올리브", "olive"]):
            bonus += 5

    # Stress - prefer complex carbs, calming nutrients
    elif any(word in condition_lower for word in ["스트레스", "stress", "압박", "불안", "anxiety"]):
        if 40 < safe_get("carbs_g", 0) < 70:
            bonus += 10
        if any(ing in meal_name_lower or ing in str(ingredients) for ing in ["퀴노아", "quinoa", "현미", "brown rice", "통곡물", "whole grain"]):
            bonus += 10
        if any(ing in meal_name_lower or ing in str(ingredients) for ing in ["연어", "salmon", "아보카도", "avocado"]):
            bonus += 5

    # For non-critical conditions, apply mild fitness goal adjustments
    if health_goal == "lose_weight":
        if safe_get("calories", 999) < 350:
            bonus += 3
    elif health_goal == "gain_muscle" or health_goal == "bulk_up":
        if safe_get("protein_g", 0) > 20:
            bonus += 5

    # SMART INGREDIENT MATCHING: Check if any word from user's request appears in meal name or ingredients
    # This allows flexible matching without hardcoding every possible food item
    condition_words = condition_lower.split()

    for word in condition_words:
        # Skip common words that don't indicate food preferences
        skip_words = ['먹고', '싶어', '싶다', '원해', 'want', 'need', 'like', 'would', 'could', 'today', 'tonight',
                      '오늘', '내일', '그리고', 'and', 'or', '또는', '아니면', '먹을', '먹을래']
        if word in skip_words or len(word) <= 1:
            continue

        # Check if this word appears in meal name or ingredients
        if word in meal_name_lower or word in str(ingredients).lower():
            bonus += 35  # Strong boost for matching ingredient/food name!

    # Additional taste/style preferences
    if any(word in condition_lower for word in ["매운", "spicy"]):
        if any(word in meal_name_lower or word in str(ingredients) for word in ["매운", "spicy", "고추", "불닭"]):
            bonus += 20

    return max(base_score + bonus, 0)  # Remove upper cap - let preference bonuses work!

def get_user_from_token(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace('Bearer ', '')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get email from token
    cursor.execute("SELECT email FROM tokens WHERE token = ?", (token,))
    token_row = cursor.fetchone()

    if not token_row:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid token")

    email = token_row['email']

    # Get user data
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user_row = cursor.fetchone()

    conn.close()

    if not user_row:
        raise HTTPException(status_code=401, detail="User not found")

    # Convert to dict and parse allergies JSON
    user = dict(user_row)
    user['allergies'] = json.loads(user['allergies'])

    return user

# Serve HTML files
@app.get("/")
async def root():
    if os.path.exists("login.html"):
        return FileResponse("login.html")
    return {
        "service": "Fitmealor AI Service",
        "version": "1.0.0-demo",
        "status": "running",
        "mode": "demo",
        "message": "Welcome to Fitmealor - AI-powered meal recommendations"
    }

@app.get("/demo_ui.html")
async def demo_ui():
    return FileResponse("demo_ui.html")

@app.get("/register.html")
async def register_page():
    return FileResponse("register.html")

@app.get("/login.html")
async def login_page():
    return FileResponse("login.html")

@app.get("/profile.html")
async def profile_page():
    return FileResponse("profile.html")

@app.get("/health")
async def health_check():
    # Check if database exists and is accessible
    db_status = "connected"
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()
        db_status = f"connected ({user_count} users)"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "service": "fastapi-demo",
        "database": db_status,
        "ai_models": "ready"
    }

# Authentication endpoints
@app.post("/api/v1/auth/register")
async def register(user_data: UserRegister):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute("SELECT email FROM users WHERE email = ?", (user_data.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered / 이미 등록된 이메일입니다")

    # Insert user into database
    created_at = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO users (
            email, password_hash, name, age, gender,
            height_cm, weight_kg, target_weight_kg,
            activity_level, health_goal, allergies, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_data.email,
        hash_password(user_data.password),
        user_data.name,
        user_data.age,
        user_data.gender,
        user_data.height_cm,
        user_data.weight_kg,
        user_data.target_weight_kg,
        user_data.activity_level,
        user_data.health_goal,
        json.dumps(user_data.allergies),
        created_at
    ))

    # Generate token
    token = generate_token()
    cursor.execute("""
        INSERT INTO tokens (token, email, created_at)
        VALUES (?, ?, ?)
    """, (token, user_data.email, created_at))

    conn.commit()
    conn.close()

    # Return user info (without password)
    user_response = {
        "email": user_data.email,
        "name": user_data.name,
        "age": user_data.age,
        "gender": user_data.gender,
        "height_cm": user_data.height_cm,
        "weight_kg": user_data.weight_kg,
        "target_weight_kg": user_data.target_weight_kg,
        "activity_level": user_data.activity_level,
        "health_goal": user_data.health_goal,
        "allergies": user_data.allergies,
        "created_at": created_at
    }

    return {
        "success": True,
        "message": "Registration successful / 회원가입 성공",
        "token": token,
        "user": user_response
    }

@app.post("/api/v1/auth/login")
async def login(credentials: UserLogin):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE email = ?", (credentials.email,))
    user_row = cursor.fetchone()

    if not user_row:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid email or password / 이메일 또는 비밀번호가 잘못되었습니다")

    user = dict(user_row)

    # Verify password
    if user["password_hash"] != hash_password(credentials.password):
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid email or password / 이메일 또는 비밀번호가 잘못되었습니다")

    # Generate new token
    token = generate_token()
    created_at = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO tokens (token, email, created_at)
        VALUES (?, ?, ?)
    """, (token, credentials.email, created_at))

    conn.commit()
    conn.close()

    # Return user info (without password)
    user_response = {k: v for k, v in user.items() if k != 'password_hash'}
    user_response['allergies'] = json.loads(user_response['allergies'])

    return {
        "success": True,
        "message": "Login successful / 로그인 성공",
        "token": token,
        "user": user_response
    }

@app.get("/api/v1/auth/profile")
async def get_profile(authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    user_response = {k: v for k, v in user.items() if k != 'password_hash'}
    return user_response

@app.put("/api/v1/auth/profile")
async def update_profile(profile: ProfileUpdate, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    email = user['email']

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Update user data in database
    cursor.execute("""
        UPDATE users SET
            age = ?,
            gender = ?,
            height_cm = ?,
            weight_kg = ?,
            target_weight_kg = ?,
            activity_level = ?,
            health_goal = ?,
            allergies = ?
        WHERE email = ?
    """, (
        profile.age,
        profile.gender,
        profile.height_cm,
        profile.weight_kg,
        profile.target_weight_kg,
        profile.activity_level,
        profile.health_goal,
        json.dumps(profile.allergies),
        email
    ))

    conn.commit()
    conn.close()

    # Return updated user info
    user_response = {
        "email": email,
        "name": user['name'],
        "age": profile.age,
        "gender": profile.gender,
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "target_weight_kg": profile.target_weight_kg,
        "activity_level": profile.activity_level,
        "health_goal": profile.health_goal,
        "allergies": profile.allergies,
        "created_at": user['created_at']
    }
    return user_response

@app.post("/api/v1/auth/find-account")
async def find_account(account: FindAccount):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT email, name FROM users WHERE email = ?", (account.email,))
    user_row = cursor.fetchone()

    conn.close()

    if not user_row:
        raise HTTPException(status_code=404, detail="등록되지 않은 이메일입니다 / Email not registered")

    # In demo mode, we'll send the account info
    # In production, this should send a password reset email
    return {
        "success": True,
        "message": f"계정을 찾았습니다! 이메일: {account.email}\n데모 모드에서는 비밀번호 재설정 이메일이 전송됩니다.\nAccount found! In production, a password reset email would be sent.",
        "email": user_row['email'],
        "name": user_row['name']
    }

@app.delete("/api/v1/auth/account")
async def delete_account(authorization: Optional[str] = Header(None)):
    """회원 탈퇴 / Delete account"""
    user = get_user_from_token(authorization)
    email = user['email']

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Delete all tokens for this user
    cursor.execute("DELETE FROM tokens WHERE email = ?", (email,))

    # Delete user account
    cursor.execute("DELETE FROM users WHERE email = ?", (email,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Account deleted successfully / 회원 탈퇴가 완료되었습니다"
    }

@app.post("/api/v1/chat")
async def chat_with_ai(chat_request: ChatMessage):
    """AI chatbot for free conversation about health, food preferences, and body condition"""

    if not openai_client:
        # Fallback: Simple rule-based responses if no API key
        message_lower = chat_request.message.lower()

        # Build dietary summary with detected keywords
        summary_parts = []

        # Detect dietary preferences
        if any(word in message_lower for word in ["저단백", "low protein"]):
            summary_parts.append("low protein")
        if any(word in message_lower for word in ["고단백", "high protein"]):
            summary_parts.append("high protein")
        if any(word in message_lower for word in ["저탄수", "low carb"]):
            summary_parts.append("low carb")
        if any(word in message_lower for word in ["저염", "low sodium"]):
            summary_parts.append("low sodium")

        # Detect symptoms
        if any(word in message_lower for word in ["피곤", "tired", "fatigue"]):
            summary_parts.append("fatigue")
        if any(word in message_lower for word in ["소화", "digestion"]):
            summary_parts.append("digestion")
        if any(word in message_lower for word in ["단백뇨", "신장", "kidney"]):
            summary_parts.append("kidney problems")

        # Detect food ingredient preferences with sentiment
        liked_foods = []
        disliked_foods = []

        # Check for negative expressions (don't want, dislike, exclude)
        has_negative = any(word in message_lower for word in ["싫", "안", "제외", "빼", "don't", "not", "no", "avoid", "dislike", "hate", "없이"])

        # Extract food items and categorize by sentiment
        food_items = {
            "소고기": "beef",
            "beef": "beef",
            "닭": "chicken",
            "닭가슴살": "chicken",
            "chicken": "chicken",
            "치킨": "chicken",
            "돼지": "pork",
            "pork": "pork",
            "연어": "salmon",
            "salmon": "salmon",
            "참치": "tuna",
            "tuna": "tuna",
            "두부": "tofu",
            "tofu": "tofu"
        }

        for keyword, food_name in food_items.items():
            if keyword in message_lower:
                if has_negative:
                    if food_name not in disliked_foods:
                        disliked_foods.append(keyword)
                        summary_parts.append(f"avoid {food_name}")
                else:
                    if food_name not in liked_foods:
                        liked_foods.append(keyword)
                        summary_parts.append(f"wants {food_name}")

        if any(word in message_lower for word in ["매운", "spicy"]):
            summary_parts.append("wants spicy food")

        # Build summary
        dietary_summary = ", ".join(summary_parts) if summary_parts else chat_request.message[:200]

        # Generate response based on sentiment
        response_parts = []
        has_food = len(liked_foods) > 0 or len(disliked_foods) > 0

        if has_food:
            if has_negative:
                response_parts.append("알겠습니다! 그 음식을 제외한 식단을 찾아보겠습니다.")
                response_parts.append("Got it! I'll look for meals without that ingredient.")
            else:
                response_parts.append("좋아요! 그 음식이 포함된 식단을 찾아보겠습니다.")
                response_parts.append("Great! I'll look for meals with that ingredient.")

        if not response_parts:
            response_parts.append("네, 이해했습니다! 말씀하신 내용을 바탕으로 식단을 추천해드리겠습니다. 😊")
            response_parts.append("I understand! I'll recommend meals based on what you've told me.")

        response_text = "\n".join(response_parts)

        # Build preferences object
        preferences = {
            "liked_foods": liked_foods,
            "disliked_foods": disliked_foods,
            "health_notes": "",
            "dietary_summary": dietary_summary
        }

        print(f"\n[FALLBACK MODE PREFERENCES] Extracted from '{chat_request.message}':")
        print(f"  Liked foods: {liked_foods}")
        print(f"  Disliked foods: {disliked_foods}\n")

        return {
            "response": response_text,
            "dietary_summary": dietary_summary,
            "preferences": preferences
        }

    # OpenAI ChatGPT integration
    try:
        # Build conversation with system prompt
        messages = [
            {
                "role": "system",
                "content": """You are a friendly nutritionist assistant for Fitmealor, a meal recommendation service for foreigners in Korea.

Your role:
1. Have natural, friendly conversations about the user's health, body condition, food preferences, and dietary needs
2. Understand what they want to eat (e.g., "I want something spicy", "I need low protein meals")
3. Extract health symptoms (fatigue, digestion issues, kidney problems, etc.)
4. Be conversational and empathetic - not robotic
5. Respond in both English and Korean when appropriate
6. Keep responses concise (2-3 sentences)

Important: You're having a conversation, not filling out a form. Be natural and friendly!"""
            }
        ]

        # Add conversation history
        for msg in chat_request.conversation_history:
            messages.append(msg)

        # Add current message
        messages.append({
            "role": "user",
            "content": chat_request.message
        })

        # Call OpenAI API
        completion = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )

        assistant_response = completion.choices[0].message.content

        # Extract dietary information for meal recommendations
        # Use GPT to extract POSITIVE and NEGATIVE food preferences in JSON format
        preference_completion = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """Extract food preferences from the user's message and return ONLY valid JSON (no markdown, no code blocks).

Return format:
{
  "liked_foods": ["food1", "food2"],
  "disliked_foods": ["food3", "food4"],
  "health_notes": "brief health condition summary",
  "dietary_summary": "brief overall summary"
}

Rules:
- liked_foods: foods user WANTS, likes, craves, is interested in (소고기, beef, 닭고기, chicken, etc.)
- disliked_foods: foods user DISLIKES, wants to avoid, hates, excludes (싫다, 안 먹고 싶다, 제외, don't want, etc.)
- health_notes: any health conditions mentioned (kidney issues, diabetes, high blood pressure, etc.)
- dietary_summary: brief overall summary for recommendations
- Return empty arrays [] if no foods mentioned
- Detect Korean AND English food names"""
                },
                {
                    "role": "user",
                    "content": f"User message: {chat_request.message}\n\nJSON response:"
                }
            ],
            temperature=0.3,
            max_tokens=150
        )

        preference_response = preference_completion.choices[0].message.content.strip()

        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            if preference_response.startswith("```"):
                preference_response = preference_response.split("```")[1]
                if preference_response.startswith("json"):
                    preference_response = preference_response[4:]

            preferences = json.loads(preference_response)
            dietary_summary = preferences.get("dietary_summary", chat_request.message[:200])
            print(f"\n[ChatGPT PREFERENCES] Extracted from '{chat_request.message}':")
            print(f"  Liked foods: {preferences.get('liked_foods', [])}")
            print(f"  Disliked foods: {preferences.get('disliked_foods', [])}")
            print(f"  Health notes: {preferences.get('health_notes', '')}\n")
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            print(f"[ERROR] Failed to parse ChatGPT JSON response: {e}")
            print(f"Raw response: {preference_response}")
            preferences = {
                "liked_foods": [],
                "disliked_foods": [],
                "health_notes": "",
                "dietary_summary": chat_request.message[:200]
            }
            dietary_summary = chat_request.message[:200]

        return {
            "response": assistant_response,
            "dietary_summary": dietary_summary,
            "preferences": preferences
        }

    except Exception as e:
        return {
            "response": f"죄송합니다. 일시적인 오류가 발생했습니다. / Sorry, there was a temporary error: {str(e)}",
            "dietary_summary": chat_request.message[:200],
            "preferences": {}
        }

@app.post("/api/v1/recommendations/recommend")
async def recommend_meals(request: RecommendationRequest):
    # Import TDEE-based recommendation system (fast mathematical algorithm)
    import sys
    sys.path.insert(0, '/Users/goorm/Fitmealor/backend')
    from tdee_recommendation import recommend_meals_by_tdee

    # Get TDEE-based recommendations from database (fast)
    try:
        result = recommend_meals_by_tdee(
            gender=request.gender,
            age=request.age,
            weight_kg=request.weight_kg,
            height_cm=request.height_cm,
            activity_level=request.activity_level,
            health_goal=request.health_goal,
            num_recommendations=50  # Get more to filter by allergies
        )

        tdee_info = result['tdee_info']
        db_recommendations = result['recommendations']

    except Exception as e:
        print(f"Error getting TDEE recommendations: {e}")
        # Fallback to simple calculation
        if request.gender.lower() == 'male':
            bmr = 10 * request.weight_kg + 6.25 * request.height_cm - 5 * request.age + 5
        elif request.gender.lower() == 'female':
            bmr = 10 * request.weight_kg + 6.25 * request.height_cm - 5 * request.age - 161
        else:
            bmr_male = 10 * request.weight_kg + 6.25 * request.height_cm - 5 * request.age + 5
            bmr_female = 10 * request.weight_kg + 6.25 * request.height_cm - 5 * request.age - 161
            bmr = (bmr_male + bmr_female) / 2

        tdee_info = {'bmr': int(bmr), 'tdee': int(bmr * 1.55), 'adjusted_tdee': int(bmr * 1.55)}
        db_recommendations = []

    # Use database recommendations (which are already TDEE-scored)
    all_meals = db_recommendations if db_recommendations else []
    tdee = tdee_info.get('adjusted_tdee', tdee_info.get('tdee', 2000))

    print(f"\n{'='*90}")
    print(f"⚡ TDEE-BASED RECOMMENDATION REQUEST")
    print(f"{'='*90}")
    print(f"User: {request.user_id}")
    print(f"Gender: {request.gender}, Age: {request.age}, Weight: {request.weight_kg}kg, Height: {request.height_cm}cm")
    print(f"Activity Level: {request.activity_level}, Health Goal: {request.health_goal}")
    print(f"BMR: {tdee_info.get('bmr', 0)} kcal")
    print(f"TDEE: {tdee_info.get('tdee', 0)} kcal")
    print(f"Adjusted TDEE: {tdee} kcal (for {request.health_goal})")
    print(f"Total meals from database: {len(all_meals)}")
    print(f"{'='*90}\n")

    # Normalize user allergies to lowercase for comparison
    user_allergies = [a.lower().strip() for a in request.allergies]

    # If we have no allergy filtering needed, return top meals immediately
    if not user_allergies:
        print(f"No allergies specified, returning top {min(20, len(all_meals))} AI-scored meals\n")
        recommendations = all_meals[:20]

        # Add the score for compatibility - use ai_score if available
        for meal in recommendations:
            if 'ai_score' in meal:
                meal['score'] = meal.get('ai_score', 80)
            elif 'tdee_score' not in meal:
                meal['score'] = meal.get('score', 80)

        recommendation_reason = generate_recommendation_reason(
            request.body_condition,
            request.health_goal,
            request.weight_kg,
            request.target_weight_kg,
            tdee,
            len(recommendations)
        )

        return {
            "success": True,
            "user_id": request.user_id,
            "tdee": tdee,
            "tdee_info": tdee_info,
            "user_allergies": request.allergies,
            "total_available": len(all_meals),
            "filtered_out": 0,
            "total_recommendations": len(recommendations),
            "recommendations": recommendations,
            "recommendation_reason": recommendation_reason,
            "message": f"Showing {len(recommendations)} AI-recommended meals"
        }

    # Comprehensive allergen mapping (ingredient -> possible allergens)
    allergen_mapping = {
        "peanuts": ["peanut", "peanuts", "땅콩"],
        "tree nuts": ["nuts", "almond", "walnut", "cashew", "pistachio", "견과류", "아몬드", "호두"],
        "milk": ["milk", "dairy", "cheese", "butter", "cream", "lactose", "우유", "유제품", "치즈"],
        "eggs": ["egg", "eggs", "계란", "달걀"],
        "fish": ["fish", "salmon", "tuna", "cod", "생선", "연어", "참치"],
        "shellfish": ["shellfish", "shrimp", "crab", "lobster", "clam", "갑각류", "새우", "게"],
        "soy": ["soy", "soybean", "tofu", "콩", "대두", "두부"],
        "wheat": ["wheat", "gluten", "flour", "밀", "밀가루", "글루텐"],
        "sesame": ["sesame", "참깨", "깨"],
        "chicken": ["chicken", "닭", "치킨"],
        "beef": ["beef", "소고기"],
        "pork": ["pork", "돼지고기"]
    }

    # Apply allergy filtering to database meals
    print(f"Filtering meals for allergies: {user_allergies}")
    safe_meals_placeholder = [
        {
            "meal_id": "1",
            "name": "CJ 비비고 닭가슴살 스테이크 (오리지널)",
            "name_en": "CJ Bibigo Chicken Breast Steak (Original)",
            "brand": "CJ제일제당",
            "category": "즉석조리식품",
            "ingredients": ["닭가슴살", "브로콜리", "올리브유", "마늘"],
            "allergens": ["chicken"],
            "calories": 120,
            "protein_g": 24,
            "carbs_g": 3,
            "fat_g": 2,
            "sodium_mg": 380,
            "serving_size": "100g",
            "origin": "국내산",
            "explanation_en": f"Premium chicken breast steak with 24g protein per serving. Perfectly grilled and seasoned with garlic and olive oil. Contains only 120 calories with minimal fat (2g) and carbs (3g), making it ideal for {request.health_goal}. The broccoli adds fiber and vitamins. Best heated in microwave for 2 minutes or pan-fried for crispy texture.",
            "explanation_ko": f"1회 제공량당 24g의 단백질을 함유한 프리미엄 닭가슴살 스테이크입니다. 마늘과 올리브유로 완벽하게 구워 간을 맞췄습니다. 120칼로리에 지방(2g)과 탄수화물(3g)이 최소화되어 {request.health_goal}에 이상적입니다. 브로콜리가 식이섬유와 비타민을 더해줍니다. 전자레인지 2분 또는 팬에 구워 바삭한 식감으로 즐기세요.",
            "score": 95
        },
        {
            "meal_id": "2",
            "name": "풀무원 연어 샐러드 (퀴노아 & 채소)",
            "name_en": "Pulmuone Salmon Salad (Quinoa & Vegetables)",
            "brand": "풀무원",
            "category": "신선식품",
            "ingredients": ["연어", "퀴노아", "양상추", "방울토마토", "레몬드레싱"],
            "allergens": ["fish"],
            "calories": 320,
            "protein_g": 22,
            "carbs_g": 28,
            "fat_g": 14,
            "sodium_mg": 450,
            "serving_size": "1팩(250g)",
            "origin": "노르웨이산 연어",
            "explanation_en": "Fresh Norwegian salmon paired with protein-rich quinoa and crisp vegetables. This nutritious salad provides 22g protein and healthy omega-3 fatty acids that support heart health, brain function, and reduce inflammation. The lemon dressing adds a refreshing citrus flavor without excessive calories. Cherry tomatoes provide antioxidants and vitamin C. Perfect for a light yet satisfying meal.",
            "explanation_ko": "신선한 노르웨이산 연어와 단백질이 풍부한 퀴노아, 아삭한 채소를 곁들인 샐러드입니다. 22g의 단백질과 심장 건강, 뇌 기능을 돕고 염증을 줄이는 건강한 오메가-3 지방산을 제공합니다. 레몬 드레싱이 과도한 칼로리 없이 상큼한 감귤 향을 더합니다. 방울토마토는 항산화제와 비타민 C를 제공합니다. 가볍지만 포만감 있는 식사로 완벽합니다.",
            "score": 92
        },
        {
            "meal_id": "3",
            "name": "CJ 비비고 비빔밥 (소고기)",
            "brand": "CJ제일제당",
            "category": "즉석밥/죽",
            "ingredients": ["쌀밥", "시금치", "당근", "계란", "소고기", "참기름", "고추장"],
            "allergens": ["egg", "beef", "sesame", "soy"],
            "calories": 480,
            "protein_g": 18,
            "carbs_g": 75,
            "fat_g": 12,
            "sodium_mg": 890,
            "serving_size": "1개(280g)",
            "origin": "국내산 쌀, 호주산 소고기",
            "explanation_en": "A classic Korean bibimbap featuring premium Australian beef, fresh spinach, carrots, and egg over steamed rice. Mixed with authentic gochujang (Korean chili paste) and sesame oil for rich, savory flavor. This balanced meal provides 18g protein and essential nutrients from various vegetables. At 480 calories, it's a complete meal with good macronutrient balance. Note: Higher in sodium (890mg), so those watching salt intake should consume moderately.",
            "explanation_ko": "프리미엄 호주산 소고기, 신선한 시금치, 당근, 계란을 고슬고슬한 쌀밥 위에 올린 정통 한식 비빔밥입니다. 고추장과 참기름으로 버무려 풍부하고 고소한 맛을 냅니다. 18g의 단백질과 다양한 채소의 필수 영양소를 제공하는 균형 잡힌 식사입니다. 480칼로리로 적절한 다량영양소 균형을 갖춘 완전식입니다. 참고: 나트륨이 높은 편(890mg)이므로 염분 섭취를 주의하시는 분은 적당히 드세요.",
            "score": 88
        },
        {
            "meal_id": "4",
            "name": "풀무원 두부면 (채소 볶음)",
            "brand": "풀무원",
            "category": "두부가공품",
            "ingredients": ["두부면", "양배추", "당근", "파프리카", "간장소스", "생강"],
            "allergens": ["soy", "wheat"],
            "calories": 185,
            "protein_g": 12,
            "carbs_g": 22,
            "fat_g": 6,
            "sodium_mg": 520,
            "serving_size": "1인분(200g)",
            "origin": "국내산 콩",
            "explanation_en": "Innovative tofu noodles stir-fried with colorful vegetables including cabbage, carrots, and bell peppers, flavored with ginger-infused soy sauce. Made from premium Korean soybeans, this plant-based dish provides 12g protein with only 185 calories. The tofu noodles offer a chewy texture similar to regular noodles but with fewer carbs (22g) and more protein. Ideal for vegetarians, vegans, and anyone seeking a lighter noodle alternative. Rich in isoflavones and dietary fiber.",
            "explanation_ko": "양배추, 당근, 파프리카 등 다채로운 채소와 함께 생강이 들어간 간장 소스로 볶은 혁신적인 두부면입니다. 프리미엄 국내산 콩으로 만들어 185칼로리에 12g의 단백질을 제공하는 식물성 요리입니다. 두부면은 일반 면과 비슷한 쫄깃한 식감을 제공하지만 탄수화물(22g)은 더 적고 단백질은 더 많습니다. 채식주의자, 비건, 가벼운 면 대체식품을 찾는 모든 분들에게 이상적입니다. 이소플라본과 식이섬유가 풍부합니다.",
            "score": 85
        },
        {
            "meal_id": "5",
            "name": "오뚜기 참치&야채 덮밥소스",
            "brand": "오뚜기",
            "category": "즉석조리식품",
            "ingredients": ["참치", "양파", "당근", "고구마", "간장소스"],
            "allergens": ["fish", "soy", "wheat"],
            "calories": 380,
            "protein_g": 28,
            "carbs_g": 42,
            "fat_g": 10,
            "sodium_mg": 720,
            "serving_size": "1인분(밥 포함, 300g)",
            "origin": "태국산 참치",
            "explanation_en": f"Savory Thai tuna rice bowl with fresh vegetables including onions, carrots, and sweet potato in a delicious soy-based sauce. This protein-packed meal delivers 28g of lean protein from premium tuna while providing omega-3 fatty acids for heart and brain health. The sweet potato adds complex carbohydrates and beta-carotene. At 380 calories with balanced macros (42g carbs, 10g fat), it's a satisfying complete meal perfect for {request.health_goal}. Ready in just 3 minutes in the microwave.",
            "explanation_ko": f"양파, 당근, 고구마 등 신선한 채소와 함께 맛있는 간장 소스로 만든 풍미 가득한 태국산 참치 덮밥입니다. 프리미엄 참치로 28g의 저지방 단백질을 제공하며 심장과 뇌 건강을 위한 오메가-3 지방산이 풍부합니다. 고구마는 복합 탄수화물과 베타카로틴을 더합니다. 380칼로리에 균형 잡힌 다량영양소(탄수화물 42g, 지방 10g)로 {request.health_goal}에 완벽한 포만감 있는 완전식입니다. 전자레인지에 3분이면 완성됩니다.",
            "score": 90
        },
        {
            "meal_id": "6",
            "name": "풀무원 퀴노아 & 슈퍼곡물 샐러드",
            "brand": "풀무원",
            "category": "신선식품",
            "ingredients": ["퀴노아", "렌틸콩", "아보카도", "방울토마토", "양상추", "레몬드레싱"],
            "allergens": [],
            "calories": 365,
            "protein_g": 14,
            "carbs_g": 48,
            "fat_g": 12,
            "sodium_mg": 380,
            "serving_size": "1팩(230g)",
            "origin": "페루산 퀴노아",
            "explanation_en": f"Nutrient-dense superfood salad combining Peruvian quinoa, protein-rich lentils, creamy avocado, and fresh vegetables with a zesty lemon dressing. This allergen-free bowl provides 14g of complete plant-based protein with all 9 essential amino acids. Quinoa and lentils offer sustained energy, while avocado provides healthy monounsaturated fats and fiber. Cherry tomatoes add vitamin C and antioxidants. At 365 calories with low sodium (380mg), it's perfect for {request.health_goal}. Great for those with multiple food allergies or following a vegan diet.",
            "explanation_ko": f"페루산 퀴노아, 단백질이 풍부한 렌틸콩, 크리미한 아보카도, 신선한 채소를 톡 쏘는 레몬 드레싱과 함께 섞은 영양이 풍부한 슈퍼푸드 샐러드입니다. 알레르기 프리 볼에는 9가지 필수 아미노산을 모두 갖춘 14g의 완전한 식물성 단백질이 들어있습니다. 퀴노아와 렌틸콩은 지속적인 에너지를 제공하고, 아보카도는 건강한 단일불포화지방과 식이섬유를 제공합니다. 방울토마토는 비타민 C와 항산화제를 더합니다. 365칼로리에 낮은 나트륨(380mg)으로 {request.health_goal}에 완벽합니다. 여러 음식 알레르기가 있거나 비건 식단을 따르는 분들에게 훌륭합니다.",
            "score": 87
        },
        {
            "meal_id": "7",
            "name": "CJ 비비고 소불고기 덮밥",
            "brand": "CJ제일제당",
            "category": "즉석밥/죽",
            "ingredients": ["쌀밥", "소고기", "양파", "당근", "참기름", "간장양념"],
            "allergens": ["beef", "sesame", "soy", "wheat"],
            "calories": 520,
            "protein_g": 26,
            "carbs_g": 68,
            "fat_g": 15,
            "sodium_mg": 950,
            "serving_size": "1개(320g)",
            "origin": "호주산 소고기, 국내산 쌀",
            "explanation_en": f"Authentic Korean bulgogi rice bowl featuring tender marinated Australian beef cooked with sweet onions and carrots in traditional soy-based sauce, finished with fragrant sesame oil. This hearty meal provides 26g protein for muscle support and 520 calories for sustained energy. The sweet and savory flavors of bulgogi make it a Korean comfort food favorite. Perfect for {request.health_goal}, though note the higher sodium content (950mg). Best enjoyed heated thoroughly and mixed well before eating.",
            "explanation_ko": f"달콤한 양파와 당근과 함께 전통 간장 양념으로 조리한 부드러운 호주산 소고기를 고슬고슬한 쌀밥 위에 올리고 고소한 참기름으로 마무리한 정통 한식 불고기 덮밥입니다. 근육 지원을 위한 26g의 단백질과 지속적인 에너지를 위한 520칼로리를 제공하는 든든한 한 끼입니다. 불고기의 달콤하고 짭짤한 맛은 한국인들이 사랑하는 대표 음식입니다. {request.health_goal}에 완벽하지만, 나트륨 함량이 높은 편(950mg)이니 참고하세요. 충분히 데운 후 잘 비벼 드시면 가장 맛있습니다.",
            "score": 88
        },
        {
            "meal_id": "8",
            "name": "풀무원 그릭요거트 베리믹스",
            "brand": "풀무원",
            "category": "유제품",
            "ingredients": ["그릭요거트", "블루베리", "딸기", "아몬드", "꿀"],
            "allergens": ["milk", "tree nuts"],
            "calories": 265,
            "protein_g": 18,
            "carbs_g": 26,
            "fat_g": 9,
            "sodium_mg": 95,
            "serving_size": "1컵(170g)",
            "origin": "국내산 우유",
            "explanation_en": f"Creamy Greek yogurt topped with antioxidant-rich mixed berries (blueberries and strawberries), crunchy almonds, and a drizzle of natural honey. This protein-packed breakfast provides 18g protein with live probiotic cultures that support digestive health and immune function. The berries offer powerful antioxidants and vitamins, while almonds add healthy fats and vitamin E. At just 265 calories with very low sodium (95mg), it's an excellent choice for {request.health_goal}. Perfect as a nutritious breakfast or post-workout snack.",
            "explanation_ko": f"항산화제가 풍부한 믹스 베리(블루베리와 딸기), 바삭한 아몬드를 올리고 천연 꿀을 살짝 뿌린 크리미한 그릭 요거트입니다. 소화 건강과 면역 기능을 돕는 살아있는 프로바이오틱스 균주와 함께 18g의 단백질을 제공하는 단백질 가득한 아침식사입니다. 베리는 강력한 항산화제와 비타민을 제공하고, 아몬드는 건강한 지방과 비타민 E를 더합니다. 265칼로리에 매우 낮은 나트륨(95mg)으로 {request.health_goal}에 탁월한 선택입니다. 영양가 높은 아침식사나 운동 후 간식으로 완벽합니다.",
            "score": 84
        },
        {
            "meal_id": "9",
            "name": "오뚜기 렌틸콩 수프 & 통곡물빵 세트",
            "brand": "오뚜기",
            "category": "즉석식품",
            "ingredients": ["렌틸콩", "당근", "양파", "셀러리", "통곡물빵", "올리브유"],
            "allergens": ["wheat"],
            "calories": 345,
            "protein_g": 15,
            "carbs_g": 52,
            "fat_g": 7,
            "sodium_mg": 680,
            "serving_size": "1세트(수프 250ml + 빵 2조각)",
            "origin": "캐나다산 렌틸콩",
            "explanation_en": f"Hearty Canadian lentil soup loaded with carrots, onions, and celery in a savory broth, served with 2 slices of wholesome whole grain bread drizzled with olive oil. This fiber powerhouse provides 15g plant-based protein and over 12g of dietary fiber for excellent digestive health and sustained fullness. Lentils are rich in iron, folate, and complex carbohydrates. At 345 calories with balanced macros, it's a comforting meal perfect for {request.health_goal}. The whole grain bread adds B vitamins and additional fiber. Heat soup thoroughly and enjoy with warm bread for dipping.",
            "explanation_ko": f"당근, 양파, 셀러리가 가득 들어간 풍미 깊은 육수의 캐나다산 렌틸콩 수프와 올리브유를 뿌린 건강한 통곡물빵 2조각이 함께 제공됩니다. 이 식이섬유 강자는 15g의 식물성 단백질과 12g 이상의 식이섬유를 제공하여 훌륭한 소화 건강과 지속적인 포만감을 선사합니다. 렌틸콩은 철분, 엽산, 복합 탄수화물이 풍부합니다. 345칼로리에 균형 잡힌 다량영양소로 {request.health_goal}에 완벽한 든든한 한 끼입니다. 통곡물빵은 비타민 B와 추가 식이섬유를 제공합니다. 수프를 충분히 데워 따뜻한 빵을 찍어 드세요.",
            "score": 86
        },
        {
            "meal_id": "10",
            "name": "하림 IFF 닭가슴살 현미밥 도시락",
            "brand": "하림",
            "category": "도시락/간편식",
            "ingredients": ["닭가슴살", "현미밥", "브로콜리", "단호박", "허브"],
            "allergens": ["chicken"],
            "calories": 395,
            "protein_g": 32,
            "carbs_g": 45,
            "fat_g": 6,
            "sodium_mg": 580,
            "serving_size": "1개(280g)",
            "origin": "국내산 닭고기, 국내산 현미",
            "explanation_en": f"Complete ready-to-eat meal box featuring herb-seasoned Korean chicken breast with nutty brown rice, vitamin-rich broccoli, and sweet kabocha pumpkin. This fitness-focused lunch delivers an impressive 32g of lean protein with only 6g fat, making it ideal for muscle building and weight management. Brown rice provides complex carbohydrates and fiber for sustained energy. At 395 calories with moderate sodium (580mg), it's a perfectly balanced meal for {request.health_goal}. Microwave for 2-3 minutes and enjoy a restaurant-quality healthy meal.",
            "explanation_ko": f"허브로 간을 한 국내산 닭가슴살과 고소한 현미밥, 비타민이 풍부한 브로콜리, 달콤한 단호박이 담긴 완벽한 도시락입니다. 피트니스에 초점을 맞춘 이 점심 도시락은 지방이 6g에 불과하면서 무려 32g의 저지방 단백질을 제공하여 근육 생성과 체중 관리에 이상적입니다. 현미는 지속적인 에너지를 위한 복합 탄수화물과 식이섬유를 제공합니다. 395칼로리에 적당한 나트륨(580mg)으로 {request.health_goal}에 완벽하게 균형 잡힌 식사입니다. 전자레인지에 2-3분 데우면 레스토랑 수준의 건강한 식사를 즐길 수 있습니다.",
            "score": 91
        },
        {
            "meal_id": "11",
            "name": "풀무원 두부면 비빔국수",
            "brand": "풀무원",
            "category": "면류",
            "ingredients": ["두부면", "고추장", "참깨", "오이", "당근"],
            "allergens": ["soy", "sesame"],
            "calories": 285,
            "protein_g": 12,
            "carbs_g": 38,
            "fat_g": 8,
            "sodium_mg": 620,
            "serving_size": "1인분(320g)",
            "origin": "국내산 콩",
            "explanation_en": f"Low-calorie tofu noodles. High in plant protein, suitable for {request.health_goal}.",
            "explanation_ko": f"저칼로리 두부면. 식물성 단백질 풍부, {request.health_goal}에 적합합니다.",
            "score": 82
        },
        {
            "meal_id": "12",
            "name": "오뚜기 맛있는 오트밀",
            "brand": "오뚜기",
            "category": "시리얼/곡물",
            "ingredients": ["귀리", "건포도", "호두", "아몬드"],
            "allergens": ["tree nuts"],
            "calories": 310,
            "protein_g": 10,
            "carbs_g": 55,
            "fat_g": 6,
            "sodium_mg": 120,
            "serving_size": "1컵(80g)",
            "origin": "호주산 귀리",
            "explanation_en": f"Whole grain oatmeal with nuts. High fiber for {request.health_goal}.",
            "explanation_ko": f"통곡물 오트밀. 식이섬유 풍부, {request.health_goal}에 도움됩니다.",
            "score": 88
        },
        {
            "meal_id": "13",
            "name": "동원 라이트 스탠다드 참치",
            "brand": "동원",
            "category": "통조림",
            "ingredients": ["참치", "물", "소금"],
            "allergens": ["fish"],
            "calories": 110,
            "protein_g": 26,
            "carbs_g": 0,
            "fat_g": 1,
            "sodium_mg": 340,
            "serving_size": "1캔(100g)",
            "origin": "원양산 참치",
            "explanation_en": f"Ultra-high protein, zero carbs. Perfect for {request.health_goal}.",
            "explanation_ko": f"초고단백, 무탄수화물. {request.health_goal}에 완벽합니다.",
            "score": 94
        },
        {
            "meal_id": "14",
            "name": "CJ 햇반 흑미밥",
            "brand": "CJ제일제당",
            "category": "즉석밥",
            "ingredients": ["흑미", "백미", "물"],
            "allergens": [],
            "calories": 310,
            "protein_g": 6,
            "carbs_g": 68,
            "fat_g": 1,
            "sodium_mg": 0,
            "serving_size": "1개(210g)",
            "origin": "국내산 쌀",
            "explanation_en": f"Black rice with nutrients. Complex carbs for {request.health_goal}.",
            "explanation_ko": f"영양소 풍부한 흑미밥. 복합 탄수화물, {request.health_goal}에 좋습니다.",
            "score": 85
        },
        {
            "meal_id": "15",
            "name": "풀무원 그린주스 케일",
            "brand": "풀무원",
            "category": "음료",
            "ingredients": ["케일", "사과", "바나나", "레몬"],
            "allergens": [],
            "calories": 95,
            "protein_g": 2,
            "carbs_g": 22,
            "fat_g": 0,
            "sodium_mg": 45,
            "serving_size": "1병(330ml)",
            "origin": "국내산 케일",
            "explanation_en": f"Nutrient-dense green juice. Low calorie for {request.health_goal}.",
            "explanation_ko": f"영양 가득 그린주스. 저칼로리, {request.health_goal}을 지원합니다.",
            "score": 79
        },
        {
            "meal_id": "16",
            "name": "롯데푸드 아몬드 브리즈",
            "brand": "롯데푸드",
            "category": "음료",
            "ingredients": ["아몬드", "물", "칼슘"],
            "allergens": ["tree nuts"],
            "calories": 40,
            "protein_g": 1,
            "carbs_g": 2,
            "fat_g": 3,
            "sodium_mg": 170,
            "serving_size": "1팩(190ml)",
            "origin": "미국산 아몬드",
            "explanation_en": f"Low-calorie almond milk. Dairy-free for {request.health_goal}.",
            "explanation_ko": f"저칼로리 아몬드 우유. 유제품 무첨가, {request.health_goal}에 적합합니다.",
            "score": 77
        },
        {
            "meal_id": "17",
            "name": "신송식품 닭가슴살 소세지 (오리지널)",
            "brand": "신송식품",
            "category": "육가공품",
            "ingredients": ["닭가슴살", "양파", "마늘", "후추"],
            "allergens": ["chicken"],
            "calories": 55,
            "protein_g": 11,
            "carbs_g": 2,
            "fat_g": 0.5,
            "sodium_mg": 280,
            "serving_size": "1개(60g)",
            "origin": "국내산 닭고기",
            "explanation_en": f"High protein, low fat sausage. Convenient for {request.health_goal}.",
            "explanation_ko": f"고단백 저지방 소세지. {request.health_goal}에 편리합니다.",
            "score": 89
        },
        {
            "meal_id": "18",
            "name": "풀무원 단호박 샐러드",
            "brand": "풀무원",
            "category": "샐러드",
            "ingredients": ["단호박", "양배추", "케일", "견과류", "발사믹 드레싱"],
            "allergens": ["tree nuts"],
            "calories": 220,
            "protein_g": 6,
            "carbs_g": 35,
            "fat_g": 7,
            "sodium_mg": 380,
            "serving_size": "1팩(250g)",
            "origin": "국내산 단호박",
            "explanation_en": f"Fiber-rich pumpkin salad. Nutrient-packed for {request.health_goal}.",
            "explanation_ko": f"식이섬유 풍부한 단호박 샐러드. 영양 가득, {request.health_goal}에 좋습니다.",
            "score": 84
        },
        {
            "meal_id": "19",
            "name": "CJ 비비고 왕교자 (야채)",
            "brand": "CJ제일제당",
            "category": "만두",
            "ingredients": ["배추", "부추", "두부", "만두피"],
            "allergens": ["soy", "wheat"],
            "calories": 240,
            "protein_g": 8,
            "carbs_g": 40,
            "fat_g": 5,
            "sodium_mg": 580,
            "serving_size": "6개(180g)",
            "origin": "국내산 야채",
            "explanation_en": f"Vegetable dumplings. Moderate calories for {request.health_goal}.",
            "explanation_ko": f"야채 만두. 적당한 칼로리, {request.health_goal}에 무난합니다.",
            "score": 78
        },
        {
            "meal_id": "20",
            "name": "청정원 우리쌀 현미 비빔밥",
            "brand": "청정원",
            "category": "즉석식품",
            "ingredients": ["현미", "시금치", "당근", "고추장", "참기름"],
            "allergens": ["sesame"],
            "calories": 380,
            "protein_g": 9,
            "carbs_g": 72,
            "fat_g": 5,
            "sodium_mg": 750,
            "serving_size": "1개(300g)",
            "origin": "국내산 현미",
            "explanation_en": f"Brown rice bibimbap. Whole grain for {request.health_goal}.",
            "explanation_ko": f"현미 비빔밥. 통곡물, {request.health_goal}에 도움됩니다.",
            "score": 80
        },
        {
            "meal_id": "21",
            "name": "하림 더미식 닭가슴살 큐브 (매운맛)",
            "brand": "하림",
            "category": "즉석조리식품",
            "ingredients": ["닭가슴살", "고추", "마늘", "간장"],
            "allergens": ["chicken", "soy"],
            "calories": 135,
            "protein_g": 25,
            "carbs_g": 5,
            "fat_g": 2,
            "sodium_mg": 420,
            "serving_size": "1팩(100g)",
            "origin": "국내산 닭고기",
            "explanation_en": f"Spicy chicken cubes. High protein, low fat for {request.health_goal}.",
            "explanation_ko": f"매운 닭가슴살 큐브. 고단백 저지방, {request.health_goal}에 최적입니다.",
            "score": 92
        },
        {
            "meal_id": "22",
            "name": "동원 덴마크 연어 스테이크",
            "brand": "동원",
            "category": "냉동식품",
            "ingredients": ["연어", "레몬", "허브"],
            "allergens": ["fish"],
            "calories": 210,
            "protein_g": 28,
            "carbs_g": 0,
            "fat_g": 11,
            "sodium_mg": 95,
            "serving_size": "1조각(120g)",
            "origin": "덴마크산 연어",
            "explanation_en": f"Omega-3 rich salmon. High protein for {request.health_goal}.",
            "explanation_ko": f"오메가3 풍부한 연어. 고단백, {request.health_goal}에 탁월합니다.",
            "score": 93
        },
        {
            "meal_id": "23",
            "name": "곰곰 그릭 요거트 플레인",
            "brand": "곰곰",
            "category": "유제품",
            "ingredients": ["우유", "유산균"],
            "allergens": ["milk"],
            "calories": 100,
            "protein_g": 10,
            "carbs_g": 5,
            "fat_g": 4,
            "sodium_mg": 55,
            "serving_size": "1컵(150g)",
            "origin": "국내산 우유",
            "explanation_en": f"Greek yogurt with probiotics. High protein for {request.health_goal}.",
            "explanation_ko": f"프로바이오틱스 그릭 요거트. 고단백, {request.health_goal}에 좋습니다.",
            "score": 87
        },
        {
            "meal_id": "24",
            "name": "얇은피 꽉찬속 김치만두",
            "brand": "CJ제일제당",
            "category": "만두",
            "ingredients": ["김치", "돼지고기", "두부", "만두피"],
            "allergens": ["pork", "soy", "wheat"],
            "calories": 280,
            "protein_g": 12,
            "carbs_g": 38,
            "fat_g": 9,
            "sodium_mg": 680,
            "serving_size": "7개(210g)",
            "origin": "국내산 돼지고기",
            "explanation_en": f"Kimchi dumplings. Traditional Korean flavor for {request.health_goal}.",
            "explanation_ko": f"김치 만두. 전통 한국 맛, {request.health_goal}에 무난합니다.",
            "score": 76
        },
        {
            "meal_id": "25",
            "name": "오리온 닥터유 그래놀라",
            "brand": "오리온",
            "category": "시리얼/곡물",
            "ingredients": ["귀리", "아몬드", "크랜베리", "꿀"],
            "allergens": ["tree nuts"],
            "calories": 220,
            "protein_g": 6,
            "carbs_g": 38,
            "fat_g": 6,
            "sodium_mg": 85,
            "serving_size": "1회분(50g)",
            "origin": "호주산 귀리",
            "explanation_en": f"Crunchy granola. High fiber for {request.health_goal}.",
            "explanation_ko": f"바삭한 그래놀라. 식이섬유 풍부, {request.health_goal}에 도움됩니다.",
            "score": 81
        },
        {
            "meal_id": "26",
            "name": "풀무원 생나또",
            "brand": "풀무원",
            "category": "발효식품",
            "ingredients": ["대두", "나또균"],
            "allergens": ["soy"],
            "calories": 85,
            "protein_g": 8,
            "carbs_g": 6,
            "fat_g": 4,
            "sodium_mg": 5,
            "serving_size": "1팩(40g)",
            "origin": "캐나다산 콩",
            "explanation_en": f"Fermented soybeans. Probiotics and protein for {request.health_goal}.",
            "explanation_ko": f"발효 콩. 프로바이오틱스와 단백질, {request.health_goal}에 좋습니다.",
            "score": 86
        },
        {
            "meal_id": "27",
            "name": "삼양 불닭볶음면 (덜매운맛)",
            "brand": "삼양식품",
            "category": "면류",
            "ingredients": ["면", "고추", "설탕", "간장"],
            "allergens": ["wheat", "soy"],
            "calories": 470,
            "protein_g": 10,
            "carbs_g": 78,
            "fat_g": 13,
            "sodium_mg": 1820,
            "serving_size": "1봉지(140g)",
            "origin": "국내산",
            "explanation_en": f"Spicy noodles (use sparingly). High sodium, not ideal for {request.health_goal}.",
            "explanation_ko": f"매운 라면 (적당히). 높은 나트륨, {request.health_goal}에 비추천.",
            "score": 55
        },
        {
            "meal_id": "28",
            "name": "농심 신라면 건면",
            "brand": "농심",
            "category": "면류",
            "ingredients": ["면", "채소분말", "고춧가루"],
            "allergens": ["wheat"],
            "calories": 410,
            "protein_g": 11,
            "carbs_g": 82,
            "fat_g": 2,
            "sodium_mg": 1650,
            "serving_size": "1봉지(120g)",
            "origin": "국내산",
            "explanation_en": f"Dried noodles. High sodium, occasional treat for {request.health_goal}.",
            "explanation_ko": f"건면. 높은 나트륨, {request.health_goal}에 가끔만.",
            "score": 58
        },
        {
            "meal_id": "29",
            "name": "빙그레 떠먹는 불가리스",
            "brand": "빙그레",
            "category": "유제품",
            "ingredients": ["우유", "설탕", "유산균"],
            "allergens": ["milk"],
            "calories": 105,
            "protein_g": 4,
            "carbs_g": 18,
            "fat_g": 2,
            "sodium_mg": 50,
            "serving_size": "1개(65g)",
            "origin": "국내산 우유",
            "explanation_en": f"Bulgarian yogurt. Probiotics for {request.health_goal}.",
            "explanation_ko": f"불가리스 요거트. 유산균, {request.health_goal}에 도움됩니다.",
            "score": 74
        },
        {
            "meal_id": "30",
            "name": "풀무원 탱탱쫄면",
            "brand": "풀무원",
            "category": "면류",
            "ingredients": ["쫄면", "양배추", "당근", "고추장", "참깨"],
            "allergens": ["wheat", "sesame"],
            "calories": 320,
            "protein_g": 9,
            "carbs_g": 58,
            "fat_g": 6,
            "sodium_mg": 920,
            "serving_size": "1인분(350g)",
            "origin": "국내산",
            "explanation_en": f"Chewy noodles with vegetables. Moderate for {request.health_goal}.",
            "explanation_ko": f"야채 쫄면. 적당함, {request.health_goal}에 무난합니다.",
            "score": 72
        },
        {
            "meal_id": "31",
            "name": "종가집 포기김치",
            "brand": "대상",
            "category": "김치",
            "ingredients": ["배추", "고춧가루", "마늘", "생강", "멸치액젓"],
            "allergens": ["fish"],
            "calories": 18,
            "protein_g": 1,
            "carbs_g": 3,
            "fat_g": 0,
            "sodium_mg": 450,
            "serving_size": "1인분(50g)",
            "origin": "국내산 배추",
            "explanation_en": f"Traditional kimchi. Low calorie, probiotics for {request.health_goal}.",
            "explanation_ko": f"전통 김치. 저칼로리, 유산균 풍부, {request.health_goal}에 좋습니다.",
            "score": 83
        },
        {
            "meal_id": "32",
            "name": "CJ 비비고 소고기 미역국",
            "brand": "CJ제일제당",
            "category": "국/탕",
            "ingredients": ["소고기", "미역", "참기름", "마늘"],
            "allergens": ["beef", "sesame"],
            "calories": 95,
            "protein_g": 8,
            "carbs_g": 6,
            "fat_g": 4,
            "sodium_mg": 680,
            "serving_size": "1팩(500ml)",
            "origin": "국내산 소고기",
            "explanation_en": f"Beef seaweed soup. Iron-rich for {request.health_goal}.",
            "explanation_ko": f"소고기 미역국. 철분 풍부, {request.health_goal}에 좋습니다.",
            "score": 79
        },
        {
            "meal_id": "33",
            "name": "동원 리챔",
            "brand": "동원",
            "category": "통조림",
            "ingredients": ["돼지고기", "전분", "식염"],
            "allergens": ["pork"],
            "calories": 290,
            "protein_g": 13,
            "carbs_g": 4,
            "fat_g": 25,
            "sodium_mg": 880,
            "serving_size": "1캔(200g)",
            "origin": "수입산 돼지고기",
            "explanation_en": f"Canned ham. High fat and sodium, not ideal for {request.health_goal}.",
            "explanation_ko": f"통조림 햄. 높은 지방과 나트륨, {request.health_goal}에 비추천.",
            "score": 62
        },
        {
            "meal_id": "34",
            "name": "SPC 삼립 호밀빵",
            "brand": "SPC삼립",
            "category": "빵",
            "ingredients": ["호밀가루", "밀가루", "효모", "소금"],
            "allergens": ["wheat"],
            "calories": 240,
            "protein_g": 8,
            "carbs_g": 48,
            "fat_g": 2,
            "sodium_mg": 380,
            "serving_size": "3조각(90g)",
            "origin": "국내산",
            "explanation_en": f"Rye bread. Whole grain for {request.health_goal}.",
            "explanation_ko": f"호밀빵. 통곡물, {request.health_goal}에 좋습니다.",
            "score": 82
        },
        {
            "meal_id": "35",
            "name": "롯데 마이 쉐이크 초코맛",
            "brand": "롯데푸드",
            "category": "음료",
            "ingredients": ["우유", "코코아", "설탕"],
            "allergens": ["milk"],
            "calories": 180,
            "protein_g": 7,
            "carbs_g": 30,
            "fat_g": 4,
            "sodium_mg": 120,
            "serving_size": "1병(240ml)",
            "origin": "국내산 우유",
            "explanation_en": f"Chocolate shake. High sugar, treat for {request.health_goal}.",
            "explanation_ko": f"초코 쉐이크. 높은 당분, {request.health_goal}에 가끔만.",
            "score": 68
        },
        {
            "meal_id": "36",
            "name": "오뚜기 카레라이스 (순한맛)",
            "brand": "오뚜기",
            "category": "즉석식품",
            "ingredients": ["쌀", "감자", "당근", "카레분말"],
            "allergens": ["wheat"],
            "calories": 420,
            "protein_g": 9,
            "carbs_g": 78,
            "fat_g": 8,
            "sodium_mg": 850,
            "serving_size": "1팩(280g)",
            "origin": "국내산 쌀",
            "explanation_en": f"Curry rice. Moderate calories for {request.health_goal}.",
            "explanation_ko": f"카레라이스. 적당한 칼로리, {request.health_goal}에 무난합니다.",
            "score": 73
        },
        {
            "meal_id": "37",
            "name": "풀무원 ABC주스",
            "brand": "풀무원",
            "category": "음료",
            "ingredients": ["사과", "비트", "당근"],
            "allergens": [],
            "calories": 110,
            "protein_g": 2,
            "carbs_g": 26,
            "fat_g": 0,
            "sodium_mg": 60,
            "serving_size": "1병(330ml)",
            "origin": "국내산",
            "explanation_en": f"ABC juice (Apple-Beet-Carrot). Nutrient-rich for {request.health_goal}.",
            "explanation_ko": f"ABC주스 (사과-비트-당근). 영양 풍부, {request.health_goal}에 좋습니다.",
            "score": 80
        },
        {
            "meal_id": "38",
            "name": "매일유업 상하목장 우유",
            "brand": "매일유업",
            "category": "유제품",
            "ingredients": ["원유"],
            "allergens": ["milk"],
            "calories": 130,
            "protein_g": 6,
            "carbs_g": 10,
            "fat_g": 8,
            "sodium_mg": 100,
            "serving_size": "1팩(200ml)",
            "origin": "국내산 원유",
            "explanation_en": f"Fresh milk. Calcium and protein for {request.health_goal}.",
            "explanation_ko": f"신선한 우유. 칼슘과 단백질, {request.health_goal}에 좋습니다.",
            "score": 77
        },
        {
            "meal_id": "39",
            "name": "농심 새우깡",
            "brand": "농심",
            "category": "스낵",
            "ingredients": ["새우", "밀가루", "감자전분", "식용유"],
            "allergens": ["shellfish", "wheat"],
            "calories": 230,
            "protein_g": 3,
            "carbs_g": 31,
            "fat_g": 11,
            "sodium_mg": 380,
            "serving_size": "1봉지(90g)",
            "origin": "국내산",
            "explanation_en": f"Shrimp crackers. Snack food, not ideal for {request.health_goal}.",
            "explanation_ko": f"새우깡 스낵. {request.health_goal}에 적합하지 않음.",
            "score": 50
        },
        {
            "meal_id": "40",
            "name": "서울우유 플레인 요거트",
            "brand": "서울우유",
            "category": "유제품",
            "ingredients": ["우유", "유산균"],
            "allergens": ["milk"],
            "calories": 70,
            "protein_g": 4,
            "carbs_g": 8,
            "fat_g": 2,
            "sodium_mg": 50,
            "serving_size": "1개(80g)",
            "origin": "국내산 우유",
            "explanation_en": f"Plain yogurt. Low calorie, probiotics for {request.health_goal}.",
            "explanation_ko": f"플레인 요거트. 저칼로리, 유산균, {request.health_goal}에 좋습니다.",
            "score": 85
        },
        {
            "meal_id": "41",
            "name": "농심 소고기 미역국",
            "brand": "농심",
            "category": "즉석국",
            "ingredients": ['소고기', '미역', '다시마', '마늘'],
            "allergens": ['beef', 'soy'],
            "calories": 180,
            "protein_g": 12,
            "carbs_g": 18,
            "fat_g": 6,
            "sodium_mg": 890,
            "serving_size": "1봉(500ml)",
            "origin": "국내산 미역",
            "explanation_en": f"농심 소고기 미역국. 즉석국. Good for {request.health_goal}.",
            "explanation_ko": f"농심 소고기 미역국. 즉석국. {request.health_goal}에 좋습니다.",
            "score": 78
        },
        {
            "meal_id": "42",
            "name": "CJ 고메 안심 스테이크",
            "brand": "CJ제일제당",
            "category": "냉동육류",
            "ingredients": ['소고기안심', '올리브유', '로즈마리', '마늘'],
            "allergens": ['beef'],
            "calories": 280,
            "protein_g": 32,
            "carbs_g": 2,
            "fat_g": 16,
            "sodium_mg": 420,
            "serving_size": "150g",
            "origin": "호주산",
            "explanation_en": f"CJ 고메 안심 스테이크. 냉동육류. Good for {request.health_goal}.",
            "explanation_ko": f"CJ 고메 안심 스테이크. 냉동육류. {request.health_goal}에 좋습니다.",
            "score": 88
        },
        {
            "meal_id": "43",
            "name": "동원 돼지고기 두루치기",
            "brand": "동원F&B",
            "category": "즉석조리",
            "ingredients": ['돼지고기', '양파', '고추장', '마늘'],
            "allergens": ['pork', 'soy'],
            "calories": 320,
            "protein_g": 22,
            "carbs_g": 15,
            "fat_g": 18,
            "sodium_mg": 950,
            "serving_size": "200g",
            "origin": "국내산 돼지고기",
            "explanation_en": f"동원 돼지고기 두루치기. 즉석조리. Good for {request.health_goal}.",
            "explanation_ko": f"동원 돼지고기 두루치기. 즉석조리. {request.health_goal}에 좋습니다.",
            "score": 75
        },
        {
            "meal_id": "44",
            "name": "풀무원 삼계탕",
            "brand": "풀무원",
            "category": "즉석국",
            "ingredients": ['닭고기', '인삼', '대추', '마늘', '찹쌀'],
            "allergens": ['chicken'],
            "calories": 380,
            "protein_g": 28,
            "carbs_g": 25,
            "fat_g": 16,
            "sodium_mg": 780,
            "serving_size": "800g",
            "origin": "국내산 닭고기",
            "explanation_en": f"풀무원 삼계탕. 즉석국. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 삼계탕. 즉석국. {request.health_goal}에 좋습니다.",
            "score": 82
        },
        {
            "meal_id": "45",
            "name": "동원 화이트 참치살코기",
            "brand": "동원F&B",
            "category": "통조림",
            "ingredients": ['참치', '정제수', '소금'],
            "allergens": ['fish'],
            "calories": 110,
            "protein_g": 26,
            "carbs_g": 0,
            "fat_g": 1,
            "sodium_mg": 320,
            "serving_size": "100g",
            "origin": "태국산",
            "explanation_en": f"동원 화이트 참치살코기. 통조림. Good for {request.health_goal}.",
            "explanation_ko": f"동원 화이트 참치살코기. 통조림. {request.health_goal}에 좋습니다.",
            "score": 92
        },
        {
            "meal_id": "46",
            "name": "사조 살코기 고등어",
            "brand": "사조대림",
            "category": "통조림",
            "ingredients": ['고등어', '정제수'],
            "allergens": ['fish'],
            "calories": 190,
            "protein_g": 22,
            "carbs_g": 0,
            "fat_g": 12,
            "sodium_mg": 280,
            "serving_size": "120g",
            "origin": "노르웨이산",
            "explanation_en": f"사조 살코기 고등어. 통조림. Good for {request.health_goal}.",
            "explanation_ko": f"사조 살코기 고등어. 통조림. {request.health_goal}에 좋습니다.",
            "score": 86
        },
        {
            "meal_id": "47",
            "name": "CJ 비비고 LA 갈비",
            "brand": "CJ제일제당",
            "category": "냉동육류",
            "ingredients": ['소갈비', '간장', '배', '마늘', '설탕'],
            "allergens": ['beef', 'soy'],
            "calories": 420,
            "protein_g": 26,
            "carbs_g": 18,
            "fat_g": 28,
            "sodium_mg": 980,
            "serving_size": "200g",
            "origin": "미국산",
            "explanation_en": f"CJ 비비고 LA 갈비. 냉동육류. Good for {request.health_goal}.",
            "explanation_ko": f"CJ 비비고 LA 갈비. 냉동육류. {request.health_goal}에 좋습니다.",
            "score": 70
        },
        {
            "meal_id": "48",
            "name": "하림 닭가슴살 소시지",
            "brand": "하림",
            "category": "육가공",
            "ingredients": ['닭가슴살', '치즈', '양파'],
            "allergens": ['chicken', 'milk'],
            "calories": 140,
            "protein_g": 18,
            "carbs_g": 6,
            "fat_g": 4,
            "sodium_mg": 480,
            "serving_size": "80g",
            "origin": "국내산 닭고기",
            "explanation_en": f"하림 닭가슴살 소시지. 육가공. Good for {request.health_goal}.",
            "explanation_ko": f"하림 닭가슴살 소시지. 육가공. {request.health_goal}에 좋습니다.",
            "score": 83
        },
        {
            "meal_id": "49",
            "name": "동원 연어 스테이크",
            "brand": "동원F&B",
            "category": "냉동수산",
            "ingredients": ['연어', '레몬', '딜'],
            "allergens": ['fish'],
            "calories": 240,
            "protein_g": 28,
            "carbs_g": 0,
            "fat_g": 14,
            "sodium_mg": 220,
            "serving_size": "120g",
            "origin": "노르웨이산",
            "explanation_en": f"동원 연어 스테이크. 냉동수산. Good for {request.health_goal}.",
            "explanation_ko": f"동원 연어 스테이크. 냉동수산. {request.health_goal}에 좋습니다.",
            "score": 90
        },
        {
            "meal_id": "50",
            "name": "풀무원 탄탄 두부",
            "brand": "풀무원",
            "category": "두부",
            "ingredients": ['대두', '간수'],
            "allergens": ['soy'],
            "calories": 90,
            "protein_g": 10,
            "carbs_g": 3,
            "fat_g": 5,
            "sodium_mg": 15,
            "serving_size": "150g",
            "origin": "국내산 콩",
            "explanation_en": f"풀무원 탄탄 두부. 두부. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 탄탄 두부. 두부. {request.health_goal}에 좋습니다.",
            "score": 88
        },
        {
            "meal_id": "51",
            "name": "CJ 햇반 현미밥",
            "brand": "CJ제일제당",
            "category": "즉석밥",
            "ingredients": ['현미', '물'],
            "allergens": [],
            "calories": 310,
            "protein_g": 7,
            "carbs_g": 68,
            "fat_g": 2,
            "sodium_mg": 5,
            "serving_size": "210g",
            "origin": "국내산 쌀",
            "explanation_en": f"CJ 햇반 현미밥. 즉석밥. Good for {request.health_goal}.",
            "explanation_ko": f"CJ 햇반 현미밥. 즉석밥. {request.health_goal}에 좋습니다.",
            "score": 85
        },
        {
            "meal_id": "52",
            "name": "풀무원 귀리밥",
            "brand": "풀무원",
            "category": "즉석밥",
            "ingredients": ['귀리', '쌀', '보리'],
            "allergens": ['wheat'],
            "calories": 280,
            "protein_g": 9,
            "carbs_g": 58,
            "fat_g": 3,
            "sodium_mg": 8,
            "serving_size": "210g",
            "origin": "국내산",
            "explanation_en": f"풀무원 귀리밥. 즉석밥. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 귀리밥. 즉석밥. {request.health_goal}에 좋습니다.",
            "score": 87
        },
        {
            "meal_id": "53",
            "name": "오뚜기 잡곡밥",
            "brand": "오뚜기",
            "category": "즉석밥",
            "ingredients": ['현미', '귀리', '보리', '렌틸콩'],
            "allergens": ['wheat'],
            "calories": 290,
            "protein_g": 8,
            "carbs_g": 62,
            "fat_g": 2,
            "sodium_mg": 10,
            "serving_size": "210g",
            "origin": "국내산",
            "explanation_en": f"오뚜기 잡곡밥. 즉석밥. Good for {request.health_goal}.",
            "explanation_ko": f"오뚜기 잡곡밥. 즉석밥. {request.health_goal}에 좋습니다.",
            "score": 86
        },
        {
            "meal_id": "54",
            "name": "CJ 컵반 소고기 덮밥",
            "brand": "CJ제일제당",
            "category": "즉석밥",
            "ingredients": ['쌀', '소고기', '양파', '간장'],
            "allergens": ['beef', 'soy', 'wheat'],
            "calories": 450,
            "protein_g": 16,
            "carbs_g": 72,
            "fat_g": 10,
            "sodium_mg": 920,
            "serving_size": "280g",
            "origin": "국내산 쌀",
            "explanation_en": f"CJ 컵반 소고기 덮밥. 즉석밥. Good for {request.health_goal}.",
            "explanation_ko": f"CJ 컵반 소고기 덮밥. 즉석밥. {request.health_goal}에 좋습니다.",
            "score": 72
        },
        {
            "meal_id": "55",
            "name": "농심 신라면볶음밥",
            "brand": "농심",
            "category": "즉석밥",
            "ingredients": ['쌀', '신라면스프', '김치', '야채'],
            "allergens": ['soy', 'wheat'],
            "calories": 520,
            "protein_g": 12,
            "carbs_g": 85,
            "fat_g": 14,
            "sodium_mg": 1280,
            "serving_size": "280g",
            "origin": "국내산",
            "explanation_en": f"농심 신라면볶음밥. 즉석밥. Good for {request.health_goal}.",
            "explanation_ko": f"농심 신라면볶음밥. 즉석밥. {request.health_goal}에 좋습니다.",
            "score": 65
        },
        {
            "meal_id": "56",
            "name": "오뚜기 진밥 곤약밥",
            "brand": "오뚜기",
            "category": "즉석밥",
            "ingredients": ['곤약', '쌀', '현미'],
            "allergens": [],
            "calories": 180,
            "protein_g": 4,
            "carbs_g": 42,
            "fat_g": 1,
            "sodium_mg": 12,
            "serving_size": "210g",
            "origin": "국내산",
            "explanation_en": f"오뚜기 진밥 곤약밥. 즉석밥. Good for {request.health_goal}.",
            "explanation_ko": f"오뚜기 진밥 곤약밥. 즉석밥. {request.health_goal}에 좋습니다.",
            "score": 90
        },
        {
            "meal_id": "57",
            "name": "CJ 햇반 흑미밥",
            "brand": "CJ제일제당",
            "category": "즉석밥",
            "ingredients": ['흑미', '쌀'],
            "allergens": [],
            "calories": 300,
            "protein_g": 7,
            "carbs_g": 66,
            "fat_g": 2,
            "sodium_mg": 6,
            "serving_size": "210g",
            "origin": "국내산",
            "explanation_en": f"CJ 햇반 흑미밥. 즉석밥. Good for {request.health_goal}.",
            "explanation_ko": f"CJ 햇반 흑미밥. 즉석밥. {request.health_goal}에 좋습니다.",
            "score": 84
        },
        {
            "meal_id": "58",
            "name": "풀무원 쁘띠첼 단호박죽",
            "brand": "풀무원",
            "category": "죽",
            "ingredients": ['단호박', '쌀', '우유'],
            "allergens": ['milk'],
            "calories": 220,
            "protein_g": 5,
            "carbs_g": 42,
            "fat_g": 4,
            "sodium_mg": 180,
            "serving_size": "280g",
            "origin": "국내산 단호박",
            "explanation_en": f"풀무원 쁘띠첼 단호박죽. 죽. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 쁘띠첼 단호박죽. 죽. {request.health_goal}에 좋습니다.",
            "score": 80
        },
        {
            "meal_id": "59",
            "name": "본죽 전복죽",
            "brand": "본아이에프",
            "category": "죽",
            "ingredients": ['쌀', '전복', '참기름', '야채'],
            "allergens": ['shellfish', 'sesame'],
            "calories": 280,
            "protein_g": 8,
            "carbs_g": 48,
            "fat_g": 6,
            "sodium_mg": 680,
            "serving_size": "350g",
            "origin": "국내산 전복",
            "explanation_en": f"본죽 전복죽. 죽. Good for {request.health_goal}.",
            "explanation_ko": f"본죽 전복죽. 죽. {request.health_goal}에 좋습니다.",
            "score": 76
        },
        {
            "meal_id": "60",
            "name": "오뚜기 맛있는 오트밀 플레인",
            "brand": "오뚜기",
            "category": "시리얼",
            "ingredients": ['귀리'],
            "allergens": ['wheat'],
            "calories": 380,
            "protein_g": 14,
            "carbs_g": 68,
            "fat_g": 7,
            "sodium_mg": 5,
            "serving_size": "100g",
            "origin": "호주산",
            "explanation_en": f"오뚜기 맛있는 오트밀 플레인. 시리얼. Good for {request.health_goal}.",
            "explanation_ko": f"오뚜기 맛있는 오트밀 플레인. 시리얼. {request.health_goal}에 좋습니다.",
            "score": 89
        },
        {
            "meal_id": "61",
            "name": "풀무원 닭가슴살 샐러드",
            "brand": "풀무원",
            "category": "샐러드",
            "ingredients": ['닭가슴살', '양상추', '방울토마토', '드레싱'],
            "allergens": ['chicken', 'eggs'],
            "calories": 180,
            "protein_g": 22,
            "carbs_g": 12,
            "fat_g": 5,
            "sodium_mg": 420,
            "serving_size": "200g",
            "origin": "국내산",
            "explanation_en": f"풀무원 닭가슴살 샐러드. 샐러드. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 닭가슴살 샐러드. 샐러드. {request.health_goal}에 좋습니다.",
            "score": 88
        },
        {
            "meal_id": "62",
            "name": "GS25 그릴드 치킨 샐러드",
            "brand": "GS리테일",
            "category": "샐러드",
            "ingredients": ['닭가슴살', '케일', '퀴노아', '견과류'],
            "allergens": ['chicken', 'tree nuts'],
            "calories": 250,
            "protein_g": 24,
            "carbs_g": 18,
            "fat_g": 8,
            "sodium_mg": 480,
            "serving_size": "250g",
            "origin": "국내산",
            "explanation_en": f"GS25 그릴드 치킨 샐러드. 샐러드. Good for {request.health_goal}.",
            "explanation_ko": f"GS25 그릴드 치킨 샐러드. 샐러드. {request.health_goal}에 좋습니다.",
            "score": 86
        },
        {
            "meal_id": "63",
            "name": "CU 단백질 샐러드",
            "brand": "BGF리테일",
            "category": "샐러드",
            "ingredients": ['계란', '두부', '브로콜리', '아보카도'],
            "allergens": ['eggs', 'soy'],
            "calories": 220,
            "protein_g": 18,
            "carbs_g": 14,
            "fat_g": 10,
            "sodium_mg": 380,
            "serving_size": "230g",
            "origin": "국내산",
            "explanation_en": f"CU 단백질 샐러드. 샐러드. Good for {request.health_goal}.",
            "explanation_ko": f"CU 단백질 샐러드. 샐러드. {request.health_goal}에 좋습니다.",
            "score": 87
        },
        {
            "meal_id": "64",
            "name": "풀무원 그린주스 시금치",
            "brand": "풀무원",
            "category": "음료",
            "ingredients": ['시금치', '바나나', '사과', '레몬'],
            "allergens": [],
            "calories": 95,
            "protein_g": 2,
            "carbs_g": 22,
            "fat_g": 0,
            "sodium_mg": 45,
            "serving_size": "200ml",
            "origin": "국내산 시금치",
            "explanation_en": f"풀무원 그린주스 시금치. 음료. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 그린주스 시금치. 음료. {request.health_goal}에 좋습니다.",
            "score": 82
        },
        {
            "meal_id": "65",
            "name": "동원 양배추 쌈",
            "brand": "동원F&B",
            "category": "즉석식품",
            "ingredients": ['양배추', '돼지고기', '두부', '된장'],
            "allergens": ['pork', 'soy'],
            "calories": 280,
            "protein_g": 16,
            "carbs_g": 22,
            "fat_g": 14,
            "sodium_mg": 780,
            "serving_size": "300g",
            "origin": "국내산",
            "explanation_en": f"동원 양배추 쌈. 즉석식품. Good for {request.health_goal}.",
            "explanation_ko": f"동원 양배추 쌈. 즉석식품. {request.health_goal}에 좋습니다.",
            "score": 76
        },
        {
            "meal_id": "66",
            "name": "풀무원 브로콜리 샐러드",
            "brand": "풀무원",
            "category": "샐러드",
            "ingredients": ['브로콜리', '퀴노아', '크랜베리', '호두'],
            "allergens": ['tree nuts'],
            "calories": 160,
            "protein_g": 6,
            "carbs_g": 20,
            "fat_g": 7,
            "sodium_mg": 220,
            "serving_size": "180g",
            "origin": "국내산",
            "explanation_en": f"풀무원 브로콜리 샐러드. 샐러드. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 브로콜리 샐러드. 샐러드. {request.health_goal}에 좋습니다.",
            "score": 85
        },
        {
            "meal_id": "67",
            "name": "오뚜기 단무지",
            "brand": "오뚜기",
            "category": "반찬",
            "ingredients": ['무', '설탕', '식초', '소금'],
            "allergens": [],
            "calories": 45,
            "protein_g": 1,
            "carbs_g": 10,
            "fat_g": 0,
            "sodium_mg": 680,
            "serving_size": "100g",
            "origin": "국내산 무",
            "explanation_en": f"오뚜기 단무지. 반찬. Good for {request.health_goal}.",
            "explanation_ko": f"오뚜기 단무지. 반찬. {request.health_goal}에 좋습니다.",
            "score": 70
        },
        {
            "meal_id": "68",
            "name": "CJ 비비고 나물 3종 세트",
            "brand": "CJ제일제당",
            "category": "반찬",
            "ingredients": ['시금치', '콩나물', '고사리', '참기름'],
            "allergens": ['sesame', 'soy'],
            "calories": 120,
            "protein_g": 5,
            "carbs_g": 12,
            "fat_g": 6,
            "sodium_mg": 420,
            "serving_size": "150g",
            "origin": "국내산",
            "explanation_en": f"CJ 비비고 나물 3종 세트. 반찬. Good for {request.health_goal}.",
            "explanation_ko": f"CJ 비비고 나물 3종 세트. 반찬. {request.health_goal}에 좋습니다.",
            "score": 82
        },
        {
            "meal_id": "69",
            "name": "풀무원 단호박 샐러드",
            "brand": "풀무원",
            "category": "샐러드",
            "ingredients": ['단호박', '그릭요거트', '견과류', '건포도'],
            "allergens": ['milk', 'tree nuts'],
            "calories": 200,
            "protein_g": 6,
            "carbs_g": 28,
            "fat_g": 8,
            "sodium_mg": 120,
            "serving_size": "200g",
            "origin": "국내산 단호박",
            "explanation_en": f"풀무원 단호박 샐러드. 샐러드. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 단호박 샐러드. 샐러드. {request.health_goal}에 좋습니다.",
            "score": 80
        },
        {
            "meal_id": "70",
            "name": "농협 새싹 채소 믹스",
            "brand": "농협",
            "category": "야채",
            "ingredients": ['새싹채소', '브로콜리싹', '무순'],
            "allergens": [],
            "calories": 25,
            "protein_g": 2,
            "carbs_g": 4,
            "fat_g": 0,
            "sodium_mg": 15,
            "serving_size": "80g",
            "origin": "국내산",
            "explanation_en": f"농협 새싹 채소 믹스. 야채. Good for {request.health_goal}.",
            "explanation_ko": f"농협 새싹 채소 믹스. 야채. {request.health_goal}에 좋습니다.",
            "score": 90
        },
        {
            "meal_id": "71",
            "name": "CJ 종가집 포기김치",
            "brand": "CJ제일제당",
            "category": "김치",
            "ingredients": ['배추', '무', '고춧가루', '마늘', '젓갈'],
            "allergens": ['fish', 'shellfish'],
            "calories": 25,
            "protein_g": 2,
            "carbs_g": 4,
            "fat_g": 0,
            "sodium_mg": 580,
            "serving_size": "100g",
            "origin": "국내산 배추",
            "explanation_en": f"CJ 종가집 포기김치. 김치. Good for {request.health_goal}.",
            "explanation_ko": f"CJ 종가집 포기김치. 김치. {request.health_goal}에 좋습니다.",
            "score": 78
        },
        {
            "meal_id": "72",
            "name": "풀무원 얇은 김치",
            "brand": "풀무원",
            "category": "김치",
            "ingredients": ['배추', '무', '고춧가루', '마늘'],
            "allergens": ['fish'],
            "calories": 20,
            "protein_g": 2,
            "carbs_g": 3,
            "fat_g": 0,
            "sodium_mg": 520,
            "serving_size": "100g",
            "origin": "국내산 배추",
            "explanation_en": f"풀무원 얇은 김치. 김치. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 얇은 김치. 김치. {request.health_goal}에 좋습니다.",
            "score": 80
        },
        {
            "meal_id": "73",
            "name": "CJ 종가집 백김치",
            "brand": "CJ제일제당",
            "category": "김치",
            "ingredients": ['배추', '무', '배', '마늘'],
            "allergens": [],
            "calories": 18,
            "protein_g": 1,
            "carbs_g": 4,
            "fat_g": 0,
            "sodium_mg": 480,
            "serving_size": "100g",
            "origin": "국내산",
            "explanation_en": f"CJ 종가집 백김치. 김치. Good for {request.health_goal}.",
            "explanation_ko": f"CJ 종가집 백김치. 김치. {request.health_goal}에 좋습니다.",
            "score": 82
        },
        {
            "meal_id": "74",
            "name": "오뚜기 깍두기",
            "brand": "오뚜기",
            "category": "김치",
            "ingredients": ['무', '고춧가루', '마늘', '젓갈'],
            "allergens": ['fish'],
            "calories": 28,
            "protein_g": 2,
            "carbs_g": 5,
            "fat_g": 0,
            "sodium_mg": 620,
            "serving_size": "100g",
            "origin": "국내산 무",
            "explanation_en": f"오뚜기 깍두기. 김치. Good for {request.health_goal}.",
            "explanation_ko": f"오뚜기 깍두기. 김치. {request.health_goal}에 좋습니다.",
            "score": 76
        },
        {
            "meal_id": "75",
            "name": "CJ 비비고 총각김치",
            "brand": "CJ제일제당",
            "category": "김치",
            "ingredients": ['총각무', '고춧가루', '마늘'],
            "allergens": ['fish'],
            "calories": 22,
            "protein_g": 2,
            "carbs_g": 4,
            "fat_g": 0,
            "sodium_mg": 560,
            "serving_size": "100g",
            "origin": "국내산",
            "explanation_en": f"CJ 비비고 총각김치. 김치. Good for {request.health_goal}.",
            "explanation_ko": f"CJ 비비고 총각김치. 김치. {request.health_goal}에 좋습니다.",
            "score": 77
        },
        {
            "meal_id": "76",
            "name": "풀무원 오이소박이",
            "brand": "풀무원",
            "category": "김치",
            "ingredients": ['오이', '고춧가루', '마늘', '부추'],
            "allergens": ['fish'],
            "calories": 15,
            "protein_g": 1,
            "carbs_g": 3,
            "fat_g": 0,
            "sodium_mg": 420,
            "serving_size": "100g",
            "origin": "국내산 오이",
            "explanation_en": f"풀무원 오이소박이. 김치. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 오이소박이. 김치. {request.health_goal}에 좋습니다.",
            "score": 80
        },
        {
            "meal_id": "77",
            "name": "CJ 햇반 낫또",
            "brand": "CJ제일제당",
            "category": "발효식품",
            "ingredients": ['대두', '낫또균'],
            "allergens": ['soy'],
            "calories": 90,
            "protein_g": 8,
            "carbs_g": 6,
            "fat_g": 5,
            "sodium_mg": 15,
            "serving_size": "50g",
            "origin": "국내산 콩",
            "explanation_en": f"CJ 햇반 낫또. 발효식품. Good for {request.health_goal}.",
            "explanation_ko": f"CJ 햇반 낫또. 발효식품. {request.health_goal}에 좋습니다.",
            "score": 88
        },
        {
            "meal_id": "78",
            "name": "풀무원 청국장",
            "brand": "풀무원",
            "category": "발효식품",
            "ingredients": ['대두', '청국장균', '파', '마늘'],
            "allergens": ['soy'],
            "calories": 110,
            "protein_g": 10,
            "carbs_g": 8,
            "fat_g": 5,
            "sodium_mg": 680,
            "serving_size": "80g",
            "origin": "국내산 콩",
            "explanation_en": f"풀무원 청국장. 발효식품. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 청국장. 발효식품. {request.health_goal}에 좋습니다.",
            "score": 82
        },
        {
            "meal_id": "79",
            "name": "서울우유 케피어",
            "brand": "서울우유",
            "category": "발효유",
            "ingredients": ['우유', '케피어균'],
            "allergens": ['milk'],
            "calories": 75,
            "protein_g": 4,
            "carbs_g": 9,
            "fat_g": 2,
            "sodium_mg": 55,
            "serving_size": "150ml",
            "origin": "국내산 우유",
            "explanation_en": f"서울우유 케피어. 발효유. Good for {request.health_goal}.",
            "explanation_ko": f"서울우유 케피어. 발효유. {request.health_goal}에 좋습니다.",
            "score": 84
        },
        {
            "meal_id": "80",
            "name": "빙그레 떠먹는 불가리스",
            "brand": "빙그레",
            "category": "발효유",
            "ingredients": ['우유', '유산균', '과일'],
            "allergens": ['milk'],
            "calories": 85,
            "protein_g": 4,
            "carbs_g": 12,
            "fat_g": 2,
            "sodium_mg": 60,
            "serving_size": "85g",
            "origin": "국내산 우유",
            "explanation_en": f"빙그레 떠먹는 불가리스. 발효유. Good for {request.health_goal}.",
            "explanation_ko": f"빙그레 떠먹는 불가리스. 발효유. {request.health_goal}에 좋습니다.",
            "score": 82
        },
        {
            "meal_id": "81",
            "name": "농심 구운 아몬드",
            "brand": "농심",
            "category": "견과류",
            "ingredients": ['아몬드', '소금'],
            "allergens": ['tree nuts'],
            "calories": 580,
            "protein_g": 21,
            "carbs_g": 22,
            "fat_g": 50,
            "sodium_mg": 280,
            "serving_size": "100g",
            "origin": "미국산",
            "explanation_en": f"농심 구운 아몬드. 견과류. Good for {request.health_goal}.",
            "explanation_ko": f"농심 구운 아몬드. 견과류. {request.health_goal}에 좋습니다.",
            "score": 86
        },
        {
            "meal_id": "82",
            "name": "롯데 호두과자 미니",
            "brand": "롯데제과",
            "category": "스낵",
            "ingredients": ['밀가루', '호두', '설탕', '계란'],
            "allergens": ['wheat', 'tree nuts', 'eggs', 'milk'],
            "calories": 450,
            "protein_g": 8,
            "carbs_g": 58,
            "fat_g": 22,
            "sodium_mg": 320,
            "serving_size": "100g",
            "origin": "국내산",
            "explanation_en": f"롯데 호두과자 미니. 스낵. Good for {request.health_goal}.",
            "explanation_ko": f"롯데 호두과자 미니. 스낵. {request.health_goal}에 좋습니다.",
            "score": 65
        },
        {
            "meal_id": "83",
            "name": "크라운 쌀과자",
            "brand": "크라운제과",
            "category": "스낵",
            "ingredients": ['쌀', '식물성유지'],
            "allergens": [],
            "calories": 480,
            "protein_g": 6,
            "carbs_g": 68,
            "fat_g": 20,
            "sodium_mg": 420,
            "serving_size": "100g",
            "origin": "국내산 쌀",
            "explanation_en": f"크라운 쌀과자. 스낵. Good for {request.health_goal}.",
            "explanation_ko": f"크라운 쌀과자. 스낵. {request.health_goal}에 좋습니다.",
            "score": 68
        },
        {
            "meal_id": "84",
            "name": "오리온 닥터유 현미칩",
            "brand": "오리온",
            "category": "스낵",
            "ingredients": ['현미', '올리브유', '소금'],
            "allergens": [],
            "calories": 420,
            "protein_g": 7,
            "carbs_g": 62,
            "fat_g": 16,
            "sodium_mg": 380,
            "serving_size": "100g",
            "origin": "국내산 현미",
            "explanation_en": f"오리온 닥터유 현미칩. 스낵. Good for {request.health_goal}.",
            "explanation_ko": f"오리온 닥터유 현미칩. 스낵. {request.health_goal}에 좋습니다.",
            "score": 72
        },
        {
            "meal_id": "85",
            "name": "해태 구운 캐슈넛",
            "brand": "해태제과",
            "category": "견과류",
            "ingredients": ['캐슈넛', '소금'],
            "allergens": ['tree nuts'],
            "calories": 570,
            "protein_g": 18,
            "carbs_g": 32,
            "fat_g": 44,
            "sodium_mg": 320,
            "serving_size": "100g",
            "origin": "베트남산",
            "explanation_en": f"해태 구운 캐슈넛. 견과류. Good for {request.health_goal}.",
            "explanation_ko": f"해태 구운 캐슈넛. 견과류. {request.health_goal}에 좋습니다.",
            "score": 82
        },
        {
            "meal_id": "86",
            "name": "농심 견과류 믹스",
            "brand": "농심",
            "category": "견과류",
            "ingredients": ['아몬드', '호두', '캐슈넛', '건포도'],
            "allergens": ['tree nuts'],
            "calories": 550,
            "protein_g": 19,
            "carbs_g": 28,
            "fat_g": 45,
            "sodium_mg": 180,
            "serving_size": "100g",
            "origin": "미국산",
            "explanation_en": f"농심 견과류 믹스. 견과류. Good for {request.health_goal}.",
            "explanation_ko": f"농심 견과류 믹스. 견과류. {request.health_goal}에 좋습니다.",
            "score": 85
        },
        {
            "meal_id": "87",
            "name": "풀무원 프로틴바 초코",
            "brand": "풀무원",
            "category": "영양바",
            "ingredients": ['대두단백', '귀리', '다크초콜릿'],
            "allergens": ['soy', 'milk', 'wheat'],
            "calories": 180,
            "protein_g": 15,
            "carbs_g": 18,
            "fat_g": 6,
            "sodium_mg": 120,
            "serving_size": "45g",
            "origin": "국내산",
            "explanation_en": f"풀무원 프로틴바 초코. 영양바. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 프로틴바 초코. 영양바. {request.health_goal}에 좋습니다.",
            "score": 84
        },
        {
            "meal_id": "88",
            "name": "CJ 프로틴 에너지바",
            "brand": "CJ제일제당",
            "category": "영양바",
            "ingredients": ['대두단백', '견과류', '꿀'],
            "allergens": ['soy', 'tree nuts'],
            "calories": 190,
            "protein_g": 16,
            "carbs_g": 20,
            "fat_g": 7,
            "sodium_mg": 100,
            "serving_size": "50g",
            "origin": "국내산",
            "explanation_en": f"CJ 프로틴 에너지바. 영양바. Good for {request.health_goal}.",
            "explanation_ko": f"CJ 프로틴 에너지바. 영양바. {request.health_goal}에 좋습니다.",
            "score": 83
        },
        {
            "meal_id": "89",
            "name": "해태 맛동산 구운 양파",
            "brand": "해태제과",
            "category": "스낵",
            "ingredients": ['밀가루', '양파', '식물성유지'],
            "allergens": ['wheat'],
            "calories": 510,
            "protein_g": 7,
            "carbs_g": 64,
            "fat_g": 25,
            "sodium_mg": 520,
            "serving_size": "100g",
            "origin": "국내산",
            "explanation_en": f"해태 맛동산 구운 양파. 스낵. Good for {request.health_goal}.",
            "explanation_ko": f"해태 맛동산 구운 양파. 스낵. {request.health_goal}에 좋습니다.",
            "score": 62
        },
        {
            "meal_id": "90",
            "name": "오리온 참 곡물 칩",
            "brand": "오리온",
            "category": "스낵",
            "ingredients": ['귀리', '현미', '퀴노아'],
            "allergens": ['wheat'],
            "calories": 440,
            "protein_g": 9,
            "carbs_g": 60,
            "fat_g": 18,
            "sodium_mg": 380,
            "serving_size": "100g",
            "origin": "국내산",
            "explanation_en": f"오리온 참 곡물 칩. 스낵. Good for {request.health_goal}.",
            "explanation_ko": f"오리온 참 곡물 칩. 스낵. {request.health_goal}에 좋습니다.",
            "score": 74
        },
        {
            "meal_id": "91",
            "name": "매일 소화가 잘되는 우유",
            "brand": "매일유업",
            "category": "유제품",
            "ingredients": ['우유', '유당분해효소'],
            "allergens": ['milk'],
            "calories": 130,
            "protein_g": 6,
            "carbs_g": 11,
            "fat_g": 7,
            "sodium_mg": 100,
            "serving_size": "200ml",
            "origin": "국내산 우유",
            "explanation_en": f"매일 소화가 잘되는 우유. 유제품. Good for {request.health_goal}.",
            "explanation_ko": f"매일 소화가 잘되는 우유. 유제품. {request.health_goal}에 좋습니다.",
            "score": 83
        },
        {
            "meal_id": "92",
            "name": "서울우유 저지방 우유",
            "brand": "서울우유",
            "category": "유제품",
            "ingredients": ['우유'],
            "allergens": ['milk'],
            "calories": 90,
            "protein_g": 6,
            "carbs_g": 11,
            "fat_g": 2,
            "sodium_mg": 110,
            "serving_size": "200ml",
            "origin": "국내산 우유",
            "explanation_en": f"서울우유 저지방 우유. 유제품. Good for {request.health_goal}.",
            "explanation_ko": f"서울우유 저지방 우유. 유제품. {request.health_goal}에 좋습니다.",
            "score": 86
        },
        {
            "meal_id": "93",
            "name": "남양 맛있는 우유GT",
            "brand": "남양유업",
            "category": "유제품",
            "ingredients": ['우유', '비타민D'],
            "allergens": ['milk'],
            "calories": 120,
            "protein_g": 6,
            "carbs_g": 10,
            "fat_g": 6,
            "sodium_mg": 105,
            "serving_size": "200ml",
            "origin": "국내산 우유",
            "explanation_en": f"남양 맛있는 우유GT. 유제품. Good for {request.health_goal}.",
            "explanation_ko": f"남양 맛있는 우유GT. 유제품. {request.health_goal}에 좋습니다.",
            "score": 84
        },
        {
            "meal_id": "94",
            "name": "풀무원 ABC 주스",
            "brand": "풀무원",
            "category": "음료",
            "ingredients": ['사과', '비트', '당근'],
            "allergens": [],
            "calories": 110,
            "protein_g": 1,
            "carbs_g": 26,
            "fat_g": 0,
            "sodium_mg": 65,
            "serving_size": "200ml",
            "origin": "국내산",
            "explanation_en": f"풀무원 ABC 주스. 음료. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 ABC 주스. 음료. {request.health_goal}에 좋습니다.",
            "score": 78
        },
        {
            "meal_id": "95",
            "name": "농협 바나나우유",
            "brand": "농협",
            "category": "음료",
            "ingredients": ['우유', '바나나', '설탕'],
            "allergens": ['milk'],
            "calories": 180,
            "protein_g": 5,
            "carbs_g": 32,
            "fat_g": 4,
            "sodium_mg": 90,
            "serving_size": "240ml",
            "origin": "국내산 우유",
            "explanation_en": f"농협 바나나우유. 음료. Good for {request.health_goal}.",
            "explanation_ko": f"농협 바나나우유. 음료. {request.health_goal}에 좋습니다.",
            "score": 70
        },
        {
            "meal_id": "96",
            "name": "빙그레 바나나맛우유 라이트",
            "brand": "빙그레",
            "category": "음료",
            "ingredients": ['저지방우유', '바나나향', '설탕'],
            "allergens": ['milk'],
            "calories": 120,
            "protein_g": 5,
            "carbs_g": 20,
            "fat_g": 2,
            "sodium_mg": 85,
            "serving_size": "200ml",
            "origin": "국내산 우유",
            "explanation_en": f"빙그레 바나나맛우유 라이트. 음료. Good for {request.health_goal}.",
            "explanation_ko": f"빙그레 바나나맛우유 라이트. 음료. {request.health_goal}에 좋습니다.",
            "score": 75
        },
        {
            "meal_id": "97",
            "name": "매일 아몬드 브리즈",
            "brand": "매일유업",
            "category": "음료",
            "ingredients": ['아몬드', '물', '칼슘'],
            "allergens": ['tree nuts'],
            "calories": 40,
            "protein_g": 1,
            "carbs_g": 8,
            "fat_g": 1,
            "sodium_mg": 120,
            "serving_size": "200ml",
            "origin": "미국산 아몬드",
            "explanation_en": f"매일 아몬드 브리즈. 음료. Good for {request.health_goal}.",
            "explanation_ko": f"매일 아몬드 브리즈. 음료. {request.health_goal}에 좋습니다.",
            "score": 80
        },
        {
            "meal_id": "98",
            "name": "풀무원 그린주스 케일",
            "brand": "풀무원",
            "category": "음료",
            "ingredients": ['케일', '사과', '레몬', '바나나'],
            "allergens": [],
            "calories": 100,
            "protein_g": 2,
            "carbs_g": 24,
            "fat_g": 0,
            "sodium_mg": 50,
            "serving_size": "200ml",
            "origin": "국내산 케일",
            "explanation_en": f"풀무원 그린주스 케일. 음료. Good for {request.health_goal}.",
            "explanation_ko": f"풀무원 그린주스 케일. 음료. {request.health_goal}에 좋습니다.",
            "score": 82
        },
        {
            "meal_id": "99",
            "name": "CJ 프레시웨이 그릭요거트",
            "brand": "CJ제일제당",
            "category": "유제품",
            "ingredients": ['그릭요거트', '꿀', '견과류'],
            "allergens": ['milk', 'tree nuts'],
            "calories": 150,
            "protein_g": 10,
            "carbs_g": 18,
            "fat_g": 4,
            "sodium_mg": 70,
            "serving_size": "150g",
            "origin": "국내산 우유",
            "explanation_en": f"CJ 프레시웨이 그릭요거트. 유제품. Good for {request.health_goal}.",
            "explanation_ko": f"CJ 프레시웨이 그릭요거트. 유제품. {request.health_goal}에 좋습니다.",
            "score": 85
        },
        {
            "meal_id": "100",
            "name": "빙그레 떠먹는 요플레",
            "brand": "빙그레",
            "category": "유제품",
            "ingredients": ['우유', '유산균', '과일'],
            "allergens": ['milk'],
            "calories": 95,
            "protein_g": 5,
            "carbs_g": 14,
            "fat_g": 2,
            "sodium_mg": 65,
            "serving_size": "120g",
            "origin": "국내산 우유",
            "explanation_en": f"빙그레 떠먹는 요플레. 유제품. Good for {request.health_goal}.",
            "explanation_ko": f"빙그레 떠먹는 요플레. 유제품. {request.health_goal}에 좋습니다.",
            "score": 82
        }
    ]

    # Function to check if meal contains any user allergens
    def contains_allergen(meal_allergens):
        for meal_allergen in meal_allergens:
            meal_allergen_lower = meal_allergen.lower()

            # Direct match
            if meal_allergen_lower in user_allergies:
                return True

            # Check against allergen mapping
            for user_allergy in user_allergies:
                # Check if user allergy matches any known allergen category
                for allergen_category, variants in allergen_mapping.items():
                    if user_allergy in variants or allergen_category == user_allergy:
                        # Check if meal contains this allergen
                        if meal_allergen_lower in variants or meal_allergen_lower == allergen_category:
                            return True

        return False

    # Get meals from database (import hardcoded data if database is empty)
    all_meals_from_db = get_all_meals_from_db()

    if not all_meals_from_db:
        # If database is empty, import the hardcoded meals
        # This will be done in a separate migration, for now just log a warning
        print("⚠️ Warning: No meals found in database")
        all_meals_from_db = []

    # Categories to exclude (supplements, vitamins, non-food items)
    excluded_categories = [
        '당류',  # Supplements/vitamins
        '특수영양식품',  # Special nutritional foods (baby formula, etc.)
        '코코아가공품류 또는 초콜릿류',  # Cocoa/chocolate products (often protein bars)
    ]

    # Supplement/vitamin keywords to filter out (these are NOT real meals)
    supplement_keywords = [
        # 보충제/영양제
        '콜라겐', '아르기닌', 'bcaa', '글루타민', '타우린', '비타', '프로틴', 'protein',
        '영양제', '보충제', '정', '캡슐', '알약', 'collagen', 'arginine',
        'vitamin', 'supplement', '마일리지', '파우더', 'powder',

        # 가공 단백질/영양 성분
        '가수분해', '분리대두', '농축', '추출물', '추출액', 'isolate', 'hydrolyzed',
        '펩타이드', 'peptide', '아미노산', 'amino', '오메가', 'omega',

        # 건강기능식품 관련
        '프로바이오틱스', '유산균', '효소', 'enzyme', '크레아틴', 'creatine',
        '글루코사민', '루테인', '엽산', 'folic', '코엔자임', 'coenzyme',

        # 스포츠/운동 보충제
        '게이너', 'gainer', '웨이', 'whey', '카제인', 'casein',
        '부스터', 'booster', '워크아웃', 'workout', '프리', 'pre-',
        '프로티', 'proti', '하이플로', 'highpro',  # 프로티넷, 하이플로 같은 단백질 제품

        # 다이어트 보조제
        '다이어트식', '저칼로리바', '쉐이크믹스', '체중조절',

        # 의료/특수 용도
        '환자식', '영양액', '영양음료', '환자용',

        # 기능성 커피 (단백질 강화 커피 등)
        '로우카본', 'lowcarb', '발란스 드립', 'balance drip', '셀렉스', 'celex',
        '내일의 커피', '프로핏', 'profit'  # 단백질 강화 커피 브랜드
    ]

    # Filter out meals with allergens and non-food items
    safe_meals = []
    filtered_count = 0
    category_filtered_count = 0
    supplement_filtered_count = 0

    for meal in all_meals_from_db:
        # Skip allergen-containing meals
        if contains_allergen(meal["allergens"]):
            filtered_count += 1
            continue  # Skip this meal

        # Skip supplements and non-food categories
        category = meal.get("category", "")
        if category in excluded_categories:
            category_filtered_count += 1
            continue  # Skip supplements/vitamins

        # Skip supplements/vitamins based on product name keywords
        meal_name = meal.get("name", "").lower()
        is_supplement = any(keyword in meal_name for keyword in supplement_keywords)
        if is_supplement:
            supplement_filtered_count += 1
            continue  # Skip supplements

        # Add is_safe flag
        meal["is_safe"] = True

        # Adjust score based on body condition, health goal, and ChatGPT-extracted preferences
        adjusted_score = adjust_meal_score_for_condition(meal, request.body_condition, request.health_goal, request.preferences)
        meal["adjusted_score"] = adjusted_score
        meal["original_score"] = meal["score"]
        meal["score"] = adjusted_score  # Update the score for sorting

        safe_meals.append(meal)

    # Sort by adjusted score
    safe_meals.sort(key=lambda x: x["score"], reverse=True)

    # Remove duplicate meal names (keep the highest-scoring one for each name)
    seen_names = set()
    unique_meals = []
    for meal in safe_meals:
        meal_name = meal.get("name", "").lower().strip()
        if meal_name not in seen_names:
            seen_names.add(meal_name)
            unique_meals.append(meal)

    # DEBUG: Show top 20 final scores
    print(f"\n{'='*90}")
    print(f"🏆 TOP 20 UNIQUE MEALS AFTER SCORING (showing final scores)")
    print(f"{'='*90}")
    for i, meal in enumerate(unique_meals[:20], 1):
        name = meal.get("name", "")[:50]
        category = meal.get("category", "")[:30]
        final_score = meal.get("score", 0)
        original_score = meal.get("original_score", 0)
        bonus = final_score - original_score
        print(f"{i:2}. {name:50} | {category:30} | Base:{original_score:3} Final:{final_score:3} (Bonus:{bonus:+4})")
    print(f"{'='*90}\n")

    # Take top recommendations (up to 10) from unique meals
    recommendations = unique_meals[:10]

    # Generate recommendation reason based on body condition and health goal
    recommendation_reason = generate_recommendation_reason(
        request.body_condition,
        request.health_goal,
        request.weight_kg,
        request.target_weight_kg,
        tdee,
        len(recommendations)
    )

    return {
        "success": True,
        "user_id": request.user_id,
        "tdee": tdee,
        "user_allergies": request.allergies,
        "total_available": len(all_meals),
        "filtered_out": filtered_count,
        "total_recommendations": len(recommendations),
        "recommendations": recommendations,
        "recommendation_reason": recommendation_reason,
        "message": f"Showing {len(recommendations)} safe meals (filtered out {filtered_count} meals containing allergens)"
    }

@app.post("/api/v1/ocr/scan")
async def scan_food_label(file: UploadFile = File(...)):
    return {
        "success": True,
        "extracted_text": "원재료: 밀가루, 설탕, 소금, 물 (Demo Mode - Sample Text)",
        "confidence": 0.95,
        "method": "demo",
        "nutrition_info": {
            "calories": 250,
            "protein": 8.0,
            "carbs": 45.0,
            "fat": 3.5
        }
    }

@app.get("/docs")
async def get_docs():
    return {"message": "Swagger UI available at /docs"}

if __name__ == "__main__":
    print("🚀 Starting Fitmealor Demo Server...")
    print("📡 Server will be available at http://localhost:8000")
    print("📚 API Documentation at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
