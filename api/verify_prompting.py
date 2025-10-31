#!/usr/bin/env python3
"""
Verification script for prompting methods.

This script helps verify that the API is loading examples correctly
for different prompting methods (zero-shot, one-shot, few-shot, many-shot).

Usage:
    python verify_prompting.py
"""

import requests
import json


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def verify_prompting_setup(base_url="http://localhost:8000"):
    """Verify the prompting setup by inspecting the API."""
    
    print_header("Citation Intent Classification API - Prompting Verification")
    
    try:
        # 1. Get configuration
        print("\n1. Fetching API configuration...")
        config_response = requests.get(f"{base_url}/config")
        config_response.raise_for_status()
        config = config_response.json()
        
        print(f"\n   Model: {config['model']}")
        print(f"   Dataset: {config['dataset']}")
        print(f"   System Prompt ID: {config['system_prompt_id']}")
        print(f"   Prompting Method: {config['prompting_method']}")
        print(f"   Examples Method: {config['examples_method']}")
        print(f"   Query Template: {config['query_template']}")
        print(f"   Temperature: {config['temperature']}")
        print(f"   Class Labels: {', '.join(config['class_labels'])}")
        
        # 2. Inspect the actual prompt
        print("\n2. Inspecting system prompt...")
        prompt_response = requests.get(f"{base_url}/inspect-prompt")
        prompt_response.raise_for_status()
        prompt_info = prompt_response.json()
        
        print(f"\n   Prompting Method: {prompt_info['prompting_method']}")
        print(f"   Examples Method: {prompt_info['examples_method']}")
        print(f"   Examples per Class: {prompt_info['example_count_per_class']}")
        print(f"   Total Classes: {prompt_info['total_classes']}")
        print(f"   Expected Total Examples: {prompt_info['total_expected_examples']}")
        print(f"   Number of Messages in Prompt: {prompt_info['num_messages']}")
        print(f"   Has Examples: {prompt_info['has_examples']}")
        
        # 3. Show prompt structure
        print("\n3. Prompt Structure:")
        print(f"   Total messages: {len(prompt_info['system_prompt'])}")
        
        for i, msg in enumerate(prompt_info['system_prompt']):
            role = msg['role']
            content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"   Message {i+1}: [{role}] {content_preview}")
        
        # 4. Verification checks
        print("\n4. Verification Checks:")
        
        prompting_method = prompt_info['prompting_method']
        examples_method = prompt_info['examples_method']
        num_messages = prompt_info['num_messages']
        expected_examples = prompt_info['total_expected_examples']
        
        if prompting_method == 'zero-shot':
            if num_messages == 1:
                print("   ✓ Zero-shot: Correct (1 system message, no examples)")
            else:
                print(f"   ✗ Zero-shot: Expected 1 message, got {num_messages}")
        
        elif examples_method == '1-inline':
            # Inline method should have 1 message with examples appended
            if num_messages == 1:
                print(f"   ✓ Inline method: Correct (1 system message with {expected_examples} examples)")
                # Check if EXAMPLES header is present
                system_content = prompt_info['system_prompt'][0]['content']
                if '# EXAMPLES #' in system_content:
                    print("   ✓ Examples header found in system message")
                else:
                    print("   ✗ Examples header '# EXAMPLES #' not found")
            else:
                print(f"   ✗ Inline method: Expected 1 message, got {num_messages}")
        
        elif examples_method == '2-roles':
            # Roles method should have 1 system message + (expected_examples * 2) user/assistant pairs
            expected_messages = 1 + (expected_examples * 2)
            if num_messages == expected_messages:
                print(f"   ✓ Roles method: Correct ({expected_messages} messages total)")
                print(f"     - 1 system message")
                print(f"     - {expected_examples} user/assistant pairs")
            else:
                print(f"   ✗ Roles method: Expected {expected_messages} messages, got {num_messages}")
        
        # 5. Show a snippet of the system prompt
        if prompt_info['has_examples']:
            print("\n5. System Prompt Preview (first message):")
            system_msg = prompt_info['system_prompt'][0]['content']
            lines = system_msg.split('\n')
            
            if examples_method == '1-inline':
                # Show the part with examples
                if '# EXAMPLES #' in system_msg:
                    examples_start = system_msg.index('# EXAMPLES #')
                    preview = system_msg[max(0, examples_start-100):examples_start+500]
                    print(f"\n{preview}\n...")
                else:
                    print(f"\n{system_msg[:500]}...")
            else:
                # For roles method, show first few messages
                print("\n   First 3 messages:")
                for msg in prompt_info['system_prompt'][:3]:
                    content_preview = msg['content'][:150].replace('\n', ' ')
                    print(f"   [{msg['role']}]: {content_preview}...")
        
        print_header("Verification Complete")
        
    except requests.exceptions.ConnectionError:
        print(f"\n✗ Error: Could not connect to API at {base_url}")
        print("   Make sure the API is running with: python main.py")
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ HTTP Error: {e}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    print("\nStarting prompting verification...")
    print("Make sure the API is running on http://localhost:8000")
    
    verify_prompting_setup()
