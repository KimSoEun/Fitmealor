"""
Extract hardcoded meals from demo_server.py and import into database
This is a one-time migration script
"""
import sqlite3
import json
import re

DB_PATH = "fitmealor.db"

# Hardcoded meals data extracted from demo_server.py
# These meals are simplified without dynamic f-string explanations
MEALS_DATA = [
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
        "explanation_en": "Premium chicken breast steak with 24g protein per serving. Perfectly grilled and seasoned with garlic and olive oil. Contains only 120 calories with minimal fat (2g) and carbs (3g), making it ideal for fitness goals. The broccoli adds fiber and vitamins. Best heated in microwave for 2 minutes or pan-fried for crispy texture.",
        "explanation_ko": "1회 제공량당 24g의 단백질을 함유한 프리미엄 닭가슴살 스테이크입니다. 마늘과 올리브유로 완벽하게 구워 간을 맞췄습니다. 120칼로리에 지방(2g)과 탄수화물(3g)이 최소화되어 건강한 식단에 이상적입니다. 브로콜리가 식이섬유와 비타민을 더해줍니다. 전자레인지 2분 또는 팬에 구워 바삭한 식감으로 즐기세요.",
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
    }
    # Add remaining 98 meals here...
]

def import_meals():
    """Import meals into database"""
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
    for meal in MEALS_DATA:
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
                json.dumps(meal.get("ingredients", []), ensure_ascii=False),
                json.dumps(meal.get("allergens", []), ensure_ascii=False),
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

if __name__ == "__main__":
    print("🚀 Starting meal data import...")
    import_meals()
    print("✅ Import completed!")
