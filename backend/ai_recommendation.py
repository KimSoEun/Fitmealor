"""
OpenAI API를 사용한 AI 기반 식품 추천 시스템
"""
import os
import sqlite3
import json
from typing import List, Dict, Any
from openai import OpenAI

DB_PATH = '/Users/goorm/Fitmealor/fitmealor.db'

# OpenAI API 키는 환경변수에서 가져옴
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def get_random_meals_from_db(limit: int = 50) -> List[Dict[str, Any]]:
    """
    데이터베이스에서 랜덤으로 식품 데이터 가져오기

    Args:
        limit: 가져올 최대 식품 수

    Returns:
        List of meal dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        SELECT meal_id, name, category, calories, protein_g, carbs_g, fat_g, sodium_mg, brand
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
            'sodium_mg': row[7] or 0,
            'brand': row[8] or ''
        })

    return meals


def score_meals_with_ai(
    meals: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
    macro_targets: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    OpenAI API를 사용하여 식품에 점수 부여

    Args:
        meals: 평가할 식품 리스트
        user_profile: 사용자 프로필 (나이, 성별, 건강목표 등)
        macro_targets: 목표 영양소 (칼로리, 단백질, 탄수화물, 지방)

    Returns:
        점수가 부여된 식품 리스트
    """
    # 한 끼 목표 (1일 목표의 1/3)
    meal_targets = {
        'calories': macro_targets['calories'] / 3,
        'protein_g': macro_targets['protein_g'] / 3,
        'carbs_g': macro_targets['carbs_g'] / 3,
        'fat_g': macro_targets['fat_g'] / 3
    }

    # 식품 정보를 간략하게 정리
    meals_summary = []
    for idx, meal in enumerate(meals):
        meals_summary.append({
            'index': idx,
            'name': meal['name'],
            'category': meal['category'],
            'calories': meal['calories'],
            'protein_g': meal['protein_g'],
            'carbs_g': meal['carbs_g'],
            'fat_g': meal['fat_g'],
            'is_processed': bool(meal.get('brand'))
        })

    # OpenAI에게 보낼 프롬프트 작성
    prompt = f"""당신은 영양사이자 건강 전문가입니다. 다음 사용자의 건강 목표와 영양 요구사항을 고려하여 식품 목록의 각 항목에 0-100점 사이의 점수를 부여해주세요.

사용자 정보:
- 나이: {user_profile.get('age', '알 수 없음')}세
- 성별: {user_profile.get('gender', '알 수 없음')}
- 건강 목표: {user_profile.get('healthGoal', '알 수 없음')}
- 활동 수준: {user_profile.get('activityLevel', '알 수 없음')}

한 끼 식사 목표 영양소:
- 칼로리: {meal_targets['calories']:.0f} kcal
- 단백질: {meal_targets['protein_g']:.0f}g
- 탄수화물: {meal_targets['carbs_g']:.0f}g
- 지방: {meal_targets['fat_g']:.0f}g

평가 기준:
1. 목표 영양소와의 적합성 (가장 중요)
2. 건강 목표와의 부합성
3. 영양 균형
4. 가공식품보다 자연식품 우선
5. 과도한 나트륨 함량은 감점

식품 목록:
{json.dumps(meals_summary, ensure_ascii=False, indent=2)}

각 식품에 대해 다음 JSON 형식으로 점수와 간단한 이유를 제공해주세요:
{{
  "scores": [
    {{"index": 0, "score": 85, "reason": "높은 단백질 함량으로 근육 증가 목표에 적합"}},
    {{"index": 1, "score": 72, "reason": "적절한 칼로리지만 나트륨이 다소 높음"}},
    ...
  ]
}}

JSON 형식만 응답해주세요."""

    try:
        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 전문 영양사입니다. 항상 JSON 형식으로만 응답합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        # 응답 파싱
        result = json.loads(response.choices[0].message.content)
        scores_data = result.get('scores', [])

        # 점수를 식품 데이터에 추가
        for score_item in scores_data:
            idx = score_item['index']
            if 0 <= idx < len(meals):
                meals[idx]['ai_score'] = score_item['score']
                meals[idx]['ai_reason'] = score_item.get('reason', '')

        # 점수가 없는 항목에는 기본 점수 부여
        for meal in meals:
            if 'ai_score' not in meal:
                meal['ai_score'] = 50
                meal['ai_reason'] = 'AI 평가 미완료'

        return meals

    except Exception as e:
        print(f"OpenAI API 오류: {e}")
        # 오류 발생 시 모든 항목에 기본 점수 부여
        for meal in meals:
            meal['ai_score'] = 50
            meal['ai_reason'] = f'AI 평가 오류: {str(e)}'
        return meals


def recommend_meals_with_ai(
    gender: str,
    age: int,
    weight_kg: float,
    height_cm: float,
    activity_level: str,
    health_goal: str,
    num_recommendations: int = 20
) -> Dict[str, Any]:
    """
    OpenAI API 기반 식품 추천

    Returns:
        Dict with TDEE info and AI-scored recommended meals
    """
    # TDEE 계산 (기존 로직 재사용)
    from tdee_recommendation import calculate_tdee

    tdee_info = calculate_tdee(gender, age, weight_kg, height_cm, activity_level, health_goal)

    # 데이터베이스에서 식품 가져오기 (더 많이 가져와서 AI가 선택)
    meals = get_random_meals_from_db(limit=100)

    # 사용자 프로필
    user_profile = {
        'age': age,
        'gender': gender,
        'healthGoal': health_goal,
        'activityLevel': activity_level
    }

    # AI로 점수 부여
    scored_meals = score_meals_with_ai(meals, user_profile, tdee_info['macro_targets'])

    # AI 점수순으로 정렬
    scored_meals.sort(key=lambda x: x.get('ai_score', 0), reverse=True)

    # 상위 N개 반환
    top_meals = scored_meals[:num_recommendations]

    return {
        'tdee_info': tdee_info,
        'recommendations': top_meals,
        'total_evaluated': len(meals)
    }


if __name__ == "__main__":
    # 테스트
    result = recommend_meals_with_ai(
        gender="남성",
        age=25,
        weight_kg=70,
        height_cm=175,
        activity_level="활동적",
        health_goal="근육증가",
        num_recommendations=10
    )

    print(f"TDEE: {result['tdee_info']['tdee']} kcal")
    print(f"조정된 TDEE: {result['tdee_info']['adjusted_tdee']} kcal")
    print(f"\nAI 추천 식품 Top 10:")
    for i, meal in enumerate(result['recommendations'][:10], 1):
        print(f"{i}. {meal['name']}")
        print(f"   AI 점수: {meal.get('ai_score', 0)}/100")
        print(f"   이유: {meal.get('ai_reason', '')}")
        print(f"   영양: {meal['calories']}kcal, 단백질 {meal['protein_g']}g")
