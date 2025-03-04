"""
DeepSeek API Test Script

This script tests the DeepSeek API integration for both Reasoner analysis and Chat function calling.
It can be run independently to verify API connectivity and functionality.
"""

import json
import argparse
from openai import OpenAI
import yaml
import os
import sys

def load_api_key():
    """Load API key from secrets.yaml or environment variable."""
    
    # First try environment variable
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if api_key:
        print("Using DeepSeek API key from environment variable")
        return api_key
    
    # Try various possible locations for the secrets.yaml file
    possible_paths = []
    
    # Current working directory
    possible_paths.append(os.path.join(os.getcwd(), "config", "secrets.yaml"))
    
    # Script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths.append(os.path.join(script_dir, "config", "secrets.yaml"))
    
    # One level up from script directory
    possible_paths.append(os.path.join(os.path.dirname(script_dir), "config", "secrets.yaml"))
    
    # Two levels up from script directory (for nested modules)
    possible_paths.append(os.path.join(os.path.dirname(os.path.dirname(script_dir)), "config", "secrets.yaml"))
    
    # Try each possible path
    for secrets_path in possible_paths:
        print(f"Looking for secrets file at: {secrets_path}")
        if os.path.exists(secrets_path):
            try:
                with open(secrets_path, 'r') as file:
                    secrets = yaml.safe_load(file)
                    if secrets and 'apis' in secrets and 'deepseek' in secrets['apis']:
                        api_key = secrets['apis']['deepseek'].get('api_key', '')
                        if api_key:
                            print(f"Using DeepSeek API key from secrets.yaml at {secrets_path}")
                            return api_key
                        else:
                            print(f"DeepSeek API key not found in secrets.yaml at {secrets_path}")
                    else:
                        print(f"Invalid structure in secrets.yaml at {secrets_path}")
            except yaml.YAMLError as e:
                print(f"Error parsing YAML from {secrets_path}: {str(e)}")
            except Exception as e:
                print(f"Error reading secrets file: {str(e)}")

            
    print("DeepSeek API key not found. Please provide it with --api-key or set DEEPSEEK_API_KEY environment variable.")
    return None

