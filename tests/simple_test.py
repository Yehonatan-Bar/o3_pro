#!/usr/bin/env python3
"""
Simple test using regular OpenAI chat API (o3-pro might not be available yet)
"""
import os
import sys
from openai import OpenAI

def test_openai():
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_2")

    print("🤖 OpenAI API Test")
    print("=" * 30)

    if not api_key:
        print("❌ No API key found")
        return

    print("✅ API key found!")

    if not os.path.exists("test_file.txt"):
        print("❌ test_file.txt not found")
        return

    try:
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized")

        # Read file content directly
        with open("test_file.txt", "r") as f:
            file_content = f.read()

        print("📁 File content loaded")

        # Try different models to see what's available
        models_to_try = ["o3-pro", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]

        for model in models_to_try:
            try:
                print(f"🤖 Trying model: {model}")

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": f"Please analyze this file content and give me a brief summary:\n\n{file_content}"}
                    ],
                    max_tokens=500
                )

                result = response.choices[0].message.content

                print(f"\n🎉 SUCCESS with {model}!")
                print("=" * 40)
                print(result)
                print("=" * 40)
                return

            except Exception as e:
                print(f"❌ {model} failed: {e}")
                continue

        print("❌ All models failed")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_openai()
