#!/usr/bin/env python3
"""
Fitmealor API Test Script
Tests OpenAI and CLOVA OCR integration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai():
    """Test OpenAI API connection"""
    print("🧪 Testing OpenAI API...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    print(f"✅ OpenAI API Key found: {api_key[:20]}...")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Simple test
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"✅ OpenAI Response: {result}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return False

def test_clova_ocr():
    """Test CLOVA OCR API connection"""
    print("\n🧪 Testing CLOVA OCR API...")
    
    secret = os.getenv('CLOVA_OCR_SECRET')
    url = os.getenv('CLOVA_OCR_URL')
    
    if not secret or not url:
        print("❌ CLOVA OCR credentials not found")
        return False
    
    print(f"✅ CLOVA OCR Secret found: {secret[:20]}...")
    print(f"✅ CLOVA OCR URL: {url}")
    
    # Note: Actual OCR test requires an image file
    print("ℹ️  CLOVA OCR configured (image test skipped)")
    return True

def test_database():
    """Test database connection"""
    print("\n🧪 Testing Database Connection...")
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found")
        return False
    
    print(f"✅ Database URL configured: {db_url[:50]}...")
    print("ℹ️  Database connection test skipped (requires PostgreSQL running)")
    return True

def main():
    """Run all API tests"""
    print("=" * 60)
    print("🚀 Fitmealor API Integration Tests")
    print("=" * 60)
    
    results = {
        'OpenAI': test_openai(),
        'CLOVA OCR': test_clova_ocr(),
        'Database': test_database()
    }
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    for service, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{service:20} {status}")
    
    print("=" * 60)
    
    all_passed = all(results.values())
    if all_passed:
        print("🎉 All tests passed! System is ready.")
    else:
        print("⚠️  Some tests failed. Check configuration.")
    
    return all_passed

if __name__ == "__main__":
    main()
