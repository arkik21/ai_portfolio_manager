"""
Analysis Engine Module

This module uses DeepSeek R1 to analyze YouTube transcripts and price data
to generate investment recommendations.
"""

import os
import json
import logging
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests

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
        self.deepseek_model = self.config.get('apis', {}).get('deepseek', {}).get('model', 'deepseek-r1-large')
    
    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return {}
    
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
    
    def _query_deepseek(self, prompt: str) -> Optional[str]:
        """
        Send a prompt to DeepSeek R1 and get the response.
        
        Args:
            prompt: Prompt to send to DeepSeek
            
        Returns:
            DeepSeek's response or None if the request fails
        """
        # NOTE: This is a dummy implementation
        # In a real implementation, we would use the DeepSeek API client
        
        logger.info(f"Sending prompt to DeepSeek (length: {len(prompt)} chars)")
        
        # For demonstration, return a dummy response
        if "BTC" in prompt or "Bitcoin" in prompt:
            return """
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
        elif "ETH" in prompt or "Ethereum" in prompt:
            return """
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
        else:
            return """
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

    def analyze_asset(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze a single asset using available data.
        
        Args:
            symbol: Asset symbol to analyze
            
        Returns:
            Analysis results dictionary
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
        
        # Extract relevant content from transcripts
        relevant_content = self._extract_relevant_transcript_content(transcripts, symbol, asset_info)
        
        # Create analysis prompt
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""
You are a professional financial analyst specialized in {asset_type} markets.

Today's date: {current_date}

Asset to analyze: {symbol} ({asset_info.get('name', '')})

Current Price: {price_data.get('current', {}).get('price', 'Unknown')}
24h Change: {price_data.get('current', {}).get('change_24h_percent', 'Unknown')}%

Asset Description: {asset_info.get('description', '')}

Tags: {', '.join(asset_info.get('tags', []))}

You have access to the following information from YouTube financial influencers:

{relevant_content}

Based on the information above, provide an analysis of {symbol} with the following structure:
1. Overall sentiment (Bullish, Neutral, or Bearish) and confidence level (High, Medium, Low)
2. Key points from the influencer content
3. Price forecast for short-term (1-2 weeks) and medium-term (1-3 months)
4. Clear recommendation (BUY, SELL, or HOLD)
5. Risk factors to consider
6. Specific trading strategy with entry/exit points if applicable

Your analysis should be objective and focus only on the information provided.
"""

        # Query DeepSeek with the prompt
        analysis_result = self._query_deepseek(prompt)
        
        if not analysis_result:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "Failed to generate analysis"
            }
        
        # Save analysis result
        result = {
            "symbol": symbol,
            "name": asset_info.get('name', ''),
            "type": asset_type,
            "date": current_date,
            "analysis": analysis_result,
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
            
        analysis_text = analysis.get('analysis', '')
        symbol = analysis.get('symbol', '')
        
        # Extract recommendation
        recommendation = None
        if "BUY" in analysis_text:
            recommendation = "BUY"
        elif "SELL" in analysis_text:
            recommendation = "SELL"
        elif "HOLD" in analysis_text or "ACCUMULATE" in analysis_text:
            recommendation = "HOLD"
        else:
            recommendation = "NONE"
            
        # Extract sentiment
        sentiment = None
        if "Bullish" in analysis_text:
            sentiment = "BULLISH"
        elif "Bearish" in analysis_text:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
            
        # Extract confidence
        confidence = None
        if "Confidence: High" in analysis_text:
            confidence = "HIGH"
        elif "Confidence: Medium" in analysis_text:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
            
        return {
            "symbol": symbol,
            "action": recommendation,
            "sentiment": sentiment,
            "confidence": confidence,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "analysis_id": analysis.get('date', '')
        }

# Example usage
if __name__ == "__main__":
    # This is for testing the module directly
    engine = AnalysisEngine(
        config_path="../config/settings.yaml",
        assets_path="../config/assets.yaml",
        narratives_path="../config/narratives.yaml",
        transcripts_path="../data/transcripts",
        prices_path="../data/prices"
    )
    
    # Analyze BTC
    btc_analysis = engine.analyze_asset("BTC")
    print(f"Analysis for BTC: {btc_analysis.get('status')}")
    
    # Extract trade signal
    signal = engine.extract_trade_signals(btc_analysis)
    print(f"Trade signal: {signal.get('action')} ({signal.get('confidence')})")