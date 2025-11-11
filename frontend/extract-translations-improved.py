#!/usr/bin/env python3
"""
Improved translation extraction script
Extracts only UI text, filters out JSX comments and code
"""

import os
import re
import json
from pathlib import Path

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def is_valid_ui_text(text):
    """Check if text is valid UI text (not code or comments)"""
    text = text.strip()

    # Filter out empty or whitespace-only
    if not text or len(text.strip()) == 0:
        return False

    # Filter out JSX comments
    if text.startswith('{/*') or text.endswith('*/}'):
        return False

    # Filter out code snippets (contains JSX syntax)
    if '{' in text and ('===' in text or '?' in text or 'className' in text):
        return False

    # Filter out very long texts (likely code)
    if len(text) > 100:
        return False

    # Filter out texts with lots of special characters
    special_char_ratio = sum(1 for c in text if c in '{}<>[]()=;:,./\\') / len(text)
    if special_char_ratio > 0.3:
        return False

    # Must contain at least some Korean
    has_korean = any('\uac00' <= c <= '\ud7a3' for c in text)
    if not has_korean:
        return False

    # Filter out variable names and keys
    if text.startswith('currentLang') or '_' in text[:5]:
        return False

    return True

def extract_korean_from_file(file_path):
    """Extract Korean UI texts from a file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    korean_texts = set()

    # Pattern 1: Quoted strings
    for match in re.finditer(r'["\']([^"\']*[\uac00-\ud7a3]+[^"\']*)["\']', content):
        text = match.group(1).strip()
        if is_valid_ui_text(text):
            korean_texts.add(text)

    # Pattern 2: JSX text content (between tags, not in braces)
    for match in re.finditer(r'>([^<{]*[\uac00-\ud7a3]+[^<{]*)<', content):
        text = match.group(1).strip()
        if is_valid_ui_text(text) and '{' not in text:
            korean_texts.add(text)

    # Pattern 3: Placeholder text in inputs
    for match in re.finditer(r'placeholder=["\'](.+?)["\']', content):
        text = match.group(1).strip()
        if is_valid_ui_text(text):
            korean_texts.add(text)

    return sorted(list(korean_texts))

def create_translation_structure(texts_by_page):
    """Create nested translation structure"""
    translations = {}

    for page, texts in texts_by_page.items():
        translations[page] = {}

        # Categorize by common UI elements
        for text in texts:
            # Create a simple key
            key = text.replace(' ', '_')[:30]
            if key in translations[page]:
                # Add number suffix if duplicate
                counter = 1
                while f"{key}_{counter}" in translations[page]:
                    counter += 1
                key = f"{key}_{counter}"

            translations[page][key] = text

    return translations

def translate_batch_with_openai(texts, page_name):
    """Translate a batch of Korean texts to English"""
    from openai import OpenAI

    if not OPENAI_API_KEY:
        return {text: f"[{text}]" for text in texts}

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Create numbered list
    text_list = "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])

    try:
        print(f"  Translating {len(texts)} texts for {page_name}...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use cheaper model
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional UI/UX translator. Translate the following Korean UI texts to natural, concise English suitable for web interfaces. Maintain the numbering format. For buttons and labels, use common UI terminology."
                },
                {
                    "role": "user",
                    "content": text_list
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )

        translated_text = response.choices[0].message.content

        # Parse translations
        translations = {}
        for line in translated_text.strip().split('\n'):
            match = re.match(r'(\d+)\.\s*(.+)', line.strip())
            if match:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(texts):
                    translations[texts[idx]] = match.group(2).strip()

        # Fill in any missing translations
        for text in texts:
            if text not in translations:
                translations[text] = text

        return translations

    except Exception as e:
        print(f"    Error: {e}")
        return {text: text for text in texts}

def main():
    print("🔍 Extracting UI texts from pages...\n")

    pages_dir = Path(__file__).parent / 'src' / 'pages'
    texts_by_page = {}

    for file_path in sorted(pages_dir.glob('*.tsx')):
        page_name = file_path.stem.lower()
        texts = extract_korean_from_file(file_path)

        if texts:
            texts_by_page[page_name] = texts
            print(f"✓ {file_path.name}: {len(texts)} texts")

    if not texts_by_page:
        print("\n❌ No Korean UI text found!")
        return

    total = sum(len(texts) for texts in texts_by_page.values())
    print(f"\n✅ Found {total} UI texts in {len(texts_by_page)} pages\n")

    # Create Korean translations
    ko_translations = create_translation_structure(texts_by_page)

    # Create English translations
    print("🤖 Translating to English with OpenAI...\n")
    en_translations = {}

    for page, texts in texts_by_page.items():
        en_translations[page] = {}
        text_list = list(texts)

        # Translate in batches of 30
        batch_size = 30
        for i in range(0, len(text_list), batch_size):
            batch = text_list[i:i+batch_size]
            translations = translate_batch_with_openai(batch, page)

            # Add to structure with same keys as Korean
            for ko_key, ko_text in ko_translations[page].items():
                if ko_text in translations:
                    en_translations[page][ko_key] = translations[ko_text]

    # Save files
    locales_dir = Path(__file__).parent / 'src' / 'locales'
    locales_dir.mkdir(exist_ok=True)

    ko_file = locales_dir / 'ko.json'
    en_file = locales_dir / 'en.json'

    with open(ko_file, 'w', encoding='utf-8') as f:
        json.dump(ko_translations, f, ensure_ascii=False, indent=2)

    with open(en_file, 'w', encoding='utf-8') as f:
        json.dump(en_translations, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Translation files saved:")
    print(f"  📄 {ko_file}")
    print(f"  📄 {en_file}")
    print(f"\n📊 Total: {total} translations")

if __name__ == '__main__':
    main()
