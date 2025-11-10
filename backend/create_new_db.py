#!/usr/bin/env python3
"""
1번 엑셀 파일(20250408_음식DB.xlsx)과 CSV 파일(fitmealor_nutrition_filled.csv)을
사용하여 새로운 데이터베이스를 생성하는 스크립트
"""

import sqlite3
import pandas as pd
import os

# 파일 경로
DATA_DIR = '/Users/goorm/Fitmealor/backend/data'
EXCEL_FILE = os.path.join(DATA_DIR, '20250408_음식DB.xlsx')
CSV_FILE = os.path.join(DATA_DIR, 'fitmealor_nutrition_filled.csv')
DB_FILE = '/Users/goorm/Fitmealor/fitmealor_new.db'

# 기존 DB 파일이 있으면 백업
if os.path.exists(DB_FILE):
    backup_file = DB_FILE.replace('.db', '_backup.db')
    print(f"기존 DB를 백업합니다: {backup_file}")
    os.rename(DB_FILE, backup_file)

print("새로운 데이터베이스 생성 시작...")

# SQLite 연결
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# 테이블 생성
print("테이블 생성 중...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    cuisine TEXT,
    meal_type TEXT,
    diet TEXT,
    tags TEXT,
    calories REAL,
    protein_g REAL,
    fat_g REAL,
    carbs_g REAL,
    allergens TEXT,
    source TEXT
)
''')

# 1. 엑셀 파일에서 데이터 읽기 및 삽입
print(f"\n엑셀 파일 로딩 중: {EXCEL_FILE}")
df_excel = pd.read_excel(EXCEL_FILE)
print(f"엑셀 파일에서 {len(df_excel)}개 행 로드됨")

excel_count = 0
for _, row in df_excel.iterrows():
    try:
        # 필수 영양소 정보가 있는 경우만 추가
        calories = row.get('에너지(kcal)', 0)
        protein = row.get('단백질(g)', 0)
        fat = row.get('지방(g)', 0)
        carbs = row.get('탄수화물(g)', 0)

        # 0이 아닌 값이 하나라도 있으면 추가
        if calories or protein or fat or carbs:
            cursor.execute('''
                INSERT INTO meals (name, description, cuisine, meal_type, diet, tags,
                                   calories, protein_g, fat_g, carbs_g, allergens, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('식품명', ''),
                row.get('식품세분류명', ''),
                row.get('식품대분류명', ''),
                '',  # meal_type
                '',  # diet
                row.get('식품중분류명', ''),
                float(calories) if pd.notna(calories) else 0,
                float(protein) if pd.notna(protein) else 0,
                float(fat) if pd.notna(fat) else 0,
                float(carbs) if pd.notna(carbs) else 0,
                '',  # allergens
                'Korean Food DB'
            ))
            excel_count += 1
    except Exception as e:
        print(f"엑셀 행 처리 오류: {e}")
        continue

print(f"엑셀 파일에서 {excel_count}개 레코드 삽입 완료")

# 2. CSV 파일에서 데이터 읽기 및 삽입
print(f"\nCSV 파일 로딩 중: {CSV_FILE}")
df_csv = pd.read_csv(CSV_FILE)
print(f"CSV 파일에서 {len(df_csv)}개 행 로드됨")

csv_count = 0
for _, row in df_csv.iterrows():
    try:
        cursor.execute('''
            INSERT INTO meals (name, description, cuisine, meal_type, diet, tags,
                               calories, protein_g, fat_g, carbs_g, allergens, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row.get('Dish Name', ''),
            row.get('Description', ''),
            row.get('Cuisine', ''),
            row.get('Meal Type', ''),
            row.get('Diet', ''),
            row.get('Tags', ''),
            float(row.get('Calories (kcal)', 0)) if pd.notna(row.get('Calories (kcal)')) else 0,
            float(row.get('Protein (g)', 0)) if pd.notna(row.get('Protein (g)')) else 0,
            float(row.get('Fat (g)', 0)) if pd.notna(row.get('Fat (g)')) else 0,
            float(row.get('Carbohydrates (g)', 0)) if pd.notna(row.get('Carbohydrates (g)')) else 0,
            row.get('Allergens', ''),
            'Fitmealor CSV'
        ))
        csv_count += 1
    except Exception as e:
        print(f"CSV 행 처리 오류: {e}")
        continue

print(f"CSV 파일에서 {csv_count}개 레코드 삽입 완료")

# 인덱스 생성
print("\n인덱스 생성 중...")
cursor.execute('CREATE INDEX IF NOT EXISTS idx_calories ON meals(calories)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_protein ON meals(protein_g)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON meals(name)')

# 커밋 및 종료
conn.commit()

# 통계 출력
cursor.execute('SELECT COUNT(*) FROM meals')
total_count = cursor.fetchone()[0]

print("\n" + "="*50)
print("데이터베이스 생성 완료!")
print("="*50)
print(f"데이터베이스 파일: {DB_FILE}")
print(f"총 레코드 수: {total_count}")
print(f"  - 엑셀 파일: {excel_count}개")
print(f"  - CSV 파일: {csv_count}개")

# 샘플 데이터 확인
print("\n샘플 데이터 (처음 5개):")
cursor.execute('SELECT id, name, calories, protein_g, fat_g, carbs_g, source FROM meals LIMIT 5')
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, 이름: {row[1]}, 칼로리: {row[2]}, 단백질: {row[3]}g, 지방: {row[4]}g, 탄수화물: {row[5]}g, 출처: {row[6]}")

conn.close()
print("\n완료!")
