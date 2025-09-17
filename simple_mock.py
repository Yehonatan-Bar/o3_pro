#!/usr/bin/env python3
"""Simple mock system for testing without API calls"""

import json
import os

# Load mock responses
MOCK_FILE = 'mock_responses.json'
mock_responses = {}

def load_mock_responses():
    """Load mock responses from JSON file"""
    global mock_responses
    if os.path.exists(MOCK_FILE):
        with open(MOCK_FILE, 'r', encoding='utf-8') as f:
            mock_responses = json.load(f)
        print(f"✅ Loaded {len(mock_responses)} mock responses")
    else:
        print("❌ Mock file not found")

def get_mock_response(guideline_title):
    """Get mock response for a guideline"""
    if guideline_title in mock_responses:
        response_data = mock_responses[guideline_title]
        # Format as JSON response like the model would return
        json_response = {
            "result": response_data["result"],
            "explanation": response_data["explanation"]
        }
        return json.dumps(json_response, ensure_ascii=False)
    return None

def add_mock_response(guideline_title, result, explanation):
    """Add a new mock response"""
    mock_responses[guideline_title] = {
        "result": result,
        "explanation": explanation
    }
    save_mock_responses()

def save_mock_responses():
    """Save mock responses to file"""
    with open(MOCK_FILE, 'w', encoding='utf-8') as f:
        json.dump(mock_responses, f, ensure_ascii=False, indent=2)

# Auto-load on import
load_mock_responses()

if __name__ == "__main__":
    # Test the mock system
    print("Testing mock system:")
    for title in mock_responses.keys():
        response = get_mock_response(title)
        print(f"\n{title}:")
        print(response[:100] + "..." if len(response) > 100 else response)