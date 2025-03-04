"""
Analysis Engine Module

This module uses DeepSeek R1 to analyze YouTube transcripts and price data,
then uses DeepSeek V3 to generate trading decisions through function calling.
"""

import os
import json
import logging
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('analysis_engine')

class AnalysisEngine:
    """Analyzes data and generates investment recommendations."""
    
    def __init__(self, config_path: str, assets_path: str, narratives_path: str,
                transcripts_path: str, prices_path: str, output_path: str = None):
        """
        Initialize the AnalysisEngine.
        
        Args:
            config_path: Path to settings.yaml
            assets_path: Path to assets.yaml
            narratives_path: Path to narratives.yaml
            transcripts_path: Path to transcripts directory
            prices_path: Path to prices directory
            output_path: Path to store analysis results (default: prices_path/analysis)
        """
        self.config_path = config_path
        self.assets_path = assets_path
        self.narratives_path = narratives_path
        self.transcripts_path = transcripts_path
        self.prices_path = prices_path
        
        # Set default output path if not provided
        if output_path is None:
            self.output_path = os.path.join(os.path.dirname(prices_path), "analysis")
        else:
            self.output_path = output_path
            
        # Load configurations
        self.config = self._load_yaml(config_path)
        self.assets = self._load_yaml(assets_path)
        self.narratives = self._load_yaml(narratives_path)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_path, exist_ok=True)
        
        # Initialize DeepSeek API credentials
        self.deepseek_api_key = self.config.get('apis', {}).get('deepseek', {}).get('api_key', '')
        self.deepseek_r1_model = self.config.get('apis', {}).get('deepseek', {}).get('model', 'deepseek-r1-large')
        self.deepseek_v3_model = self.config.get('apis', {}).get('deepseek', {}).get('function_model', 'deepseek-chat')
        
        # Initialize DeepSeek clients
        self.analysis_client = None
        self.execution_client = None
        
        if self.deepseek_api_key:
            try:
                # Create client for analysis (R1)
                self.analysis_client = OpenAI(
                    api_key=self.deepseek_api_key,
                    base_url="https://api.deepseek.com"
                )
                
                # Create client for execution (V3)
                self.execution_client = OpenAI(
                    api_key=self.deepseek_api_key,
                    base_url="https://api.deepseek.com"
                )
                
                logger.info("DeepSeek clients initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing DeepSeek clients: {e}")
                logger.error("Falling back to dummy implementation")
    
    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(file_path, 'r') as file:
                config = yaml.safe_load(file) or {}
                
            # Also try to load secrets file if it exists
            secrets_path = os.path.join(os.path.dirname(file_path), "secrets.yaml")
            if os.path.exists(secrets_path):
                try:
                    with open(secrets_path, 'r') as secret_file:
                        secrets = yaml.safe_load(secret_file) or {}
                        
                    # Merge secrets into config (deep merge)
                    self._merge_dicts(config, secrets)
                except Exception as e:
                    logger.error(f"Failed to load secrets from {secrets_path}: {e}")
                    
            return config
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return {}
            
    def _merge_dicts(self, dict1, dict2):
        """
        Recursively merge dict2 into dict1
        """
        for key in dict2:
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                self._merge_dicts(dict1[key], dict2[key])
            else:
                dict1[key] = dict2[key]
    
    def _load_transcripts(self, max_age_days: int = 30) -> List[Dict[str, Any]]:
        """
        Load transcripts from storage.
        
        Args:
            max_age_days: Maximum age of transcripts to load
            
        Returns:
            List of transcript data with metadata
        """
        transcripts = []
        cutoff_date = datetime.now().timestamp() - (max_age_days * 86400)
        
        for filename in os.listdir(self.transcripts_path):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.transcripts_path, filename), 'r') as file:
                        transcript_data = json.load(file)
                        
                        # Parse published_at date and filter by age
                        try:
                            published_at = datetime.fromisoformat(transcript_data['published_at'].replace('Z', '+00:00'))
                            if published_at.timestamp() >= cutoff_date:
                                transcripts.append(transcript_data)
                        except (KeyError, ValueError):
                            # If we can't parse the date, include it anyway
                            transcripts.append(transcript_data)
                            
                except Exception as e:
                    logger.error(f"Error loading transcript {filename}: {e}")
        
        # Sort by published date, newest first
        transcripts.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        return transcripts
    
    def _load_price_data(self, symbol: str) -> Dict[str, Any]:
        """
        Load latest price data for a symbol.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Dictionary with current and historical price data
        """
        result = {
            "current": None,
            "historical": []
        }
        
        # Find the most recent current price file
        current_files = [f for f in os.listdir(self.prices_path) 
                        if f.startswith(f"{symbol}_current_") and f.endswith('.json')]
        if current_files:
            # Get the most recent file based on filename date
            latest_file = sorted(current_files, reverse=True)[0]
            try:
                with open(os.path.join(self.prices_path, latest_file), 'r') as file:
                    result["current"] = json.load(file)
            except Exception as e:
                logger.error(f"Error loading current price data for {symbol}: {e}")
        
        # Find the most recent historical price file
        historical_files = [f for f in os.listdir(self.prices_path) 
                           if f.startswith(f"{symbol}_historical_") and f.endswith('.json')]
        if historical_files:
            # Get the most recent file based on filename date
            latest_file = sorted(historical_files, reverse=True)[0]
            try:
                with open(os.path.join(self.prices_path, latest_file), 'r') as file:
                    result["historical"] = json.load(file)
            except Exception as e:
                logger.error(f"Error loading historical price data for {symbol}: {e}")
        
        return result
    
    def _extract_relevant_transcript_content(self, transcripts: List[Dict[str, Any]], 
                                          symbol: str, asset_info: Dict[str, Any]) -> str:
        """
        Extract content from transcripts that's relevant to a specific asset.
        
        Args:
            transcripts: List of transcript data
            symbol: Asset symbol to filter for
            asset_info: Asset information from config
            
        Returns:
            String with relevant transcript content
        """
        # Get keywords for this asset
        keywords = [symbol.lower(), asset_info.get('name', '').lower()]
        
        # Add keywords from related narratives
        for narrative in self.narratives.get('narratives', []):
            if symbol in narrative.get('assets_affected', []):
                keywords.extend([k.lower() for k in narrative.get('keywords', [])])
        
        # Remove duplicates
        keywords = list(set(keywords))
        
        relevant_segments = []
        
        # Extract relevant segments from transcripts
        for transcript in transcripts:
            video_segments = []
            
            for segment in transcript.get('transcript', []):
                text = segment.get('text', '').lower()
                
                # Check if the segment contains any of the keywords
                if any(keyword in text for keyword in keywords):
                    video_segments.append(segment.get('text', ''))
            
            if video_segments:
                video_info = (
                    f"Video: {transcript.get('title', 'Unknown')}\n"
                    f"Channel: {transcript.get('channel', 'Unknown')}\n"
                    f"Date: {transcript.get('published_at', 'Unknown')}\n\n"
                )
                video_content = "\n".join(video_segments)
                relevant_segments.append(f"{video_info}{video_content}\n\n{'='*50}\n\n")
        
        if not relevant_segments:
            return f"No relevant content found for {symbol} in the transcripts."
        
        return "".join(relevant_segments)
    
    def _query_deepseek_r1(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Send a prompt to DeepSeek R1 and get the structured analysis response.
        
        Args:
            prompt: Prompt to send to DeepSeek
            
        Returns:
            Structured analysis data or None if the request fails
        """
        if not self.analysis_client:
            logger.warning("DeepSeek analysis client not initialized, using dummy implementation")
            return self._dummy_query_deepseek_r1(prompt)
            
        try:
            logger.info(f"Sending prompt to DeepSeek R1 (length: {len(prompt)} chars)")
            
            response = self.analysis_client.chat.completions.create(
                model=self.deepseek_r1_model,
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a professional financial analyst specialized in cryptocurrency and stock markets. 
                        Analyze the provided data and output a structured analysis in this exact JSON format:
                        {
                            "sentiment": "bullish|neutral|bearish",
                            "confidence": "high|medium|low",
                            "key_points": ["point1", "point2", "point3", ...],
                            "price_forecast": {
                                "short_term": "text forecast for 1-2 weeks",
                                "medium_term": "text forecast for 1-3 months"
                            },
                            "recommendation": "buy|sell|hold",
                            "risk_factors": ["risk1", "risk2", "risk3", ...],
                            "trading_strategy": "detailed trading strategy text",
                            "entry_points": [price1, price2, ...],
                            "exit_points": [price1, price2, ...],
                            "analysis_text": "full text analysis with all details"
                        }"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            # Extract and parse JSON response
            analysis_json = response.choices[0].message.content
            
            try:
                analysis_data = json.loads(analysis_json)
                logger.info(f"Successfully parsed JSON response from DeepSeek R1")
                return analysis_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from DeepSeek R1: {e}")
                logger.error(f"Raw response: {analysis_json[:500]}...")
                return self._dummy_query_deepseek_r1(prompt)
            
        except Exception as e:
            logger.error(f"Error querying DeepSeek R1 API: {e}")
            logger.warning("Falling back to dummy implementation")
            return self._dummy_query_deepseek_r1(prompt)
            
    def _dummy_query_deepseek_r1(self, prompt: str) -> Dict[str, Any]:
        """
        Dummy implementation of DeepSeek R1 API for fallback.
        
        Args:
            prompt: Prompt that would be sent to DeepSeek
            
        Returns:
            Dummy structured analysis based on asset symbol
        """
        logger.info(f"Using dummy DeepSeek R1 implementation (prompt length: {len(prompt)} chars)")
        
        # Extract the symbol from the prompt for dummy response
        symbol = None
        if "BTC" in prompt:
            symbol = "BTC"
        elif "ETH" in prompt:
            symbol = "ETH"
        elif "SOL" in prompt:
            symbol = "SOL"
        else:
            # Try to find other common crypto symbols
            for crypto in ["XRP", "ADA", "DOT", "DOGE", "LINK", "XMR", "KAS"]:
                if crypto in prompt:
                    symbol = crypto
                    break
        
        # Generate response based on symbol
        if symbol == "BTC":
            return {
                "sentiment": "bullish",
                "confidence": "high",
                "key_points": [
                    "Strong institutional adoption trend continuing in 2025",
                    "Technical analysis shows support at current levels with resistance at $70,000",
                    "Market narratives around Bitcoin as an inflation hedge remain strong",
                    "Recent regulatory clarity has been generally positive for Bitcoin"
                ],
                "price_forecast": {
                    "short_term": "Likely to test $70,000 resistance level",
                    "medium_term": "Potential for new all-time highs if current support holds"
                },
                "recommendation": "buy",
                "risk_factors": [
                    "Potential regulatory changes in major markets",
                    "Macroeconomic factors affecting risk assets broadly",
                    "Technical resistance at $70,000 could lead to short-term rejection"
                ],
                "trading_strategy": "Accumulate at current prices. Set buy orders at support levels around $64,000-$65,000. Take partial profits at $70,000 and $75,000 levels.",
                "entry_points": [64000, 65000],
                "exit_points": [70000, 75000],
                "analysis_text": """
Analysis for Bitcoin (BTC):

Sentiment: Bullish
Confidence: High

Key Points:
1. Multiple influencers have highlighted the strong institutional adoption trend continuing in 2025.
2. Technical analysis shows support at current levels with resistance at $70,000.
3. Market narratives around Bitcoin as an inflation hedge remain strong.
4. Recent regulatory clarity has been generally positive for Bitcoin.

Price Forecast:
- Short-term (1-2 weeks): Likely to test $70,000 resistance level
- Medium-term (1-3 months): Potential for new all-time highs if current support holds

Recommendation:
ACCUMULATE at current prices. Consider setting buy orders at support levels around $64,000-$65,000. 
Set take-profit orders at $70,000 and $75,000 levels.

Risk Factors:
- Potential regulatory changes in major markets
- Macroeconomic factors affecting risk assets broadly
- Technical resistance at $70,000 could lead to short-term rejection

Trading Strategy:
- Maintain current position
- Consider adding 5-10% to position at support levels
- Take partial profits at resistance levels
"""
            }
        elif symbol == "ETH":
            return {
                "sentiment": "neutral",
                "confidence": "medium",
                "key_points": [
                    "The recent Ethereum upgrade has positive long-term implications",
                    "DeFi activity on Ethereum has been increasing steadily",
                    "Competition from alternative L1s remains a concern for market share",
                    "Technical analysis shows a consolidation pattern forming"
                ],
                "price_forecast": {
                    "short_term": "Likely to remain in the $3300-$3600 range",
                    "medium_term": "Potential upside to $4000+ if broader crypto market remains strong"
                },
                "recommendation": "hold",
                "risk_factors": [
                    "Technical issues with recent upgrade could impact sentiment",
                    "Continued gas fee concerns affecting user experience",
                    "Competition from alternative L1 blockchains"
                ],
                "trading_strategy": "Hold current position. Consider adding on dips below $3200. Set buy orders at $3200 and $3000 levels.",
                "entry_points": [3000, 3200],
                "exit_points": [4000, 4200],
                "analysis_text": """
Analysis for Ethereum (ETH):

Sentiment: Neutral to Bullish
Confidence: Medium

Key Points:
1. The recent Ethereum upgrade has positive long-term implications but short-term impact is uncertain.
2. DeFi activity on Ethereum has been increasing steadily.
3. Competition from alternative L1s remains a concern for market share.
4. Technical analysis shows a consolidation pattern forming.

Price Forecast:
- Short-term (1-2 weeks): Likely to remain in the $3300-$3600 range
- Medium-term (1-3 months): Potential upside to $4000+ if broader crypto market remains strong

Recommendation:
HOLD current position. Consider adding on dips below $3200.

Risk Factors:
- Technical issues with recent upgrade could impact sentiment
- Continued gas fee concerns affecting user experience
- Competition from alternative L1 blockchains

Trading Strategy:
- Maintain current position
- Set buy orders at support levels ($3200, $3000)
- Consider rebalancing if ETH/BTC ratio falls further
"""
            }
        else:
            return {
                "sentiment": "neutral",
                "confidence": "low",
                "key_points": [
                    "Insufficient data to make a strong recommendation",
                    "Market conditions remain uncertain",
                    "Technical indicators are mixed"
                ],
                "price_forecast": {
                    "short_term": "Uncertain short-term outlook",
                    "medium_term": "Direction will depend on broader market conditions"
                },
                "recommendation": "hold",
                "risk_factors": [
                    "High market volatility",
                    "Limited information available",
                    "Uncertain regulatory environment"
                ],
                "trading_strategy": "Hold current position until more data becomes available. Monitor market conditions closely.",
                "entry_points": [],
                "exit_points": [],
                "analysis_text": """
Analysis:

Sentiment: Neutral
Confidence: Low

Key Points:
1. Insufficient data to make a strong recommendation.
2. Market conditions remain uncertain.
3. Technical indicators are mixed.

Recommendation:
HOLD current position until more data becomes available.

Risk Factors:
- High market volatility
- Limited information available

Trading Strategy:
- Wait for more clear signals before taking action
- Monitor market conditions closely
"""
            }

    def _process_analysis_with_v3(self, analysis_data: Dict[str, Any], symbol: str, current_price: float) -> Dict[str, Any]:
        """
        Process the analysis using DeepSeek V3 for function calling.
        
        Args:
            analysis_data: The structured analysis from DeepSeek R1
            symbol: The asset symbol
            current_price: Current price of the asset
            
        Returns:
            Function call result with trading decision
        """
        if not self.execution_client:
            logger.warning("DeepSeek execution client not initialized, using dummy implementation")
            return self._dummy_process_analysis(analysis_data, symbol, current_price)
        
        try:
            logger.info(f"Processing analysis with DeepSeek V3 for {symbol}")
            
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
            
            # Construct message for V3 model
            messages = [
                {
                    "role": "system",
                    "content":                     """You are a trading executor that converts financial analysis into concrete trading actions.
                    Based on the analysis provided, determine whether to buy, sell, or hold the asset.
                    For buy/sell decisions, determine an appropriate portfolio allocation percentage based on confidence level:
                    - High confidence: Consider larger allocations (10-15% of portfolio)
                    - Medium confidence: Consider moderate allocations (5-8% of portfolio)
                    - Low confidence: Consider smaller allocations (1-3% of portfolio) or holding
                    
                    Always provide a clear rationale for your decision. Keep allocation percentages within prudent risk management guidelines.
                    """
                },
                {
                    "role": "user",
                    "content": f"""
                    Asset: {symbol}
                    Current price: ${current_price}
                    
                    Analysis data:
                    {json.dumps(analysis_data, indent=2)}
                    
                    Based on this analysis, determine whether to buy, sell, or hold {symbol}, and if buying or selling, 
                    determine an appropriate USD amount. Call the place_market_order function with your decision.
                    """
                }
            ]
            
            # Call V3 model with function calling
            response = self.execution_client.chat.completions.create(
                model=self.deepseek_v3_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=500
            )
            
            # Check if there's a function call in the response
            if not response.choices[0].message.tool_calls:
                logger.warning(f"No function calls in V3 response for {symbol}")
                return self._dummy_process_analysis(analysis_data, symbol, current_price)
            
            # Extract function call
            function_call = response.choices[0].message.tool_calls[0]
            function_name = function_call.function.name
            
            try:
                function_args = json.loads(function_call.function.arguments)
                logger.info(f"V3 model called {function_name} with args: {function_args}")
                
                # Validate required fields
                if "action" not in function_args or "symbol" not in function_args:
                    logger.warning(f"Missing required fields in function call for {symbol}")
                    return self._dummy_process_analysis(analysis_data, symbol, current_price)
                
                # Ensure allocation_percentage is present for buy/sell actions
                if function_args["action"] in ["buy", "sell"] and "allocation_percentage" not in function_args:
                    # Set default allocation based on confidence
                    if function_args.get("confidence") == "high":
                        function_args["allocation_percentage"] = 10  # 10% default for high confidence
                    elif function_args.get("confidence") == "medium":
                        function_args["allocation_percentage"] = 5   # 5% default for medium confidence
                    else:
                        function_args["allocation_percentage"] = 2   # 2% default for low confidence
                
                return {
                    "function": function_name,
                    "arguments": function_args,
                    "model_response": response.choices[0].message.content
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse function arguments from V3: {e}")
                return self._dummy_process_analysis(analysis_data, symbol, current_price)
                
        except Exception as e:
            logger.error(f"Error processing analysis with DeepSeek V3: {e}")
            logger.warning("Falling back to dummy implementation")
            return self._dummy_process_analysis(analysis_data, symbol, current_price)
    
    def _dummy_process_analysis(self, analysis_data: Dict[str, Any], symbol: str, current_price: float) -> Dict[str, Any]:
        """
        Dummy implementation for function calling based on analysis.
        
        Args:
            analysis_data: The structured analysis
            symbol: The asset symbol
            current_price: Current price of the asset
            
        Returns:
            Dummy function call result
        """
        logger.info(f"Using dummy processing for {symbol} analysis")
        
        # Extract recommendation and confidence
        recommendation = analysis_data.get("recommendation", "hold").lower()
        confidence = analysis_data.get("confidence", "low").lower()
        
        # Determine allocation percentage based on confidence
        allocation_percentage = 0
        if recommendation in ["buy", "sell"]:
            if confidence == "high":
                allocation_percentage = 12  # 12% of portfolio
            elif confidence == "medium":
                allocation_percentage = 6   # 6% of portfolio
            else:  # low
                allocation_percentage = 2   # 2% of portfolio
        
        # Generate reason based on key points
        key_points = analysis_data.get("key_points", [])
        reason = "Based on analysis"
        if key_points and len(key_points) > 0:
            reason = f"Based on: {key_points[0]}"
            if len(key_points) > 1:
                reason += f" and {key_points[1]}"
        
        return {
            "function": "place_market_order",
            "arguments": {
                "symbol": symbol,
                "action": recommendation,
                "allocation_percentage": allocation_percentage,
                "confidence": confidence,
                "reason": reason
            },
            "model_response": "Dummy function call based on analysis"
        }

    def analyze_asset(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze a single asset using available data, then generate trading decisions.
        
        Args:
            symbol: Asset symbol to analyze
            
        Returns:
            Analysis results dictionary with trading decision
        """
        logger.info(f"Analyzing asset: {symbol}")
        
        # Find asset info
        asset_info = {}
        asset_type = None
        
        for asset_category in ['crypto', 'stocks']:
            for asset in self.assets.get(asset_category, []):
                if asset.get('symbol') == symbol:
                    asset_info = asset
                    asset_type = asset_category
                    break
            if asset_info:
                break
                
        if not asset_info:
            logger.error(f"Asset {symbol} not found in configuration")
            return {
                "symbol": symbol,
                "status": "error",
                "message": "Asset not found in configuration"
            }
        
        # Load relevant data
        transcripts = self._load_transcripts()
        price_data = self._load_price_data(symbol)
        
        # Get current price
        current_price = price_data.get('current', {}).get('price', 0.0)
        if not current_price:
            logger.warning(f"No current price data for {symbol}, using default")
            current_price = 1000.0  # Default placeholder
        
        # Extract relevant content from transcripts
        relevant_content = self._extract_relevant_transcript_content(transcripts, symbol, asset_info)
        
        # Create analysis prompt
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""
You are a professional financial analyst specialized in {asset_type} markets.

Today's date: {current_date}

Asset to analyze: {symbol} ({asset_info.get('name', '')})

Current Price: {current_price}
24h Change: {price_data.get('current', {}).get('change_24h_percent', 'Unknown')}%

Asset Description: {asset_info.get('description', '')}

Tags: {', '.join(asset_info.get('tags', []))}

You have access to the following information from YouTube financial influencers:

{relevant_content}

Based on the information above, provide a structured analysis of {symbol} with the following required components:
1. Overall sentiment (Bullish, Neutral, or Bearish) and confidence level (High, Medium, Low)
2. Key points from the influencer content
3. Price forecast for short-term (1-2 weeks) and medium-term (1-3 months)
4. Clear recommendation (BUY, SELL, or HOLD)
5. Risk factors to consider
6. Specific trading strategy with entry/exit points if applicable

Your analysis must be objective and focus only on the information provided.
"""

        # PHASE 1: Query DeepSeek R1 for structured analysis
        analysis_data = self._query_deepseek_r1(prompt)
        
        if not analysis_data:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "Failed to generate analysis"
            }
        
        # PHASE 2: Process analysis with DeepSeek V3 for function calling
        function_call = self._process_analysis_with_v3(analysis_data, symbol, current_price)
        
        # Combine results
        result = {
            "symbol": symbol,
            "name": asset_info.get('name', ''),
            "type": asset_type,
            "date": current_date,
            "current_price": current_price,
            "analysis": analysis_data,
            "trading_decision": function_call.get("arguments", {}),
            "status": "success"
        }
        
        self._save_analysis(symbol, result)
        return result
    
    def _save_analysis(self, symbol: str, analysis: Dict[str, Any]) -> bool:
        """
        Save analysis results to storage.
        
        Args:
            symbol: Asset symbol
            analysis: Analysis data to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            file_path = os.path.join(self.output_path, f"{symbol}_analysis_{date_str}.json")
            
            with open(file_path, 'w') as file:
                json.dump(analysis, file, indent=2)
            
            logger.info(f"Saved analysis for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Error saving analysis for {symbol}: {e}")
            return False
    
    def analyze_all_crypto(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze all cryptocurrencies in the assets config.
        
        Returns:
            Dictionary of symbol -> analysis results
        """
        results = {}
        
        crypto_assets = self.assets.get('crypto', [])
        for asset in crypto_assets:
            symbol = asset.get('symbol')
            if not symbol:
                continue
                
            analysis = self.analyze_asset(symbol)
            results[symbol] = analysis
            
        return results
    
    def get_latest_recommendation(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent analysis for a symbol.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Latest analysis data or None if not found
        """
        analysis_files = [f for f in os.listdir(self.output_path) 
                         if f.startswith(f"{symbol}_analysis_") and f.endswith('.json')]
        
        if not analysis_files:
            return None
            
        # Get the most recent file based on filename date
        latest_file = sorted(analysis_files, reverse=True)[0]
        
        try:
            with open(os.path.join(self.output_path, latest_file), 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading analysis for {symbol}: {e}")
            return None
    
    def extract_trade_signals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract actionable trade signals from an analysis.
        
        Args:
            analysis: Analysis data dictionary
            
        Returns:
            Dictionary with trade signal information
        """
        if analysis.get('status') != 'success':
            return {"action": "NONE", "reason": "Analysis failed"}
        
        # First try to use the trading_decision if available (from V3 function call)
        if 'trading_decision' in analysis and analysis['trading_decision']:
            trading_decision = analysis['trading_decision']
            
            return {
                "symbol": analysis.get('symbol', ''),
                "action": trading_decision.get('action', 'NONE').upper(),
                "sentiment": analysis.get('analysis', {}).get('sentiment', 'NEUTRAL').upper(),
                "confidence": trading_decision.get('confidence', 'LOW').upper(),
                "allocation_percentage": trading_decision.get('allocation_percentage', 0),
                "reason": trading_decision.get('reason', ''),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "analysis_id": analysis.get('date', '')
            }
            
        # Fallback to extracting from the text analysis
        analysis_data = analysis.get('analysis', {})
        
        # Try to get structured data first
        recommendation = analysis_data.get('recommendation', '').upper()
        sentiment = analysis_data.get('sentiment', '').upper()
        confidence = analysis_data.get('confidence', '').upper()
        
        if not recommendation:
            # Extract from analysis_text if structured data not available
            analysis_text = analysis_data.get('analysis_text', '')
            
            # Extract recommendation
            if "BUY" in analysis_text:
                recommendation = "BUY"
            elif "SELL" in analysis_text:
                recommendation = "SELL"
            elif "HOLD" in analysis_text or "ACCUMULATE" in analysis_text:
                recommendation = "HOLD"
            else:
                recommendation = "NONE"
                
            # Extract sentiment
            if "Bullish" in analysis_text:
                sentiment = "BULLISH"
            elif "Bearish" in analysis_text:
                sentiment = "BEARISH"
            else:
                sentiment = "NEUTRAL"
                
            # Extract confidence
            if "Confidence: High" in analysis_text:
                confidence = "HIGH"
            elif "Confidence: Medium" in analysis_text:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"
        
        # Determine allocation percentage based on confidence
        allocation_percentage = 0
        if recommendation in ["BUY", "SELL"]:
            if confidence == "HIGH":
                allocation_percentage = 12  # 12% of portfolio
            elif confidence == "MEDIUM":
                allocation_percentage = 6   # 6% of portfolio
            else:  # LOW
                allocation_percentage = 2   # 2% of portfolio
                
        return {
            "symbol": analysis.get('symbol', ''),
            "action": recommendation,
            "sentiment": sentiment,
            "confidence": confidence,
            "allocation_percentage": allocation_percentage,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "analysis_id": analysis.get('date', '')
        }

# Example usage
if __name__ == "__main__":
    # This is for testing the module directly
    engine = AnalysisEngine(
        config_path="./config/settings.yaml",
        assets_path="./config/assets.yaml",
        narratives_path="./config/narratives.yaml",
        transcripts_path="./data/transcripts",
        prices_path="./data/prices"
    )
    
    # Analyze BTC
    btc_analysis = engine.analyze_asset("BTC")
    print(f"Analysis for BTC: {btc_analysis.get('status')}")
    
    # Extract trade signal
    signal = engine.extract_trade_signals(btc_analysis)
    print(f"Trade signal: {signal.get('action')} ({signal.get('confidence')})")