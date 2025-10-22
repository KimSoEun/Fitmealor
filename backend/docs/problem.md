
- 필터링은 **사전 제거**가 아닌 **후처리 기반 자동 적용 필터**로 동작
- 사용자는 "제외된 메뉴"와 "제외 사유"를 확인 가능 (신뢰도 향상)
- **추천 후보군은 필터링 후에도 최소 Top‑10이 보장**되도록 충분히 확보

---

## 🧠 추천 알고리즘 최적화 목표

추천 알고리즘은 필터링과 별개로, 다음 항목들을 중심으로 **점수를 계산하여 추천 순위를 생성**함.

| 항목 | 설명 | 최적화 방식 |
|------|------|-------------|
| 🥗 **영양 적합도** | 하루/한 끼 타깃 대비 영양 구성 (단백질/칼로리 등) | 거리 기반 유사도 |
| 😋 **맛/카테고리 선호** | 사용자 선호(매운맛/한식/샐러드 등) 반영 | 코사인 유사도 |
| 💸 **예산 고려** | 예산 초과 시 패널티 적용 | 점수 보정 |
| 🔁 **추천 다양성** | Top-N 리스트 내 유사 메뉴 반복 방지 | MMR (Maximal Marginal Relevance) |

> 각 요소는 목적 함수로 통합되어 최종 점수를 계산하며, 가중치는 설정 파일(`configs/default.yaml`)로 조정 가능

---

## 📐 목적 함수 예시

\[
Score = w_{nut}S_{nut} + w_{taste}S_{taste} + w_{hist}S_{hist} + w_{div}S_{div} + w_{cost}S_{cost}
\]

- `S_nut`: 영양소 타깃과의 적합도
- `S_taste`: 사용자 선호 유사도 (맛, 재료, 국가 등)
- `S_hist`: 과거 좋아요/클릭 기록과의 유사도
- `S_div`: 리스트 다양성
- `S_cost`: 예산 초과 여부

---

## 📦 시스템 구조

[User Input]
↓
[후보군 생성 (임베딩 기반)]
↓
[추천 점수 계산]
↓
[Top-100 추출]
↓
[UX 필터링 적용 (알러지, 비건 등)]
↓
[Top-N 결과 노출 + 필터링 사유 안내]

---

## 📊 평가 지표

| 항목 | 지표 | 설명 |
|------|------|------|
| 추천 품질 | Hit@K, NDCG@K | 사용자의 클릭/선택과 얼마나 일치하는가 |
| 조건 위반률 | 필터 후 결과의 알레르기/금지 식단 위반률 | 0%가 목표 |
| 영양 적합도 | 타깃 섭취량 대비 오차율 | 평균 오차 계산 |
| 다양성 | Intra-list Diversity | 추천 리스트 내 중복도 감소 여부 |
| UX 신뢰도 | 필터링 사유 표시율 | 제외 이유가 시각적으로 명확한가 |

---

## ❌ 제외 범위

- 실시간 주문/결제 연동
- 위치 기반 음식점 추천
- 챗봇 인터페이스
- 사용자 장기 선호 모델링 (초기 버전에서는 단기 추천만)

---

## 📌 예시 입력/출력

```json
요청:
{
  "user_profile": {
    "goal": {"type": "weight_loss", "kcal_target": 500},
    "taste_pref": {"spicy": 1.0},
    "diet_rules": ["vegan"],
    "allergy": ["peanut"]
  },
  "request_text": "spicy vegan meal",
  "top_n": 5
}
```

```json
출력:
{
  "items": [
    {
      "item_id": "i320",
      "name": "Spicy Tofu Bowl",
      "desc": "A high-protein vegan bowl with tofu and chili sauce.",
      "nutrition": {"kcal": 470, "protein": 32, "carb": 35, "fat": 15},
      "price_krw": 8700,
      "why": ["Matches protein target", "No allergens", "Spicy preference"]
    },
    ...
  ],
  "excluded_items": [
    {
      "item_id": "i104",
      "name": "Peanut Chili Noodles",
      "excluded_reason": ["Contains allergen: peanut"]
    }
  ]
}
```
