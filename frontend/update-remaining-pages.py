#!/usr/bin/env python3
"""
Update Register.tsx and Home.tsx with translation calls
"""

import re
import json

# Load the generated translations to know what keys we have
with open('/Users/goorm/Fitmealor/frontend/src/locales/ko.json', 'r', encoding='utf-8') as f:
    ko_translations = json.load(f)

def update_file(file_path, page_name):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove currentLang state if it exists
    content = re.sub(
        r'const \[currentLang, setCurrentLang\] = useState\(i18n\.language\);?\n',
        '',
        content
    )

    # Remove language change listener if it exists
    content = re.sub(
        r'useEffect\(\(\) => \{[^}]*setCurrentLang\(lng\);[^}]*\}, \[i18n\]\);?\n?',
        '',
        content,
        flags=re.DOTALL
    )

    # Get all translation keys for this page
    if page_name in ko_translations:
        translations = ko_translations[page_name]

        # Replace each Korean text with translation call
        for key, korean_text in translations.items():
            # Escape special regex characters in korean_text
            escaped_text = re.escape(korean_text)

            # Pattern 1: In JSX {korean_text}
            pattern1 = r'\{["\']' + escaped_text + r'["\']\}'
            replacement1 = "{t('" + page_name + "." + key + "')}"
            content = re.sub(pattern1, replacement1, content)

            # Pattern 2: Direct string "korean_text" or 'korean_text' in JSX
            pattern2 = r'>["\']' + escaped_text + r'["\']<'
            replacement2 = ">{t('" + page_name + "." + key + "')}<"
            content = re.sub(pattern2, replacement2, content)

            # Pattern 3: In attributes like placeholder="korean_text"
            pattern3 = r'="' + escaped_text + r'"'
            replacement3 = '={t(\'' + page_name + '.' + key + '\')}'
            content = re.sub(pattern3, replacement3, content)

            # Pattern 4: currentLang conditionals
            pattern4 = r"\{currentLang === 'en' \? ['\"][^'\"]*['\"] : ['\"]" + escaped_text + r"['\"]\}"
            replacement4 = "{t('" + page_name + "." + key + "')}"
            content = re.sub(pattern4, replacement4, content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {file_path.split('/')[-1]} updated successfully!")

# Update both files
update_file('/Users/goorm/Fitmealor/frontend/src/pages/Register.tsx', 'register')
update_file('/Users/goorm/Fitmealor/frontend/src/pages/Home.tsx', 'home')

print("\n✅ All pages updated successfully!")
