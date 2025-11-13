#!/usr/bin/env python3
"""
Quick script to replace currentLang conditionals with t() calls in HealthProfile.tsx
"""

import re

file_path = '/Users/goorm/Fitmealor/frontend/src/pages/HealthProfile.tsx'

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define replacement patterns
replacements = {
    "{currentLang === 'en' ? 'Name' : '이름'}": "{t('healthprofile.이름')}",
    "{currentLang === 'en' ? 'Age' : '나이'}": "{t('healthprofile.나이')}",
    "{currentLang === 'en' ? 'Sex' : '성별'}": "{t('healthprofile.성별')}",
    "{currentLang === 'en' ? 'Male' : '남성'}": "{t('healthprofile.남성')}",
    "{currentLang === 'en' ? 'Female' : '여성'}": "{t('healthprofile.여성')}",
    "{currentLang === 'en' ? 'Height' : '키'}": "{t('healthprofile.키')}",
    "{currentLang === 'en' ? 'Current Weight' : '현재 체중'}": "{t('healthprofile.현재_체중')}",
    "{currentLang === 'en' ? 'Goal Weight' : '목표 체중'}": "{t('healthprofile.목표_체중')}",
    "{currentLang === 'en' ? 'Activity Level' : '활동량'}": "{t('healthprofile.활동량')}",
    "{currentLang === 'en' ? 'Health Goal' : '건강 목표'}": "{t('healthprofile.건강_목표')}",
    "{currentLang === 'en' ? 'Sedentary' : '비활동적'}": "{t('healthprofile.비활동적')}",
    "{currentLang === 'en' ? 'Light' : '가볍게 활동적'}": "{t('healthprofile.가볍게_활동적')}",
    "{currentLang === 'en' ? 'Active' : '활동적'}": "{t('healthprofile.활동적')}",
    "{currentLang === 'en' ? 'Very Active' : '매우 활동적'}": "{t('healthprofile.매우_활동적')}",
    "{currentLang === 'en' ? 'Weight Loss' : '체중감량'}": "{t('healthprofile.체중감량')}",
    "{currentLang === 'en' ? 'Maintain Weight' : '체중유지'}": "{t('healthprofile.체중유지')}",
    "{currentLang === 'en' ? 'Muscle Gain' : '근육증가'}": "{t('healthprofile.근육증가')}",
    "{currentLang === 'en' ? 'BMI' : '체질량 지수 (BMI)'}": "{t('healthprofile.체질량_지수_(BMI)')}",
    "{currentLang === 'en' ? bmiCategory.description : bmiCategory.label}": "{i18n.language === 'en' ? bmiCategory.description : bmiCategory.label}",
    "{currentLang === 'en' ? category.description : category.label}": "{i18n.language === 'en' ? category.description : category.label}",
    "{currentLang === 'en' ? 'Calorie & Nutrient Goals' : '칼로리 및 영양소 목표'}": "{t('healthprofile.칼로리_및_영양소_목표')}",
    "{currentLang === 'en' ? 'Basal Metabolic Rate (BMR)' : '기초대사량 (BMR)'}": "{t('healthprofile.기초대사량_(BMR)')}",
    "{currentLang === 'en' ? 'kcal/day' : 'kcal/일'}": "{t('healthprofile.kcal/일')}",
    "{currentLang === 'en' ? 'Total Daily Energy Expenditure (TDEE)' : '일일 소모 칼로리 (TDEE)'}": "{t('healthprofile.일일_소모_칼로리_(TDEE)')}",
    "{currentLang === 'en' ? 'Target Calories' : '목표 칼로리'}": "{t('healthprofile.목표_칼로리')}",
    "{currentLang === 'en' ? 'Daily Nutrient Goals' : '일일 영양소 목표'}": "{t('healthprofile.일일_영양소_목표')}",
    "{currentLang === 'en' ? 'Protein' : '단백질'}": "{t('healthprofile.단백질')}",
    "{currentLang === 'en' ? 'Carbohydrates' : '탄수화물'}": "{t('healthprofile.탄수화물')}",
    "{currentLang === 'en' ? 'Fat' : '지방'}": "{t('healthprofile.지방')}",
    "{currentLang === 'en' ? 'Body Metrics' : '체중 정보'}": "{t('healthprofile.체중_정보')}",
}

# Apply replacements
for old, new in replacements.items():
    content = content.replace(old, new)

# Write back to file
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ HealthProfile.tsx updated successfully!")
print(f"   Applied {len(replacements)} replacements")
