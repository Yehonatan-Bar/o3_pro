#!/usr/bin/env python3
"""Clear mock data and logs"""

import os
import shutil

def clear_mock_data():
    """Clear all mock data and logs"""
    files_to_remove = [
        'logs/all_prompt_responses.jsonl',
        'mock_data/captured_responses.json'
    ]

    dirs_to_clear = [
        'logs',
        'mock_data'
    ]

    print("Clearing mock data and logs...")

    # Remove specific files
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ Removed: {file_path}")
        else:
            print(f"❌ Not found: {file_path}")

    # Clear directories but keep them
    for dir_path in dirs_to_clear:
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"✅ Removed: {file_path}")
        else:
            print(f"❌ Directory not found: {dir_path}")

    print("✅ Mock data cleared! Ready for fresh capture.")

if __name__ == "__main__":
    clear_mock_data()