def test_reasoner_analysis(api_key, reasoner_model="deepseek-reasoner"):
    """Test DeepSeek Reasoner for structured financial analysis."""
    print(f"\n==== Testing DeepSeek Reasoner Analysis ({reasoner_model}) ====\n")
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    # Sample analysis prompt for Bitcoin
    prompt = """
Analyze Bitcoin (BTC) as a potential investment with the current market conditions.
Current price: $68,500
24h Change: 2.3%

Include your assessment of market sentiment, key factors affecting price, and a short-term price forecast.
"""
    
    try:
        print("Sending analysis request to DeepSeek Reasoner...")
        response = client.chat.completions.create(
            model=reasoner_model,
            messages=[
                {
                    "role": "system", 
                    "content": """You are a financial analyst specialized in cryptocurrency markets.
                    Analyze the provided data and present a structured analysis with clear section headings:
                    
                    SENTIMENT: (Bullish, Neutral, or Bearish)
                    CONFIDENCE: (High, Medium, Low)
                    KEY POINTS:
                    - Point 1
                    - Point 2
                    - Point 3
                    
                    PRICE FORECAST:
                    Short-term (1-2 weeks): Your forecast
                    Medium-term (1-3 months): Your forecast
                    
                    RECOMMENDATION: (BUY, SELL, or HOLD)
                    
                    RISK FACTORS:
                    - Risk 1
                    - Risk 2
                    
                    TRADING STRATEGY:
                    Detailed strategy with entry and exit points.
                    """
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
            # DO NOT include response_format parameter for Reasoner
        )
        
        # Print the raw response for inspection
        print("\nRaw API Response:")
        print(response)
        
        # Extract text response
        analysis_text = response.choices[0].message.content
        
        print("\nAnalysis Content (first 500 chars):")
        print(analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text)
        
        # Check for key sections to validate structure
        expected_sections = ["SENTIMENT", "CONFIDENCE", "KEY POINTS", "PRICE FORECAST", 
                            "RECOMMENDATION", "RISK FACTORS", "TRADING STRATEGY"]
        
        found_sections = []
        for section in expected_sections:
            if section in analysis_text:
                found_sections.append(section)
                
        print(f"\nFound {len(found_sections)}/{len(expected_sections)} expected sections:")
        print(", ".join(found_sections))
        
        if len(found_sections) < len(expected_sections):
            missing = [s for s in expected_sections if s not in found_sections]
            print(f"\nMissing sections: {', '.join(missing)}")
        
        return len(found_sections) > 0  # Success if at least one section is found
            
    except Exception as e:
        print(f"\nError querying DeepSeek Reasoner API: {e}")
        return False

def test_v3_function_calling(api_key, v3_model="deepseek-chat"):
    """Test DeepSeek Chat for function calling based on financial analysis."""
    print(f"\n==== Testing DeepSeek Chat Function Calling ({v3_model}) ====\n")
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    # Sample analysis data that would come from Reasoner
    sample_analysis = """
SENTIMENT: Bullish
CONFIDENCE: Medium

KEY POINTS:
- Bitcoin is seeing increased institutional adoption
- Technical indicators suggest a potential breakout
- Market sentiment is recovering after recent correction

PRICE FORECAST:
Short-term (1-2 weeks): Likely to test $70,000 resistance level
Medium-term (1-3 months): Potential for new all-time highs if current support holds

RECOMMENDATION: BUY

RISK FACTORS:
- Regulatory uncertainty in major markets
- Potential macroeconomic headwinds
- Technical resistance could lead to short-term rejection

TRADING STRATEGY:
Consider accumulating Bitcoin at current levels with a target of $70,000 for short-term
and $75,000 for medium-term. Set stop-loss at $62,000 to manage downside risk.
"""
    
    # Define the tools for function calling
    tools = [
        {
            "type": "function",
            "function": {
                "name": "place_market_order",
                "description": "Execute a market order for asset trading",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "The asset symbol (e.g., BTC, ETH)"},
                        "action": {"type": "string", "enum": ["buy", "sell", "hold"], "description": "Trading action to take"},
                        "allocation_percentage": {"type": "number", "description": "Percentage of portfolio AUM to allocate (1-15%)"},
                        "confidence": {"type": "string", "enum": ["high", "medium", "low"], "description": "Confidence level in the decision"},
                        "reason": {"type": "string", "description": "Rationale for the trading decision"}
                    },
                    "required": ["symbol", "action", "confidence", "reason"]
                }
            }
        }
    ]
    
    try:
        print("Sending function calling request to DeepSeek Chat...")
        
        # Construct message for Chat model
        messages = [
            {
                "role": "system",
                "content": """You are a trading executor that converts financial analysis into concrete trading actions.
                Based on the analysis provided, determine whether to buy, sell, or hold the asset.
                For buy/sell decisions, determine an appropriate portfolio allocation percentage based on confidence level:
                - High confidence: Consider larger allocations (10-15% of portfolio)
                - Medium confidence: Consider moderate allocations (5-8% of portfolio)
                - Low confidence: Consider smaller allocations (1-3% of portfolio) or holding
                
                Always provide a clear rationale for your decision.
                """
            },
            {
                "role": "user",
                "content": f"""
                Asset: BTC
                Current price: $68,500
                
                Analysis:
                {sample_analysis}
                
                Based on this analysis, determine whether to buy, sell, or hold BTC, and if buying or selling, 
                determine an appropriate portfolio allocation percentage. Call the place_market_order function with your decision.
                """
            }
        ]
        
        # Call Chat model with function calling
        response = client.chat.completions.create(
            model=v3_model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=500
        )
        
        # Print the raw response for inspection
        print("\nRaw API Response:")
        print(response)
        
        # Check if there's a function call in the response
        if not response.choices[0].message.tool_calls:
            print("\nWarning: No function calls in the response!")
            print("Model Content:", response.choices[0].message.content)
            return False
        
        # Extract function call
        function_call = response.choices[0].message.tool_calls[0]
        function_name = function_call.function.name
        
        print(f"\nFunction Called: {function_name}")
        
        try:
            function_args = json.loads(function_call.function.arguments)
            print(f"\nFunction Arguments:")
            print(json.dumps(function_args, indent=2))
            
            # Validate required fields
            required_fields = ["symbol", "action", "confidence", "reason"]
            missing_fields = [field for field in required_fields if field not in function_args]
            
            if missing_fields:
                print(f"\nWarning: Missing required fields: {', '.join(missing_fields)}")
            else:
                print("\nAll required fields present!")
                
            # Check if allocation_percentage is present for buy/sell
            if function_args.get("action") in ["buy", "sell"] and "allocation_percentage" not in function_args:
                print("\nWarning: 'allocation_percentage' not specified for buy/sell action")
            elif function_args.get("action") in ["buy", "sell"]:
                print(f"\nAllocation Percentage: {function_args.get('allocation_percentage')}%")
                
            return True
            
        except json.JSONDecodeError as e:
            print(f"\nError: Failed to parse function arguments: {e}")
            print("Raw arguments:", function_call.function.arguments)
            return False
            
    except Exception as e:
        print(f"\nError with DeepSeek Chat function calling: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test DeepSeek API Integration")
    parser.add_argument("--api-key", type=str, help="DeepSeek API Key")
    parser.add_argument("--reasoner-model", type=str, default="deepseek-reasoner", help="DeepSeek Reasoner model name")
    parser.add_argument("--chat-model", type=str, default="deepseek-chat", help="DeepSeek Chat model name")
    parser.add_argument("--test-reasoner", action="store_true", help="Test Reasoner Analysis")
    parser.add_argument("--test-chat", action="store_true", help="Test Chat Function Calling")
    
    args = parser.parse_args()
    
    # Get API key from args or load from config
    api_key = args.api_key or load_api_key()
    
    if not api_key:
        sys.exit(1)
    
    # If no specific test is selected, run both
    run_reasoner = args.test_reasoner or not (args.test_reasoner or args.test_chat)
    run_chat = args.test_chat or not (args.test_reasoner or args.test_chat)
    
    success = True
    
    if run_reasoner:
        reasoner_success = test_reasoner_analysis(api_key, args.reasoner_model)
        success = success and reasoner_success
    
    if run_chat:
        chat_success = test_v3_function_calling(api_key, args.chat_model)
        success = success and chat_success
    
    if success:
        print("\n✅ All tests passed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()