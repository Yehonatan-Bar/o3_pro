#!/usr/bin/env python3
import xml.etree.ElementTree as ET

try:
    tree = ET.parse('prompt_library.xml')
    root = tree.getroot()

    general_analysis = root.find('general_analysis_prompt')
    system_prompt = general_analysis.find('system_prompt')

    print("✅ XML loaded successfully!")
    print(f"System prompt starts with: {system_prompt.text[:50]}...")

    # Check if it's the new JSON prompt
    if "[ROLE]" in system_prompt.text:
        print("✅ New JSON prompt is loaded correctly!")
    else:
        print("❌ Still using old prompt")

except Exception as e:
    print(f"❌ Error: {e}")