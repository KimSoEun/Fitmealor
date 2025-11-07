"""
Extract hardcoded meals from demo_server.py
Parse the all_meals list and save as JSON for import
"""
import re
import json
import ast

# Read demo_server.py
with open('demo_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the all_meals list in the content
# It starts with "all_meals = [" and ends with the closing "]"
# The list is inside the recommend_meals function

# Strategy: Find the line "all_meals = [" and extract until we find the matching "]"
lines = content.split('\n')

capturing = False
indent_level = 0
meals_lines = []
start_found = False

for i, line in enumerate(lines):
    if 'all_meals = [' in line and not start_found:
        capturing = True
        start_found = True
        meals_lines.append('[')
        continue

    if capturing:
        meals_lines.append(line)
        # Check if we've reached the end of the list
        stripped = line.strip()
        if stripped == ']' and 'def contains_allergen' in lines[i+1] if i+1 < len(lines) else False:
            break

# Join the lines
meals_code = '\n'.join(meals_lines)

# Now we need to handle the f-strings with {request.health_goal}
# Replace f-string references with placeholder text
meals_code = re.sub(r'f"([^"]*\{request\.health_goal\}[^"]*)"', r'"\1"', meals_code)
meals_code = re.sub(r"f'([^']*\{request\.health_goal\}[^']*)'", r"'\1'", meals_code)
meals_code = meals_code.replace('{request.health_goal}', 'your fitness goals')

print("Extracted meals code:")
print(meals_code[:500])
print("\n\nAttempting to parse...")

try:
    # Try to evaluate as Python literal
    meals_data = ast.literal_eval(meals_code)
    print(f"\n✅ Successfully parsed {len(meals_data)} meals!")

    # Save to JSON file
    with open('meals_data.json', 'w', encoding='utf-8') as f:
        json.dump(meals_data, f, ensure_ascii=False, indent=2)
    print("✅ Saved to meals_data.json")

except Exception as e:
    print(f"❌ Error parsing: {e}")
    # Save the code to a file for inspection
    with open('meals_code_debug.txt', 'w', encoding='utf-8') as f:
        f.write(meals_code)
    print("❌ Saved unparsed code to meals_code_debug.txt for inspection")
