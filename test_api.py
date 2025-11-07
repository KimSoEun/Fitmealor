import requests

# Register a new user without allergies
reg_response = requests.post('http://localhost:8000/api/v1/auth/register', json={
    'email': 'noallergy@test.com',
    'password': 'test123',
    'name': '알레르기없음',
    'age': 25,
    'gender': '남성',
    'height_cm': 175.0,
    'weight_kg': 70.0,
    'target_weight_kg': 65.0,
    'activity_level': '활동적',
    'health_goal': '근육증가',
    'allergies': []  # No allergies
})

if reg_response.status_code != 201:
    # Already registered, login
    login_response = requests.post('http://localhost:8000/api/v1/auth/login', json={
        'email': 'noallergy@test.com',
        'password': 'test123'
    })
    token = login_response.json().get('token')
else:
    token = reg_response.json().get('token')

print('Token obtained!')

# Get meal recommendations
rec_response = requests.post(
    'http://localhost:8000/api/v1/recommendations/recommend',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'user_id': 'noallergy@test.com',
        'age': 25,
        'gender': '남성',
        'height_cm': 175.0,
        'weight_kg': 70.0,
        'target_weight_kg': 65.0,
        'activity_level': '활동적',
        'health_goal': '근육증가'
    },
    timeout=120
)

print(f'\nAPI Status: {rec_response.status_code}')
if rec_response.status_code == 200:
    rec_data = rec_response.json()
    meals = rec_data.get('recommendations', [])
    print(f'\n✅ SUCCESS! Total meals recommended: {len(meals)}')
    print(f'📋 First 10 meals from official nutrition database (162,583 total foods):')
    print('='*90)
    for i, meal in enumerate(meals[:10], 1):
        name = meal.get('name', '')[:45]
        calories = meal.get('calories', 0)
        protein = meal.get('protein_g', 0)
        score = meal.get('score', 0)
        category = meal.get('category', '')[:25]
        print(f'{i}. {name}')
        print(f'   {calories}kcal | 단백질 {protein}g | 점수 {score} | {category}')
else:
    print(f'Error: {rec_response.text[:500]}')
