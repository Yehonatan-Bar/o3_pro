#!/usr/bin/env python3
"""Test script for the mock system"""

import requests
import json
import os

def test_mock_status():
    """Test the mock status endpoint"""
    try:
        response = requests.get('http://localhost:9000/api/mock-status')
        if response.status_code == 200:
            data = response.json()
            print("✅ Mock Status:")
            print(f"   Mock Mode: {data['mock_mode']}")
            print(f"   Mock Data File: {data['mock_data_file']}")
            print(f"   Mock Data Exists: {data['mock_data_exists']}")
            print(f"   Available Mock Responses: {data['available_mock_responses']}")
            print(f"   Current Session Logs: {data['current_session_logs']}")
            return True
        else:
            print(f"❌ Mock status request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing mock status: {e}")
        return False

def test_export_mock_data():
    """Test the export mock data endpoint"""
    try:
        response = requests.get('http://localhost:9000/api/export-mock-data')
        if response.status_code == 200:
            data = response.json()
            print("✅ Export Mock Data:")
            print(f"   {data['message']}")
            print(f"   Total Responses: {data['total_responses']}")
            return True
        else:
            print(f"❌ Export mock data request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing export: {e}")
        return False

def check_files():
    """Check if expected files exist"""
    print("\n📁 File Status:")

    files_to_check = [
        'logs/all_prompt_responses.jsonl',
        'mock_data/captured_responses.json'
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   ✅ {file_path} ({size} bytes)")
        else:
            print(f"   ❌ {file_path} (not found)")

if __name__ == "__main__":
    print("=" * 60)
    print("Mock System Test")
    print("=" * 60)

    # Test endpoints
    test_mock_status()
    print()
    test_export_mock_data()

    # Check files
    check_files()

    print("\n" + "=" * 60)
    print("Instructions:")
    print("1. Run a real analysis to capture responses")
    print("2. Call /api/export-mock-data to create mock file")
    print("3. Set MOCK_MODE=true environment variable")
    print("4. Restart app to use mock responses")
    print("=" * 60)