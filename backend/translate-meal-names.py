"""
Translate all meal names from CSV to Korean and save to JSON cache file
"""
import csv
import json
import os
from openai import OpenAI

# Configure OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CSV_PATH = "/Users/goorm/Fitmealor/backend/data/fitmealor_nutrition_filled.csv"
OUTPUT_PATH = "/Users/goorm/Fitmealor/backend/data/meal_name_translations.json"

def translate_batch(english_names):
    """Translate a batch of English names to Korean"""
    translations = {}

    for name in english_names:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Translate food dish names from English to Korean. Return ONLY the Korean translation, nothing else."
                    },
                    {
                        "role": "user",
                        "content": f"Translate this dish name to Korean: {name}"
                    }
                ],
                temperature=0.3,
                max_tokens=100
            )

            korean_name = response.choices[0].message.content.strip()
            translations[name] = korean_name
            print(f"✓ {name} → {korean_name}")

        except Exception as e:
            print(f"✗ Error translating '{name}': {e}")
            translations[name] = name  # Fallback to English

    return translations

def main():
    print("Loading meal names from CSV...")

    # Load all unique meal names from CSV
    meal_names = set()
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            meal_names.add(row["Dish Name"])

    print(f"Found {len(meal_names)} unique meal names")
    print("\nTranslating...")

    # Translate all names
    translations = translate_batch(sorted(meal_names))

    # Save to JSON file
    print(f"\nSaving translations to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)

    print(f"✓ Successfully saved {len(translations)} translations!")

if __name__ == "__main__":
    main()
