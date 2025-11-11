"""
Translate all meal names from CSV to Korean in batches (faster)
"""
import csv
import json
import os
from openai import OpenAI

# Configure OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CSV_PATH = "/Users/goorm/Fitmealor/backend/data/fitmealor_nutrition_filled.csv"
OUTPUT_PATH = "/Users/goorm/Fitmealor/backend/data/meal_name_translations.json"
BATCH_SIZE = 20  # Translate 20 items at once

def translate_batch(english_names):
    """Translate a batch of English names to Korean in one API call"""
    # Create a numbered list for the API
    numbered_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(english_names)])

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional translator. Translate food dish names from English to Korean. Return ONLY the Korean translations in a numbered list format, one per line. Keep the same numbering."
                },
                {
                    "role": "user",
                    "content": f"Translate these dish names to Korean:\n\n{numbered_list}"
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )

        korean_text = response.choices[0].message.content.strip()

        # Parse the response
        translations = {}
        korean_lines = korean_text.split('\n')

        for i, line in enumerate(korean_lines):
            if i < len(english_names):
                # Remove numbering from Korean translation
                korean_name = line.strip()
                # Remove "1. ", "2. " etc from the start
                if '. ' in korean_name:
                    korean_name = korean_name.split('. ', 1)[1]

                translations[english_names[i]] = korean_name
                print(f"✓ {english_names[i]} → {korean_name}")

        return translations

    except Exception as e:
        print(f"✗ Error translating batch: {e}")
        # Fallback: return English names
        return {name: name for name in english_names}

def main():
    print("Loading meal names from CSV...")

    # Load all unique meal names from CSV
    meal_names = []
    seen = set()
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Dish Name"]
            if name not in seen:
                meal_names.append(name)
                seen.add(name)

    print(f"Found {len(meal_names)} unique meal names")
    print(f"Translating in batches of {BATCH_SIZE}...\n")

    # Translate in batches
    all_translations = {}
    for i in range(0, len(meal_names), BATCH_SIZE):
        batch = meal_names[i:i+BATCH_SIZE]
        print(f"\nBatch {i//BATCH_SIZE + 1}/{(len(meal_names)-1)//BATCH_SIZE + 1}")
        translations = translate_batch(batch)
        all_translations.update(translations)

    # Save to JSON file
    print(f"\nSaving translations to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_translations, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Successfully saved {len(all_translations)} translations!")

if __name__ == "__main__":
    main()
