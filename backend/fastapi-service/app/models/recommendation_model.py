"""
AI Meal Recommendation Model
Uses nutrition expertise to recommend personalized meals
"""

import torch
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from openai import AsyncOpenAI
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """User health profile data"""
    user_id: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    target_weight_kg: float
    activity_level: str
    health_goal: str
    allergies: List[str]
    dietary_restrictions: List[str]
    health_conditions: Optional[List[str]] = None
    symptoms: Optional[List[str]] = None


@dataclass
class MealData:
    """Meal nutritional data"""
    meal_id: str
    name: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    ingredients: List[str]
    allergens: List[str]
    is_vegetarian: bool
    is_vegan: bool
    is_halal: bool


class NutritionExpertModel:
    """
    Nutrition expert AI model for meal recommendations
    
    Process:
    1. Analyze user health status and symptoms
    2. Infer deficient nutrients using nutrition expert prompt
    3. Search foods containing required nutrients
    4. Apply personalization filtering (allergies, preferences, goals)
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.expert_prompt = settings.NUTRITION_EXPERT_PROMPT
        
    async def analyze_health_status(
        self,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """
        Step 1: Analyze user health status and calculate nutritional needs
        """
        # Calculate TDEE (Total Daily Energy Expenditure)
        tdee = self._calculate_tdee(profile)
        
        # Calculate macronutrient targets based on health goal
        macro_targets = self._calculate_macro_targets(tdee, profile.health_goal)
        
        # Analyze symptoms to identify potential deficiencies
        deficiencies = await self._analyze_symptoms(profile)
        
        return {
            "tdee": tdee,
            "macro_targets": macro_targets,
            "identified_deficiencies": deficiencies,
            "health_goal": profile.health_goal
        }
    
    def _calculate_tdee(self, profile: UserProfile) -> int:
        """Calculate Total Daily Energy Expenditure using Mifflin-St Jeor"""
        # BMR calculation
        if profile.gender.lower() == 'male':
            bmr = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + 5
        else:
            bmr = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age - 161
        
        # Activity multipliers
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }
        
        multiplier = activity_multipliers.get(profile.activity_level, 1.55)
        tdee = int(bmr * multiplier)
        
        # Adjust for weight goal
        if profile.health_goal == 'lose_weight':
            tdee -= 500  # 500 calorie deficit
        elif profile.health_goal in ['gain_muscle', 'bulk_up']:
            tdee += 300  # 300 calorie surplus
        
        return tdee
    
    def _calculate_macro_targets(
        self,
        tdee: int,
        health_goal: str
    ) -> Dict[str, float]:
        """Calculate macronutrient targets based on health goal"""
        macro_ratios = {
            'lose_weight': {'protein': 0.40, 'carbs': 0.30, 'fat': 0.30},
            'maintain': {'protein': 0.30, 'carbs': 0.40, 'fat': 0.30},
            'gain_muscle': {'protein': 0.35, 'carbs': 0.45, 'fat': 0.20},
            'bulk_up': {'protein': 0.30, 'carbs': 0.50, 'fat': 0.20},
        }
        
        ratios = macro_ratios.get(health_goal, macro_ratios['maintain'])
        
        return {
            'protein_g': (tdee * ratios['protein']) / 4,  # 4 cal/g
            'carbs_g': (tdee * ratios['carbs']) / 4,      # 4 cal/g
            'fat_g': (tdee * ratios['fat']) / 9,           # 9 cal/g
            'calories': tdee
        }
    
    async def _analyze_symptoms(
        self,
        profile: UserProfile
    ) -> List[Dict[str, Any]]:
        """
        Use GPT-4 with nutrition expert prompt to analyze symptoms
        and identify potential nutrient deficiencies
        """
        if not profile.symptoms or not settings.OPENAI_API_KEY:
            return []
        
        prompt = f"""{self.expert_prompt}

사용자 정보:
- 나이: {profile.age}세
- 성별: {profile.gender}
- 건강 목표: {profile.health_goal}
- 증상: {', '.join(profile.symptoms) if profile.symptoms else '없음'}
- 건강 상태: {', '.join(profile.health_conditions) if profile.health_conditions else '없음'}

