#!/usr/bin/env python3
"""
음식 이름을 영어/한글로 번역하고 데이터베이스에 저장하는 스크립트
"""

import sqlite3
import os
import time
import json
from openai import OpenAI

DB_PATH = '/Users/goorm/Fitmealor/fitmealor.db'
BATCH_SIZE = 50  # 한 번에 처리할 음식 수
CHECKPOINT_FILE = '/Users/goorm/Fitmealor/translation_checkpoint.json'

# OpenAI API 클라이언트 초기화
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def load_checkpoint():
    """체크포인트 로드"""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {'last_processed_id': 0, 'total_processed': 0}

def save_checkpoint(last_id, total):
    """체크포인트 저장"""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump({'last_processed_id': last_id, 'total_processed': total}, f)

def translate_name_with_openai(name: str) -> dict:
    """
    OpenAI API를 사용해서 음식 이름을 영어와 한글로 번역

    Returns:
        dict: {'english': '...', 'korean': '...'}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional food translator. Translate food names into both English and Korean. Return ONLY a JSON object with 'english' and 'korean' keys, nothing else."},
                {"role": "user", "content": f"Translate this food name into both English and Korean: '{name}'\n\nReturn format:\n{{\"english\": \"...\", \"korean\": \"...\"}}"}
            ],
            temperature=0.3,
            max_tokens=150
        )

        # 응답 파싱
        content = response.choices[0].message.content.strip()

        # JSON 파싱
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()

        result = json.loads(content)

        # 검증
        if 'english' in result and 'korean' in result:
            return result
        else:
            print(f"   ⚠️  Invalid response format for '{name}': {content}")
            return {'english': name, 'korean': name}

    except Exception as e:
        print(f"   ❌ Error translating '{name}': {e}")
        # 실패 시에도 '_' 제거
        return {'english': name, 'korean': name.replace('_', ' ')}

def translate_batch(meals: list) -> list:
    """
    여러 음식 이름을 한 번에 번역 (배치 처리)

    Args:
        meals: [(id, name), ...] 형식의 리스트

    Returns:
        list: [(id, english, korean), ...] 형식의 리스트
    """
    results = []
    meal_names = [name for _, name in meals]

    try:
        # 배치 번역 요청
        names_text = '\n'.join([f"{i+1}. {name}" for i, name in enumerate(meal_names)])

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional food translator. Translate each food name into both English and Korean. Return ONLY a JSON array where each element has 'english' and 'korean' keys, nothing else."},
                {"role": "user", "content": f"Translate these food names into both English and Korean:\n\n{names_text}\n\nReturn format:\n[{{\"english\": \"...\", \"korean\": \"...\"}}, ...]"}
            ],
            temperature=0.3,
            max_tokens=3000
        )

        # 응답 파싱
        content = response.choices[0].message.content.strip()

        # JSON 파싱
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()

        translations = json.loads(content)

        # 결과 조합
        for i, (meal_id, name) in enumerate(meals):
            if i < len(translations):
                trans = translations[i]
                # 한글 이름에서 '_' 제거
                korean_name = trans.get('korean', name).replace('_', ' ')
                results.append((meal_id, trans.get('english', name), korean_name))
            else:
                # 원본 이름에서도 '_' 제거
                results.append((meal_id, name, name.replace('_', ' ')))

    except Exception as e:
        print(f"   ❌ Batch translation error: {e}")
        # 실패 시 개별 번역으로 폴백
        for meal_id, name in meals:
            trans = translate_name_with_openai(name)
            # 한글 이름에서 '_' 제거
            korean_name = trans['korean'].replace('_', ' ')
            results.append((meal_id, trans['english'], korean_name))
            time.sleep(0.2)  # API 제한 방지

    return results

def main():
    print("=" * 60)
    print("음식 이름 번역 시작")
    print("=" * 60)

    # 체크포인트 로드
    checkpoint = load_checkpoint()
    last_id = checkpoint['last_processed_id']
    total_processed = checkpoint['total_processed']

    print(f"이전 진행 상황: ID {last_id}까지 {total_processed}개 처리 완료\n")

    # 데이터베이스 연결
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 아직 번역되지 않은 음식 개수 확인
    cursor.execute("""
        SELECT COUNT(*) FROM meals
        WHERE (name_en IS NULL OR name_kr IS NULL) AND id > ?
    """, (last_id,))
    remaining = cursor.fetchone()[0]

    print(f"번역 대기 중: {remaining:,}개\n")

    if remaining == 0:
        print("✅ 모든 음식이 이미 번역되었습니다!")
        conn.close()
        return

    # 배치 단위로 처리
    batch_num = 0

    while True:
        # 다음 배치 가져오기
        cursor.execute("""
            SELECT id, name
            FROM meals
            WHERE (name_en IS NULL OR name_kr IS NULL) AND id > ?
            ORDER BY id
            LIMIT ?
        """, (last_id, BATCH_SIZE))

        batch = cursor.fetchall()

        if not batch:
            break

        batch_num += 1
        print(f"배치 #{batch_num} (ID {batch[0][0]} ~ {batch[-1][0]}, {len(batch)}개)")

        # 배치 번역
        translations = translate_batch(batch)

        # 데이터베이스 업데이트
        for meal_id, english, korean in translations:
            cursor.execute("""
                UPDATE meals
                SET name_en = ?, name_kr = ?
                WHERE id = ?
            """, (english, korean, meal_id))

        conn.commit()

        # 체크포인트 저장
        last_id = batch[-1][0]
        total_processed += len(batch)
        save_checkpoint(last_id, total_processed)

        # 진행 상황 표시
        progress_pct = (total_processed / (total_processed + remaining - len(batch))) * 100
        print(f"   ✓ 완료: {total_processed:,}/{total_processed + remaining:,} ({progress_pct:.1f}%)\n")

        # 샘플 출력
        if len(translations) > 0:
            sample = translations[0]
            print(f"   예시: {batch[0][1]}")
            print(f"         EN: {sample[1]}")
            print(f"         KR: {sample[2]}\n")

        # API 제한 방지
        time.sleep(1)

    conn.close()

    print("\n" + "=" * 60)
    print(f"✅ 번역 완료! 총 {total_processed:,}개 처리")
    print("=" * 60)

if __name__ == "__main__":
    main()
