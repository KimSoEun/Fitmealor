"""
Migrate meal data from hardcoded list to SQLite database
"""
import sqlite3
import json

DB_PATH = "fitmealor.db"

def create_meals_table():
    """Create meals table in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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
    print("✅ Meals table created successfully")

def insert_sample_data():
    """Insert sample meal data to verify table structure"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Sample meal for testing
    sample_meal = {
        "meal_id": "test_001",
        "name": "테스트 식품",
        "name_en": "Test Food",
        "brand": "테스트브랜드",
        "category": "테스트",
        "ingredients": json.dumps(["재료1", "재료2"]),
        "allergens": json.dumps(["eggs"]),
        "calories": 100,
        "protein_g": 10.0,
        "carbs_g": 5.0,
        "fat_g": 3.0,
        "sodium_mg": 200,
        "serving_size": "100g",
        "origin": "국내산",
        "explanation_en": "Test explanation in English",
        "explanation_ko": "한국어 설명 테스트",
        "score": 85
    }

    cursor.execute("""
        INSERT OR REPLACE INTO meals VALUES (
            :meal_id, :name, :name_en, :brand, :category,
            :ingredients, :allergens, :calories, :protein_g,
            :carbs_g, :fat_g, :sodium_mg, :serving_size,
            :origin, :explanation_en, :explanation_ko, :score
        )
    """, sample_meal)

    conn.commit()
    conn.close()
    print("✅ Sample data inserted successfully")

def verify_table():
    """Verify table creation and data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meals'")
    if cursor.fetchone():
        print("✅ Table 'meals' exists")
    else:
        print("❌ Table 'meals' not found")
        return

    # Check data
    cursor.execute("SELECT COUNT(*) FROM meals")
    count = cursor.fetchone()[0]
    print(f"📊 Total meals in database: {count}")

    # Show sample
    cursor.execute("SELECT meal_id, name, name_en, calories FROM meals LIMIT 3")
    rows = cursor.fetchall()
    print("\n📋 Sample data:")
    for row in rows:
        print(f"  - ID: {row[0]}, Name: {row[1]} ({row[2]}), Calories: {row[3]}")

    conn.close()

if __name__ == "__main__":
    print("🚀 Starting meal data migration...")
    create_meals_table()
    insert_sample_data()
    verify_table()
    print("\n✅ Migration script completed!")
    print("⚠️  Note: Actual meal data will be imported when demo_server.py runs for the first time")
