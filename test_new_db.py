#!/usr/bin/env python3
"""
새로운 데이터베이스를 테스트하는 스크립트
"""

import sqlite3

DB_PATH = '/Users/goorm/Fitmealor/fitmealor.db'

# 데이터베이스 연결
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 60)
print("새 데이터베이스 테스트")
print("=" * 60)

# 1. 총 레코드 수 확인
cursor.execute('SELECT COUNT(*) FROM meals')
total = cursor.fetchone()[0]
print(f"\n총 레코드 수: {total:,}개")

# 2. 소스별 분포 확인
print("\n소스별 분포:")
cursor.execute('SELECT source, COUNT(*) as count FROM meals GROUP BY source')
for row in cursor.fetchall():
    print(f"  - {row[0]}: {row[1]:,}개")

# 3. 샘플 데이터 (각 소스에서 3개씩)
print("\n한국 음식 샘플 (3개):")
cursor.execute('''
    SELECT name, calories, protein_g, fat_g, carbs_g
    FROM meals
    WHERE source = "Korean Food DB"
    LIMIT 3
''')
for i, row in enumerate(cursor.fetchall(), 1):
    print(f"  {i}. {row[0]}")
    print(f"     칼로리: {row[1]:.1f} kcal, 단백질: {row[2]:.1f}g, 지방: {row[3]:.1f}g, 탄수화물: {row[4]:.1f}g")

print("\n국제 요리 샘플 (3개):")
cursor.execute('''
    SELECT name, calories, protein_g, fat_g, carbs_g
    FROM meals
    WHERE source = "Fitmealor CSV"
    LIMIT 3
''')
for i, row in enumerate(cursor.fetchall(), 1):
    print(f"  {i}. {row[0]}")
    print(f"     칼로리: {row[1]:.1f} kcal, 단백질: {row[2]:.1f}g, 지방: {row[3]:.1f}g, 탄수화물: {row[4]:.1f}g")

# 4. 추천 알고리즘 테스트 (TDEE 기반)
print("\n" + "=" * 60)
print("TDEE 기반 추천 알고리즘 테스트")
print("=" * 60)

# 예시 프로필
target_calories = 600
target_protein = 30
target_fat = 20
target_carbs = 70

print(f"\n목표 영양소:")
print(f"  - 칼로리: {target_calories} kcal")
print(f"  - 단백질: {target_protein}g")
print(f"  - 지방: {target_fat}g")
print(f"  - 탄수화물: {target_carbs}g")

# 근사치 음식 찾기 (각 영양소의 오차 합이 최소인 음식)
cursor.execute('''
    SELECT
        name,
        calories,
        protein_g,
        fat_g,
        carbs_g,
        source,
        (ABS(calories - ?) +
         ABS(protein_g - ?) * 4 +
         ABS(fat_g - ?) * 4 +
         ABS(carbs_g - ?) * 4) as difference
    FROM meals
    WHERE calories > 0 AND protein_g > 0 AND carbs_g > 0
    ORDER BY difference ASC
    LIMIT 5
''', (target_calories, target_protein, target_fat, target_carbs))

print("\n가장 근접한 음식 5개:")
for i, row in enumerate(cursor.fetchall(), 1):
    name, cal, protein, fat, carbs, source, diff = row
    print(f"\n{i}. {name} ({source})")
    print(f"   칼로리: {cal:.1f} kcal (차이: {abs(cal - target_calories):.1f})")
    print(f"   단백질: {protein:.1f}g (차이: {abs(protein - target_protein):.1f})")
    print(f"   지방: {fat:.1f}g (차이: {abs(fat - target_fat):.1f})")
    print(f"   탄수화물: {carbs:.1f}g (차이: {abs(carbs - target_carbs):.1f})")

conn.close()

print("\n" + "=" * 60)
print("테스트 완료!")
print("=" * 60)
