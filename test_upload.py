#!/usr/bin/env python3
"""
Simple test script to simulate file upload and analysis with o3-pro
Works entirely in terminal without needing web browser access
"""
import os
import sys
from openai import OpenAI

def analyze_file_with_o3_pro(file_path, custom_prompt=None):
    """Analyze file using OpenAI o3-pro model"""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_2")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY or OPENAI_API_KEY_2 environment variable not set")
        print("Please add your OpenAI API key to GitHub Codespaces secrets:")
        print("1. Go to your repo → Settings → Secrets and variables → Codespaces")
        print("2. Add secret: OPENAI_API_KEY = your actual OpenAI key")
        return None

    client = OpenAI(api_key=api_key)

    default_prompt = "Read the attached file and give me a concise summary with three key takeaways."
    prompt = custom_prompt if custom_prompt else default_prompt

    try:
        print(f"📁 Uploading file: {file_path}")

        # 1) Upload the file so the model can reference it
        uploaded = client.files.create(
            file=open(file_path, "rb"),
            purpose="user_data"
        )
        print(f"✅ File uploaded with ID: {uploaded.id}")

        print("🤖 Analyzing with o3-pro... (this may take a moment)")

        # 2) Call o3-pro and include the uploaded file as an input part
        resp = client.responses.create(
            model="o3-pro",
            reasoning={"effort": "medium"},
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_file", "file_id": uploaded.id},
                        {"type": "input_text", "text": prompt}
                    ]
                }
            ]
        )

        # 3) Extract model text output
        out_text = []
        for item in resp.output:
            if getattr(item, "content", None):
                for c in item.content:
                    if getattr(c, "text", None):
                        out_text.append(c.text)

        result = "".join(out_text)

        # Clean up the uploaded file from OpenAI
        try:
            client.files.delete(uploaded.id)
            print(f"🗑️ Cleaned up uploaded file: {uploaded.id}")
        except:
            pass

        return result

    except Exception as e:
        print(f"❌ Error analyzing file: {str(e)}")
        return None

def main():
    print("🤖 o3-pro File Analyzer (Terminal Version)")
    print("=" * 50)

    # Check if file path provided as argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Interactive mode
        file_path = input("📁 Enter file path to analyze: ").strip()

    if not file_path:
        print("❌ No file path provided")
        return

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    # Get custom prompt (optional)
    custom_prompt = input("💭 Enter custom prompt (or press Enter for default): ").strip()
    if not custom_prompt:
        custom_prompt = None

    print(f"\n🔄 Processing file: {file_path}")
    if custom_prompt:
        print(f"💭 Using prompt: {custom_prompt}")
    else:
        print("💭 Using default prompt: Read the attached file and give me a concise summary with three key takeaways.")

    # Analyze the file
    result = analyze_file_with_o3_pro(file_path, custom_prompt)

    if result:
        print("\n" + "=" * 50)
        print("📊 ANALYSIS RESULTS")
        print("=" * 50)
        print(result)
        print("=" * 50)
    else:
        print("❌ Analysis failed")

if __name__ == "__main__":
    main()