"""
TDEE 기반 식품 추천 시스템
"""
import sqlite3
import random
from typing import List, Dict, Any

DB_PATH = '/Users/goorm/Fitmealor/fitmealor.db'

def calculate_tdee(gender: str, age: int, weight_kg: float, height_cm: float, activity_level: str, health_goal: str) -> Dict[str, Any]:
    """
    TDEE (Total Daily Energy Expenditure) 계산

    Args:
        gender: 성별 ('남성' 또는 '여성')
        age: 나이
        weight_kg: 체중 (kg)
        height_cm: 키 (cm)
        activity_level: 활동 수준 ('비활동적', '가볍게 활동적', '활동적', '매우 활동적')
        health_goal: 건강 목표 ('체중감량', '체중유지', '근육증가')

    Returns:
        Dict with TDEE, BMR, and macro targets
    """
    # 1. BMR 계산 (Mifflin-St Jeor 공식)
    if gender in ['남성', 'male', 'Male', 'MALE', 'M', 'm']:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:  # 여성
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    # 2. 활동 수준에 따른 multiplier
    activity_multipliers = {
        '비활동적': 1.2,
        'sedentary': 1.2,
        '가볍게 활동적': 1.375,
        'light': 1.375,
        '활동적': 1.55,
        'moderate': 1.55,
        'active': 1.55,
        '매우 활동적': 1.725,
        'very_active': 1.725,
        'very active': 1.725
    }

    multiplier = activity_multipliers.get(activity_level, 1.55)  # 기본값은 활동적
    tdee = int(bmr * multiplier)

    # 3. 건강 목표에 따른 칼로리 조정
    goal_adjustments = {
        '체중감량': -500,
        'lose_weight': -500,
        'weight_loss': -500,
        '체중유지': 0,
        'maintain': 0,
        '근육증가': +300,
        'gain_muscle': +300,
        'muscle_gain': +300,
        'bulk_up': +300
    }

    adjustment = goal_adjustments.get(health_goal, 0)
    adjusted_tdee = tdee + adjustment

    # 4. 목표에 따른 다량영양소 비율
    macro_ratios = {
        '체중감량': {'protein': 0.40, 'carbs': 0.30, 'fat': 0.30},
        'lose_weight': {'protein': 0.40, 'carbs': 0.30, 'fat': 0.30},
        'weight_loss': {'protein': 0.40, 'carbs': 0.30, 'fat': 0.30},
        '체중유지': {'protein': 0.30, 'carbs': 0.40, 'fat': 0.30},
        'maintain': {'protein': 0.30, 'carbs': 0.40, 'fat': 0.30},
        '근육증가': {'protein': 0.35, 'carbs': 0.45, 'fat': 0.20},
        'gain_muscle': {'protein': 0.35, 'carbs': 0.45, 'fat': 0.20},
        'muscle_gain': {'protein': 0.35, 'carbs': 0.45, 'fat': 0.20},
        'bulk_up': {'protein': 0.30, 'carbs': 0.50, 'fat': 0.20}
    }

    ratios = macro_ratios.get(health_goal, macro_ratios['maintain'])

    # 5. 다량영양소 목표 계산
    macro_targets = {
        'protein_g': (adjusted_tdee * ratios['protein']) / 4,  # 4 cal/g
        'carbs_g': (adjusted_tdee * ratios['carbs']) / 4,      # 4 cal/g
        'fat_g': (adjusted_tdee * ratios['fat']) / 9,          # 9 cal/g
        'calories': adjusted_tdee
    }

    return {
        'bmr': int(bmr),
        'tdee': tdee,
        'adjusted_tdee': adjusted_tdee,
        'macro_targets': macro_targets,
        'activity_multiplier': multiplier,
        'calorie_adjustment': adjustment
    }


