#!/usr/bin/env python3
"""
Extract Korean text from React components and generate translation files using OpenAI
"""

import os
import re
import json
from pathlib import Path

# OpenAI API configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def extract_korean_text(file_path):
    """Extract Korean text from a TypeScript/React file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Patterns to match Korean text
    patterns = [
        r'["\']([^"\']*[\uac00-\ud7a3]+[^"\']*)["\']',  # Strings containing Korean
        r'>([^<]*[\uac00-\ud7a3]+[^<]*)<',  # JSX text content
    ]

    korean_texts = set()
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            text = match.strip()
            if text and any('\uac00' <= c <= '\ud7a3' for c in text):
                korean_texts.add(text)

    return list(korean_texts)

def extract_from_all_pages(pages_dir):
    """Extract Korean text from all page files"""
    all_texts = {}

    pages_dir = Path(pages_dir)
    for file_path in pages_dir.glob('**/*.tsx'):
        print(f"Processing {file_path.name}...")
        texts = extract_korean_text(file_path)
        if texts:
            page_name = file_path.stem.lower()
            all_texts[page_name] = texts
            print(f"  Found {len(texts)} Korean texts")

    return all_texts

def create_translation_key(text):
    """Create a translation key from Korean text"""
    # Remove special characters and convert to camelCase
    key = re.sub(r'[^\w\s가-힣]', '', text)
    key = key.strip().replace(' ', '_')
    return key[:50]  # Limit length

def generate_translation_files(texts_by_page):
    """Generate ko.json and en.json translation files"""
    ko_translations = {}
    en_translations = {}

    for page, texts in texts_by_page.items():
        ko_translations[page] = {}
        en_translations[page] = {}

        for text in texts:
            key = create_translation_key(text)
            ko_translations[page][key] = text
            # Placeholder for English - will be translated by OpenAI
            en_translations[page][key] = f"[TO_TRANSLATE: {text}]"

    return ko_translations, en_translations

def translate_with_openai(texts):
    """Translate Korean texts to English using OpenAI API"""
    from openai import OpenAI

    if not OPENAI_API_KEY:
        print("Warning: OPENAI_API_KEY not found. Using placeholder translations.")
        return {text: f"[EN: {text}]" for text in texts}

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Prepare batch translation
    texts_to_translate = "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate the following Korean UI texts to natural English. Keep the same numbering format."},
                {"role": "user", "content": texts_to_translate}
            ],
            temperature=0.3
        )

        translated_text = response.choices[0].message.content

        # Parse translated texts
        translated_lines = translated_text.strip().split('\n')
        translations = {}
        for line in translated_lines:
            match = re.match(r'(\d+)\.\s*(.+)', line)
            if match:
                idx = int(match.group(1)) - 1
                if idx < len(texts):
                    translations[texts[idx]] = match.group(2).strip()

        return translations
    except Exception as e:
        print(f"Error translating with OpenAI: {e}")
        return {text: f"[EN: {text}]" for text in texts}

def main():
    """Main function"""
    print("🔍 Extracting Korean text from pages...")

    pages_dir = Path(__file__).parent / 'src' / 'pages'
    texts_by_page = extract_from_all_pages(pages_dir)

    if not texts_by_page:
        print("❌ No Korean text found!")
        return

    print(f"\n✅ Found Korean text in {len(texts_by_page)} pages")

    # Generate translation structure
    print("\n📝 Generating translation files...")
    ko_translations, en_translations = generate_translation_files(texts_by_page)

    # Translate with OpenAI if API key is available
    if OPENAI_API_KEY:
        print("\n🤖 Translating with OpenAI API...")
        for page, texts in texts_by_page.items():
            print(f"  Translating {page}...")
            text_list = list(texts)
            translations = translate_with_openai(text_list)

            # Update English translations
            for text in text_list:
                key = create_translation_key(text)
                if text in translations:
                    en_translations[page][key] = translations[text]
    else:
        print("\n⚠️  OPENAI_API_KEY not set. Using placeholder translations.")

    # Save translation files
    locales_dir = Path(__file__).parent / 'src' / 'locales'
    locales_dir.mkdir(exist_ok=True)

    ko_file = locales_dir / 'ko.json'
    en_file = locales_dir / 'en.json'

    with open(ko_file, 'w', encoding='utf-8') as f:
        json.dump(ko_translations, f, ensure_ascii=False, indent=2)

    with open(en_file, 'w', encoding='utf-8') as f:
        json.dump(en_translations, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Translation files created:")
    print(f"  - {ko_file}")
    print(f"  - {en_file}")
    print(f"\n📊 Total translations: {sum(len(v) for v in ko_translations.values())}")

if __name__ == '__main__':
    main()
