"""
Simple test script for the Citation Intent Classification API

This script demonstrates how to use the API programmatically.
"""

import requests
import json
from pathlib import Path

# API configuration
API_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    return response.status_code == 200

def test_config():
    """Test the config endpoint."""
    print("Testing config endpoint...")
    response = requests.get(f"{API_URL}/config")
    print(f"Status: {response.status_code}")
    config = response.json()
    print(f"Model: {config['model']}")
    print(f"Dataset: {config['dataset']}")
    print(f"Class labels: {config['class_labels']}\n")
    return response.status_code == 200

def test_classify(text, cite_start, cite_end):
    """Test the classify endpoint."""
    print("Testing classify endpoint...")
    print(f"Citation span: '{text[cite_start:cite_end]}'")
    
    data = {
        "text": text,
        "cite_start": cite_start,
        "cite_end": cite_end
    }
    
    response = requests.post(f"{API_URL}/classify", json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResults:")
        print(f"  Citation context: {result['citation_context']}")
        print(f"  Raw prediction: {result['raw_prediction']}")
        print(f"  Predicted class: {result['predicted_class']}")
        print(f"  Valid: {result['valid']}")
        print(f"  Model: {result['model']}")
        return True
    else:
        print(f"Error: {response.json()}")
        return False

def test_with_example_file():
    """Test using the example input file."""
    print("\nTesting with example_input.json...")
    
    example_path = Path(__file__).parent / "example_input.json"
    with open(example_path, 'r') as f:
        data = json.load(f)
    
    return test_classify(data['text'], data['cite_start'], data['cite_end'])

def test_error_handling():
    """Test error handling with invalid input."""
    print("\n\nTesting error handling...")
    
    # Test with invalid cite positions
    data = {
        "text": "Short text",
        "cite_start": 5,
        "cite_end": 100  # Beyond text length
    }
    
    response = requests.post(f"{API_URL}/classify", json=data)
    print(f"Status: {response.status_code}")
    print(f"Expected error: {response.json()}\n")
    return response.status_code == 400

if __name__ == "__main__":
    print("=" * 80)
    print("Citation Intent Classification API - Test Suite")
    print("=" * 80)
    print()
    
    try:
        # Run tests
        test_health()
        test_config()
        test_with_example_file()
        test_error_handling()
        
        print("=" * 80)
        print("All tests completed!")
        print("=" * 80)
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API.")
        print("Make sure the API is running:")
        print("  cd api")
        print("  python main.py")
