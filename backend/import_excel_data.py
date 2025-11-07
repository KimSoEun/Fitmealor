#!/usr/bin/env python3
"""
Excel 파일을 데이터베이스로 임포트하는 스크립트
두 개의 엑셀 파일 (가공식품DB, 음식DB)를 fitmealor.db에 임포트합니다.
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

# 파일 경로 설정
DB_PATH = '/Users/goorm/Fitmealor/fitmealor.db'
FILE1_PATH = '/Users/goorm/Fitmealor/backend/data/20250327_가공식품DB_147999건.xlsx'
FILE2_PATH = '/Users/goorm/Fitmealor/backend/data/20250408_음식DB.xlsx'

def clean_value(value):
    """NaN, None 값을 처리하고 값을 정리합니다"""
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    return value

def map_excel_to_db(row, source_file):
    """엑셀 행 데이터를 데이터베이스 스키마로 매핑합니다"""

    # 기본 매핑
    meal_data = {
        'meal_id': clean_value(row.get('식품코드')),
        'name': clean_value(row.get('식품명')),
        'name_en': None,  # 엑셀에 없음
        'brand': clean_value(row.get('제조사명') if '제조사명' in row else None),
        'category': clean_value(row.get('식품대분류명', row.get('식품중분류명', row.get('식품소분류명')))),
        'ingredients': None,  # 엑셀에 없음
        'allergens': None,  # 엑셀에 없음
        'calories': int(float(row.get('에너지(kcal)', 0))) if pd.notna(row.get('에너지(kcal)')) else 0,
        'protein_g': float(row.get('단백질(g)', 0)) if pd.notna(row.get('단백질(g)')) else 0.0,
        'carbs_g': float(row.get('탄수화물(g)', 0)) if pd.notna(row.get('탄수화물(g)')) else 0.0,
        'fat_g': float(row.get('지방(g)', 0)) if pd.notna(row.get('지방(g)')) else 0.0,
        'sodium_mg': int(float(row.get('나트륨(mg)', 0))) if pd.notna(row.get('나트륨(mg)')) else 0,
        'serving_size': clean_value(row.get('영양성분함량기준량', '100g')),
        'origin': clean_value(row.get('원산지국명') if '원산지국명' in row else None),
        'explanation_en': None,  # 엑셀에 없음
        'explanation_ko': None,  # 엑셀에 없음
        'score': 80  # 기본값
    }

    return meal_data

def import_excel_file(file_path, conn, cursor, source_name):
    """엑셀 파일을 읽어서 데이터베이스에 임포트합니다"""

    print(f"\n{'='*60}")
    print(f"임포트 시작: {source_name}")
    print(f"파일: {file_path}")
    print(f"{'='*60}")

    # 엑셀 파일 읽기
    print("엑셀 파일 읽는 중...")
    df = pd.read_excel(file_path)
    total_rows = len(df)
    print(f"총 {total_rows:,}개 행 발견")

    # 데이터 임포트
    success_count = 0
    error_count = 0
    skip_count = 0

    for idx, row in df.iterrows():
        try:
            # 데이터 매핑
            meal_data = map_excel_to_db(row, source_name)

            # meal_id나 name이 없으면 스킵
            if not meal_data['meal_id'] or not meal_data['name']:
                skip_count += 1
                continue

            # 데이터베이스에 삽입
            cursor.execute('''
                INSERT OR REPLACE INTO meals
                (meal_id, name, name_en, brand, category, ingredients, allergens,
                 calories, protein_g, carbs_g, fat_g, sodium_mg, serving_size,
                 origin, explanation_en, explanation_ko, score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                meal_data['meal_id'],
                meal_data['name'],
                meal_data['name_en'],
                meal_data['brand'],
                meal_data['category'],
                meal_data['ingredients'],
                meal_data['allergens'],
                meal_data['calories'],
                meal_data['protein_g'],
                meal_data['carbs_g'],
                meal_data['fat_g'],
                meal_data['sodium_mg'],
                meal_data['serving_size'],
                meal_data['origin'],
                meal_data['explanation_en'],
                meal_data['explanation_ko'],
                meal_data['score']
            ))

            success_count += 1

            # 진행상황 출력 (1000행마다)
            if (idx + 1) % 1000 == 0:
                print(f"진행중... {idx + 1:,} / {total_rows:,} ({(idx + 1) / total_rows * 100:.1f}%)")
                conn.commit()  # 중간 커밋

        except Exception as e:
            error_count += 1
            if error_count <= 10:  # 처음 10개 에러만 출력
                print(f"에러 (행 {idx + 1}): {str(e)}")

    # 최종 커밋
    conn.commit()

    print(f"\n{source_name} 임포트 완료:")
    print(f"  - 성공: {success_count:,}개")
    print(f"  - 스킵: {skip_count:,}개")
    print(f"  - 에러: {error_count:,}개")

    return success_count, skip_count, error_count

def main():
    """메인 함수"""

    print("="*60)
    print("Excel 데이터 임포트 시작")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # 데이터베이스 연결
    print(f"\n데이터베이스 연결 중: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 임포트 전 데이터 개수 확인
    cursor.execute("SELECT COUNT(*) FROM meals")
    before_count = cursor.fetchone()[0]
    print(f"임포트 전 데이터: {before_count:,}개")

    # 파일 1 임포트 (가공식품DB)
    success1, skip1, error1 = import_excel_file(FILE1_PATH, conn, cursor, "가공식품DB")

    # 파일 2 임포트 (음식DB)
    success2, skip2, error2 = import_excel_file(FILE2_PATH, conn, cursor, "음식DB")

    # 임포트 후 데이터 개수 확인
    cursor.execute("SELECT COUNT(*) FROM meals")
    after_count = cursor.fetchone()[0]

    # 결과 요약
    print(f"\n{'='*60}")
    print("전체 임포트 결과 요약")
    print(f"{'='*60}")
    print(f"임포트 전 데이터: {before_count:,}개")
    print(f"임포트 후 데이터: {after_count:,}개")
    print(f"순 증가: {after_count - before_count:,}개")
    print(f"\n파일별 통계:")
    print(f"  가공식품DB - 성공: {success1:,}, 스킵: {skip1:,}, 에러: {error1:,}")
    print(f"  음식DB    - 성공: {success2:,}, 스킵: {skip2:,}, 에러: {error2:,}")
    print(f"\n총 성공: {success1 + success2:,}개")
    print(f"총 스킵: {skip1 + skip2:,}개")
    print(f"총 에러: {error1 + error2:,}개")
    print(f"\n완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # 연결 종료
    conn.close()
    print("\n✓ 임포트 완료!")

if __name__ == "__main__":
    main()
