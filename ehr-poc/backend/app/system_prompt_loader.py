import json
import os
import re
from pathlib import Path

_cached_system_prompt = None

def load_system_prompt():
    """Load cached system prompt from JSON file"""
    global _cached_system_prompt
    
    if _cached_system_prompt is not None:
        return _cached_system_prompt
    
    try:
        prompt_path = Path(__file__).parent / "system_prompt.json"
        with open(prompt_path, 'r') as f:
            _cached_system_prompt = json.load(f)
        return _cached_system_prompt
    except FileNotFoundError:
        raise FileNotFoundError(f"System prompt not found at {prompt_path}")

def get_system_instructions():
    """Get system instructions text"""
    prompt = load_system_prompt()
    return prompt["system_instructions"]

def get_keywords():
    """Get keyword mappings"""
    prompt = load_system_prompt()
    return prompt["keywords"]

def get_examples():
    """Get examples for prompt"""
    prompt = load_system_prompt()
    return prompt["examples"]

def detect_order_request(question: str) -> dict:
    """Detect if user is requesting an order - uses word boundary matching"""
    keywords = get_keywords()
    order_keywords = keywords["order_actions"]
    order_types_map = keywords["order_types"]
    
    question_lower = question.lower()
    
    # Word boundary matching: "order" matches "order xray" but not "disorder"
    is_order = False
    for kw in order_keywords:
        pattern = rf'\b{kw}\b'  # Word boundary regex
        if re.search(pattern, question_lower):
            is_order = True
            break
    
    if not is_order:
        return {"is_order": False}
    
    # Find order type
    detected_type = None
    for order_type, type_keywords in order_types_map.items():
        if any(keyword in question_lower for keyword in type_keywords):
            detected_type = order_type
            break
    
    return {
        "is_order": True,
        "order_type": detected_type,
        "full_question": question
    }

def detect_latest_query(question: str) -> bool:
    """Detect if user is asking about 'latest' anything"""
    keywords = get_keywords()
    latest_indicators = keywords["latest_indicators"]
    
    question_lower = question.lower()
    return any(indicator in question_lower for indicator in latest_indicators)

def build_system_prompt_for_claude():
    """Build system prompt with examples for Claude API"""
    instructions = get_system_instructions()
    examples = get_examples()
    
    example_text = "\n\nExamples:\n"
    for ex in examples:
        example_text += f"\nUser: '{ex['user']}'\nLogic: {ex['logic']}\nResponse: {ex['response']}"
    
    full_prompt = instructions + example_text
    return full_prompt
