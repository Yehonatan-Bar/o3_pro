#!/usr/bin/env python3
"""Test script to verify JSON parsing and prompt loading"""

import json
import re
import xml.etree.ElementTree as ET

def test_prompt_loading():
    """Test that prompt_library.xml loads correctly"""
    print("Testing prompt library loading...")
    try:
        tree = ET.parse('prompt_library.xml')
        root = tree.getroot()

        general_analysis = root.find('general_analysis_prompt')
        if general_analysis is None:
            print("❌ Could not find 'general_analysis_prompt' element")
            return False

        system_prompt = general_analysis.find('system_prompt')
        if system_prompt is None:
            print("❌ Could not find 'system_prompt' element")
            return False

        print(f"✅ Loaded system prompt ({len(system_prompt.text)} characters)")
        print(f"   First 100 chars: {system_prompt.text[:100]}...")

        return True
    except Exception as e:
        print(f"❌ Error loading prompt library: {e}")
        return False

def test_json_parsing():
    """Test JSON extraction from model responses"""
    print("\nTesting JSON parsing...")

    # Test cases with different response formats
    test_cases = [
        {
            "name": "Standard JSON response",
            "response": '{"result": 1, "explanation": "ההנחיה מתקיימת. בעמוד 3, סעיף 4.2"}',
            "expected_result": 1,
            "expected_status": "כן"
        },
        {
            "name": "JSON with extra text",
            "response": 'Here is my analysis:\n{"result": 0, "explanation": "ההנחיה אינה מתקיימת"}\n',
            "expected_result": 0,
            "expected_status": "לא"
        },
        {
            "name": "JSON with multiline explanation",
            "response": '''{"result": -1, "explanation": "לא ניתן לקבוע.\nחסר מידע במסמך"}''',
            "expected_result": -1,
            "expected_status": "Unknown"
        },
        {
            "name": "Malformed JSON with Hebrew text",
            "response": 'התשובה היא כן, ההנחיה מתקיימת',
            "expected_result": None,
            "expected_status": "כן"
        }
    ]

    for test in test_cases:
        print(f"\nTest: {test['name']}")
        result_text = test['response']

        # Extract JSON (similar to app.py logic)
        compliance_status = "Unknown"
        explanation = ""
        json_obj = None

        try:
            # Try direct JSON parsing
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = result_text[json_start:json_end]
                json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                try:
                    json_obj = json.loads(json_str)
                except:
                    pass

            # If no JSON, try regex
            if not json_obj:
                json_pattern = r'\{\s*"result"\s*:\s*(-?\d+)\s*,\s*"explanation"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}'
                matches = re.search(json_pattern, result_text, re.DOTALL | re.MULTILINE)

                if matches:
                    result_value = int(matches.group(1))
                    explanation = matches.group(2)
                    json_obj = {'result': result_value, 'explanation': explanation}

            if json_obj:
                result_value = json_obj.get('result', -1)
                explanation = json_obj.get('explanation', '')

                if result_value == 1:
                    compliance_status = "כן"
                elif result_value == 0:
                    compliance_status = "לא"
                else:
                    compliance_status = "Unknown"
            else:
                # Fallback to Hebrew detection
                if "כן" in result_text:
                    compliance_status = "כן"
                elif "לא" in result_text:
                    compliance_status = "לא"

        except Exception as e:
            print(f"   Error: {e}")

        # Check results
        if compliance_status == test['expected_status']:
            print(f"   ✅ Status: {compliance_status} (correct)")
            if explanation:
                print(f"   Explanation: {explanation[:50]}...")
        else:
            print(f"   ❌ Status: {compliance_status} (expected: {test['expected_status']})")

if __name__ == "__main__":
    print("=" * 60)
    print("JSON Parsing and Prompt Loading Tests")
    print("=" * 60)

    # Test prompt loading
    if test_prompt_loading():
        print("\n✅ Prompt library loaded successfully!")
    else:
        print("\n❌ Prompt library loading failed!")

    # Test JSON parsing
    test_json_parsing()

    print("\n" + "=" * 60)
    print("Tests completed!")