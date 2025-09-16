#!/usr/bin/env python3
"""
Simple test script to simulate multiple file upload and analysis with o3-pro
Works entirely in terminal without needing web browser access
Supports multiple PDF files at once
"""
import os
import sys
from openai import OpenAI

def analyze_files_with_o3_pro(file_paths, custom_prompt=None):
    """Analyze multiple files using OpenAI o3-pro model"""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_2")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY or OPENAI_API_KEY_2 environment variable not set")
        print("Please add your OpenAI API key to GitHub Codespaces secrets:")
        print("1. Go to your repo → Settings → Secrets and variables → Codespaces")
        print("2. Add secret: OPENAI_API_KEY = your actual OpenAI key")
        return None

    client = OpenAI(api_key=api_key)

    default_prompt = "Read the attached files and give me a concise summary with three key takeaways from each file."
    prompt = custom_prompt if custom_prompt else default_prompt

    uploaded_files = []
    try:
        # 1) Upload all files so the model can reference them
        for file_path in file_paths:
            print(f"📁 Uploading file: {file_path}")
            uploaded = client.files.create(
                file=open(file_path, "rb"),
                purpose="user_data"
            )
            uploaded_files.append(uploaded)
            print(f"✅ File uploaded with ID: {uploaded.id}")

        print(f"🤖 Analyzing {len(file_paths)} files with o3-pro... (this may take a moment)")

        # 2) Build content array with all files
        content = []
        for uploaded in uploaded_files:
            content.append({"type": "input_file", "file_id": uploaded.id})
        content.append({"type": "input_text", "text": prompt})

        # 3) Call o3-pro and include all uploaded files as input parts
        resp = client.responses.create(
            model="o3-pro",
            reasoning={"effort": "medium"},
            input=[
                {
                    "role": "user",
                    "content": content
                }
            ]
        )

        # 4) Extract model text output
        out_text = []
        for item in resp.output:
            if getattr(item, "content", None):
                for c in item.content:
                    if getattr(c, "text", None):
                        out_text.append(c.text)

        result = "".join(out_text)

        # Clean up all uploaded files from OpenAI
        for uploaded in uploaded_files:
            try:
                client.files.delete(uploaded.id)
                print(f"🗑️ Cleaned up uploaded file: {uploaded.id}")
            except:
                pass

        return result

    except Exception as e:
        # Clean up uploaded files on error
        for uploaded in uploaded_files:
            try:
                client.files.delete(uploaded.id)
            except:
                pass
        print(f"❌ Error analyzing files: {str(e)}")
        return None

def main():
    print("🤖 o3-pro Multiple Files Analyzer (Terminal Version)")
    print("=" * 60)

    # Check if file paths provided as arguments
    if len(sys.argv) > 1:
        file_paths = sys.argv[1:]
    else:
        # Interactive mode
        print("📁 Enter file paths to analyze (separated by space):")
        input_paths = input("> ").strip()
        if not input_paths:
            print("❌ No file paths provided")
            return
        file_paths = input_paths.split()

    # Validate all files exist
    valid_paths = []
    for file_path in file_paths:
        if os.path.exists(file_path):
            valid_paths.append(file_path)
            print(f"✅ Found: {file_path}")
        else:
            print(f"❌ File not found: {file_path}")

    if not valid_paths:
        print("❌ No valid files found")
        return

    print(f"\n📁 Will analyze {len(valid_paths)} file{'s' if len(valid_paths) > 1 else ''}")

    # Get custom prompt (optional)
    custom_prompt = input("💭 Enter custom prompt (or press Enter for default): ").strip()
    if not custom_prompt:
        custom_prompt = None

    print(f"\n🔄 Processing {len(valid_paths)} file{'s' if len(valid_paths) > 1 else ''}...")
    for i, path in enumerate(valid_paths, 1):
        print(f"  {i}. {path}")

    if custom_prompt:
        print(f"💭 Using prompt: {custom_prompt}")
    else:
        print("💭 Using default prompt: Read the attached files and give me a concise summary with three key takeaways from each file.")

    # Analyze the files
    result = analyze_files_with_o3_pro(valid_paths, custom_prompt)

    if result:
        print("\n" + "=" * 60)
        print("📊 ANALYSIS RESULTS")
        print("=" * 60)
        print(result)
        print("=" * 60)
    else:
        print("❌ Analysis failed")

if __name__ == "__main__":
    main()