def get_meals_from_db(limit: int = 1000) -> List[Dict[str, Any]]:
    """
    데이터베이스에서 식품 데이터 가져오기

    Args:
        limit: 가져올 최대 식품 수

    Returns:
        List of meal dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 영양성분이 있는 식품만 가져오기 (칼로리 > 0)
    query = """
        SELECT id, name, cuisine, calories, protein_g, carbs_g, fat_g, source
        FROM meals
        WHERE calories > 0 AND protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0
        ORDER BY RANDOM()
        LIMIT ?
    """

    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    conn.close()

    meals = []
    for row in rows:
        meals.append({
            'meal_id': row[0],
            'name': row[1],
            'category': row[2] or '기타',
            'calories': row[3] or 0,
            'protein_g': row[4] or 0.0,
            'carbs_g': row[5] or 0.0,
            'fat_g': row[6] or 0.0,
            'sodium_mg': 0,  # 새 DB에는 없는 필드
            'score': 80,     # 기본 점수
            'brand': row[7] or ''  # source를 brand로 사용
        })

    return meals


def score_meal_for_tdee(meal: Dict[str, Any], macro_targets: Dict[str, float]) -> float:
    """
    TDEE 기반으로 식품 점수 계산

    한 끼 식사 목표는 TDEE의 1/3로 가정
    """
    # 한 끼 목표
    meal_cal_target = macro_targets['calories'] / 3
    meal_protein_target = macro_targets['protein_g'] / 3
    meal_carbs_target = macro_targets['carbs_g'] / 3
    meal_fat_target = macro_targets['fat_g'] / 3

    # 각 영양소의 편차 계산 (0~1 범위로 정규화)
    cal_diff = abs(meal['calories'] - meal_cal_target) / meal_cal_target if meal_cal_target > 0 else 0
    protein_diff = abs(meal['protein_g'] - meal_protein_target) / meal_protein_target if meal_protein_target > 0 else 0
    carbs_diff = abs(meal['carbs_g'] - meal_carbs_target) / meal_carbs_target if meal_carbs_target > 0 else 0
    fat_diff = abs(meal['fat_g'] - meal_fat_target) / meal_fat_target if meal_fat_target > 0 else 0

    # 평균 편차 (낮을수록 좋음)
    avg_deviation = (cal_diff + protein_diff + carbs_diff + fat_diff) / 4

    # 100점 만점으로 변환 (편차가 클수록 점수 낮아짐)
    base_score = max(0, 100 - (avg_deviation * 100))

    # 카테고리 기반 점수 조정 (조미식품, 과자류, 빵류, 떡류는 점수 삭감)
    category = meal.get('category', '').lower()
    penalty_keywords = ['조미', '과자', '빵', '떡']

    # 카테고리에 해당 키워드가 포함되어 있으면 점수에 0.5 곱하기 (50% 삭감)
    for keyword in penalty_keywords:
        if keyword in category:
            base_score *= 0.5
            break

    # 가공식품DB 데이터 (brand가 있는 경우) -50점 가중치 적용
    brand = meal.get('brand', '')
    if brand and len(brand) > 0:
        base_score -= 50
        base_score = max(0, base_score)  # 음수 방지

    return base_score


def recommend_meals_by_tdee(
    gender: str,
    age: int,
    weight_kg: float,
    height_cm: float,
    activity_level: str,
    health_goal: str,
    num_recommendations: int = 20
) -> Dict[str, Any]:
    """
    TDEE 기반 식품 추천

    Returns:
        Dict with TDEE info and recommended meals
    """
    # 1. TDEE 계산
    tdee_info = calculate_tdee(gender, age, weight_kg, height_cm, activity_level, health_goal)

    # 2. 데이터베이스에서 식품 가져오기
    meals = get_meals_from_db(limit=2000)  # 충분한 수의 식품 가져오기

    # 3. 각 식품에 점수 부여
    scored_meals = []
    for meal in meals:
        score = score_meal_for_tdee(meal, tdee_info['macro_targets'])
        scored_meals.append({
            **meal,
            'tdee_score': score
        })

    # 4. 점수순으로 정렬
    scored_meals.sort(key=lambda x: x['tdee_score'], reverse=True)

    # 5. 상위 N개 반환
    top_meals = scored_meals[:num_recommendations]

    return {
        'tdee_info': tdee_info,
        'recommendations': top_meals,
        'total_available': len(meals)
    }


if __name__ == "__main__":
    # 테스트
    result = recommend_meals_by_tdee(
        gender="남성",
        age=25,
        weight_kg=70,
        height_cm=175,
        activity_level="활동적",
        health_goal="근육증가",
        num_recommendations=10
    )

    print(f"BMR: {result['tdee_info']['bmr']} kcal")
    print(f"TDEE: {result['tdee_info']['tdee']} kcal")
    print(f"조정된 TDEE: {result['tdee_info']['adjusted_tdee']} kcal")
    print(f"\n다량영양소 목표:")
    print(f"  단백질: {result['tdee_info']['macro_targets']['protein_g']:.1f}g")
    print(f"  탄수화물: {result['tdee_info']['macro_targets']['carbs_g']:.1f}g")
    print(f"  지방: {result['tdee_info']['macro_targets']['fat_g']:.1f}g")
    print(f"\n추천 식품 Top 10:")
    for i, meal in enumerate(result['recommendations'][:10], 1):
        print(f"{i}. {meal['name']}")
        print(f"   칼로리: {meal['calories']}kcal, 단백질: {meal['protein_g']}g, 탄수화물: {meal['carbs_g']}g, 지방: {meal['fat_g']}g")
        print(f"   TDEE 점수: {meal['tdee_score']:.1f}/100")
