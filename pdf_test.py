#!/usr/bin/env python3
"""
Quick test script - no interactive prompts
"""
import os
import sys
from openai import OpenAI

def test_o3_pro():
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_2")

    print("🤖 o3-pro API Key Test")
    print("=" * 30)

    if not api_key:
        print("❌ No API key found")
        print("Checked: OPENAI_API_KEY, OPENAI_API_KEY_2")
        print("\n🔧 To fix this:")
        print("1. Add OPENAI_API_KEY to GitHub Codespaces secrets")
        print("2. Or restart Codespace if already added")
        return

    print("✅ API key found!")
    print(f"📁 Testing with file: test_file.pdf")

    if not os.path.exists("test_file.pdf"):
        print("❌ test_file.pdf not found")
        return

    try:
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized")

        # Try to upload file
        print("📤 Uploading file...")
        uploaded = client.files.create(
            file=open("test_file.pdf", "rb"),
            purpose="user_data"
        )
        print(f"✅ File uploaded: {uploaded.id}")

        # Try o3-pro call
        print("🤖 Calling o3-pro...")
        resp = client.responses.create(
            model="o3-pro",
            reasoning={"effort": "medium"},
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_file", "file_id": uploaded.id},
                    {"type": "input_text", "text": "Summarize this file briefly."}
                ]
            }]
        )

        # Extract results
        out_text = []
        for item in resp.output:
            if getattr(item, "content", None):
                for c in item.content:
                    if getattr(c, "text", None):
                        out_text.append(c.text)

        result = "".join(out_text)

        print("\n🎉 SUCCESS! o3-pro Response:")
        print("=" * 40)
        print(result)
        print("=" * 40)

        # Cleanup
        client.files.delete(uploaded.id)
        print("🗑️ Cleaned up uploaded file")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_o3_pro()