위 정보를 바탕으로 부족할 가능성이 있는 영양소와 그 이유를 분석해주세요.
JSON 형식으로 답변해주세요:
{{
  "deficiencies": [
    {{
      "nutrient": "영양소 이름",
      "reason": "부족 가능성 이유",
      "recommended_foods": ["음식1", "음식2"],
      "severity": "low/medium/high"
    }}
  ]
}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self.expert_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('deficiencies', [])
            
        except Exception as e:
            logger.error(f"Error analyzing symptoms: {e}")
            return []
    
    async def recommend_meals(
        self,
        profile: UserProfile,
        available_meals: List[MealData],
        num_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Main recommendation function
        
        Steps:
        1. Analyze health status
        2. Filter out allergens and dietary restrictions
        3. Score meals based on nutritional needs
        4. Generate personalized explanations
        """
        # Step 1: Analyze health status
        health_analysis = await self.analyze_health_status(profile)
        
        # Step 2: Filter meals
        filtered_meals = self._filter_meals(profile, available_meals)
        
        if not filtered_meals:
            return []
        
        # Step 3: Score meals
        scored_meals = self._score_meals(
            filtered_meals,
            health_analysis,
            profile
        )
        
        # Step 4: Sort and take top recommendations
        scored_meals.sort(key=lambda x: x['score'], reverse=True)
        top_meals = scored_meals[:num_recommendations]
        
        # Step 5: Generate explanations
        recommendations = await self._generate_explanations(
            top_meals,
            health_analysis,
            profile
        )
        
        return recommendations
    
    def _filter_meals(
        self,
        profile: UserProfile,
        meals: List[MealData]
    ) -> List[MealData]:
        """Filter out meals with allergens or incompatible dietary restrictions"""
        filtered = []
        
        for meal in meals:
            # Check allergens
            if any(allergen in meal.allergens for allergen in profile.allergies):
                continue
            
            # Check dietary restrictions
            if 'vegetarian' in profile.dietary_restrictions and not meal.is_vegetarian:
                continue
            if 'vegan' in profile.dietary_restrictions and not meal.is_vegan:
                continue
            if 'halal' in profile.dietary_restrictions and not meal.is_halal:
                continue
            
            filtered.append(meal)
        
        return filtered
    
    def _score_meals(
        self,
        meals: List[MealData],
        health_analysis: Dict[str, Any],
        profile: UserProfile
    ) -> List[Dict[str, Any]]:
        """Score meals based on nutritional fit"""
        targets = health_analysis['macro_targets']
        deficiencies = health_analysis.get('identified_deficiencies', [])
        
        scored_meals = []
        
        for meal in meals:
            # Calculate macro deviation (lower is better)
            protein_dev = abs(meal.protein_g - targets['protein_g'] / 3) / (targets['protein_g'] / 3)
            carbs_dev = abs(meal.carbs_g - targets['carbs_g'] / 3) / (targets['carbs_g'] / 3)
            fat_dev = abs(meal.fat_g - targets['fat_g'] / 3) / (targets['fat_g'] / 3)
            calorie_dev = abs(meal.calories - targets['calories'] / 3) / (targets['calories'] / 3)
            
            # Average deviation (lower is better)
            avg_deviation = (protein_dev + carbs_dev + fat_dev + calorie_dev) / 4
            
            # Base score (100 - deviation penalty)
            base_score = max(0, 100 - (avg_deviation * 100))
            
            # Bonus for addressing deficiencies
            deficiency_bonus = 0
            for deficiency in deficiencies:
                # This would ideally check meal's micronutrient content
                # For now, simple keyword matching
                if any(food.lower() in meal.name.lower() 
                       for food in deficiency.get('recommended_foods', [])):
                    deficiency_bonus += 15
            
            final_score = min(100, base_score + deficiency_bonus)
            
            scored_meals.append({
                'meal': meal,
                'score': final_score,
                'macro_fit': {
                    'protein_deviation': protein_dev,
                    'carbs_deviation': carbs_dev,
                    'fat_deviation': fat_dev,
                    'calorie_deviation': calorie_dev
                }
            })
        
        return scored_meals
    
    async def _generate_explanations(
        self,
        scored_meals: List[Dict[str, Any]],
        health_analysis: Dict[str, Any],
        profile: UserProfile
    ) -> List[Dict[str, Any]]:
        """Generate personalized explanations for recommendations"""
        recommendations = []
        
        for item in scored_meals:
            meal = item['meal']
            score = item['score']
            
            # Generate explanation using GPT
            explanation = await self._generate_meal_explanation(
                meal,
                health_analysis,
                profile
            )
            
            recommendations.append({
                'meal_id': meal.meal_id,
                'name': meal.name,
                'score': score,
                'calories': meal.calories,
                'macros': {
                    'protein_g': meal.protein_g,
                    'carbs_g': meal.carbs_g,
                    'fat_g': meal.fat_g,
                    'fiber_g': meal.fiber_g
                },
                'explanation_en': explanation.get('en', ''),
                'explanation_ko': explanation.get('ko', ''),
                'why_recommended': explanation.get('reasons', []),
                'allergen_safe': True,
                'macro_fit': item['macro_fit']
            })
        
        return recommendations
    
    async def _generate_meal_explanation(
        self,
        meal: MealData,
        health_analysis: Dict[str, Any],
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Generate bilingual explanation for why this meal is recommended"""
        
        if not settings.OPENAI_API_KEY:
            return {
                'en': f"This meal provides {meal.protein_g}g protein, {meal.carbs_g}g carbs, and {meal.fat_g}g fat.",
                'ko': f"이 식단은 단백질 {meal.protein_g}g, 탄수화물 {meal.carbs_g}g, 지방 {meal.fat_g}g을 제공합니다.",
                'reasons': ['Matches your nutritional needs']
            }
        
        prompt = f"""{self.expert_prompt}

사용자 건강 목표: {profile.health_goal}
일일 목표 칼로리: {health_analysis['tdee']}kcal

추천 식단: {meal.name}
- 칼로리: {meal.calories}kcal
- 단백질: {meal.protein_g}g
- 탄수화물: {meal.carbs_g}g
- 지방: {meal.fat_g}g
- 식이섬유: {meal.fiber_g}g

이 식단이 왜 추천되는지 영어와 한국어로 간단히 설명해주세요.
JSON 형식:
{{
  "en": "English explanation (2-3 sentences)",
  "ko": "한국어 설명 (2-3 문장)",
  "reasons": ["reason 1", "reason 2"]
}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self.expert_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return {
                'en': f"Recommended for your {profile.health_goal} goal",
                'ko': f"{profile.health_goal} 목표에 적합한 식단입니다",
                'reasons': ['Nutritionally balanced']
            }


# Global model instance
nutrition_model = NutritionExpertModel()
