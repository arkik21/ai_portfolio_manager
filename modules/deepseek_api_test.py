"""
DeepSeek API Test Script

This script tests the DeepSeek API integration for both R1 analysis and V3 function calling.
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
    
    # Try to load from secrets.yaml
    try:
        # Look for secrets.yaml in the same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(script_dir, "config")
        secrets_path = os.path.join(config_dir, "secrets.yaml")
        
        if not os.path.exists(secrets_path):
            print(f"Secrets file not found at: {secrets_path}")
            # Try one level up
            config_dir = os.path.join(os.path.dirname(script_dir), "config")
            secrets_path = os.path.join(config_dir, "secrets.yaml")
        
        if os.path.exists(secrets_path):
            with open(secrets_path, 'r') as file:
                secrets = yaml.safe_load(file)
                api_key = secrets.get('apis', {}).get('deepseek', {}).get('api_key', '')
                if api_key:
                    print(f"Using DeepSeek API key from secrets.yaml")
                    return api_key
    except Exception as e:
        print(f"Error loading API key from secrets: {e}")
    
    print("DeepSeek API key not found. Please provide it with --api-key or set DEEPSEEK_API_KEY environment variable.")
    return None

def test_r1_analysis(api_key, r1_model="deepseek-r1-large"):
    """Test DeepSeek R1 for structured financial analysis."""
    print(f"\n==== Testing DeepSeek R1 Analysis ({r1_model}) ====\n")
    
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
        print("Sending analysis request to DeepSeek R1...")
        response = client.chat.completions.create(
            model=r1_model,
            messages=[
                {
                    "role": "system", 
                    "content": """You are a financial analyst specialized in cryptocurrency markets.
                    Analyze the given asset and output a structured analysis in this exact JSON format:
                    {
                        "sentiment": "bullish|neutral|bearish",
                        "confidence": "high|medium|low",
                        "key_points": ["point1", "point2", "point3"],
                        "price_forecast": {
                            "short_term": "text forecast for 1-2 weeks",
                            "medium_term": "text forecast for 1-3 months"
                        },
                        "recommendation": "buy|sell|hold"
                    }"""
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        # Print the raw response for inspection
        print("\nRaw API Response:")
        print(response)
        
        # Extract and parse JSON response
        analysis_json = response.choices[0].message.content
        
        print("\nAnalysis Content:")
        print(analysis_json)
        
        # Try to parse the JSON to validate format
        try:
            analysis_data = json.loads(analysis_json)
            print("\nSuccessfully parsed JSON response!")
            print("\nFormatted Analysis:")
            print(json.dumps(analysis_data, indent=2))
            
            # Validate required fields
            required_fields = ["sentiment", "confidence", "key_points", "price_forecast", "recommendation"]
            missing_fields = [field for field in required_fields if field not in analysis_data]
            
            if missing_fields:
                print(f"\nWarning: Missing required fields: {', '.join(missing_fields)}")
            else:
                print("\nAll required fields present!")
                
            return True
            
        except json.JSONDecodeError as e:
            print(f"\nError: Failed to parse JSON from DeepSeek R1: {e}")
            print("The response was not valid JSON.")
            return False
            
    except Exception as e:
        print(f"\nError querying DeepSeek R1 API: {e}")
        return False

def test_v3_function_calling(api_key, v3_model="deepseek-chat"):
    """Test DeepSeek V3 for function calling based on financial analysis."""
    print(f"\n==== Testing DeepSeek V3 Function Calling ({v3_model}) ====\n")
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    # Sample analysis data that would come from R1
    sample_analysis = {
        "sentiment": "bullish",
        "confidence": "medium",
        "key_points": [
            "Bitcoin is seeing increased institutional adoption",
            "Technical indicators suggest a potential breakout",
            "Market sentiment is recovering after recent correction"
        ],
        "price_forecast": {
            "short_term": "Likely to test $70,000 resistance level",
            "medium_term": "Potential for new all-time highs if current support holds"
        },
        "recommendation": "buy"
    }
    
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
        print("Sending function calling request to DeepSeek V3...")
        
        # Construct message for V3 model
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
                
                Analysis data:
                {json.dumps(sample_analysis, indent=2)}
                
                Based on this analysis, determine whether to buy, sell, or hold BTC, and if buying or selling, 
                determine an appropriate portfolio allocation percentage. Call the place_market_order function with your decision.
                """
            }
        ]
        
        # Call V3 model with function calling
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
        print(f"\nError with DeepSeek V3 function calling: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test DeepSeek API Integration")
    parser.add_argument("--api-key", type=str, help="DeepSeek API Key")
    parser.add_argument("--r1-model", type=str, default="deepseek-r1-large", help="DeepSeek R1 model name")
    parser.add_argument("--v3-model", type=str, default="deepseek-chat", help="DeepSeek V3 model name")
    parser.add_argument("--test-r1", action="store_true", help="Test R1 Analysis")
    parser.add_argument("--test-v3", action="store_true", help="Test V3 Function Calling")
    
    args = parser.parse_args()
    
    # Get API key from args or load from config
    api_key = args.api_key or load_api_key()
    
    if not api_key:
        sys.exit(1)
    
    # If no specific test is selected, run both
    run_r1 = args.test_r1 or not (args.test_r1 or args.test_v3)
    run_v3 = args.test_v3 or not (args.test_r1 or args.test_v3)
    
    success = True
    
    if run_r1:
        r1_success = test_r1_analysis(api_key, args.r1_model)
        success = success and r1_success
    
    if run_v3:
        v3_success = test_v3_function_calling(api_key, args.v3_model)
        success = success and v3_success
    
    if success:
        print("\n✅ All tests passed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()