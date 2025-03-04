# analysis_engine

Analysis Engine Module

This module uses DeepSeek R1 to analyze YouTube transcripts and price data,
then uses DeepSeek V3 to generate trading decisions through function calling.

**Module Path:** `analysis_engine`

## Table of Contents

### Classes

- [AnalysisEngine](#analysisengine)

## Classes

### AnalysisEngine

Analyzes data and generates investment recommendations.

#### Methods

##### `__init__(config_path, assets_path, narratives_path, transcripts_path, prices_path, output_path=None)`

Initialize the AnalysisEngine.

Args:
    config_path: Path to settings.yaml
    assets_path: Path to assets.yaml
    narratives_path: Path to narratives.yaml
    transcripts_path: Path to transcripts directory
    prices_path: Path to prices directory
    output_path: Path to store analysis results (default: prices_path/analysis)

**Type Hints:**

- **config_path**: `str`
- **assets_path**: `str`
- **narratives_path**: `str`
- **transcripts_path**: `str`
- **prices_path**: `str`
- **output_path**: `str`

##### `_load_yaml(file_path)`

Load YAML configuration file.

**Type Hints:**

- **file_path**: `str`
- **returns**: `Dict[str, Any]`

##### `_merge_dicts(dict1, dict2)`

Recursively merge dict2 into dict1

##### `_load_transcripts(max_age_days=30)`

Load transcripts from storage.

Args:
    max_age_days: Maximum age of transcripts to load
    
Returns:
    List of transcript data with metadata

**Type Hints:**

- **max_age_days**: `int`
- **returns**: `List[Dict[str, Any]]`

##### `_load_price_data(symbol)`

Load latest price data for a symbol.

Args:
    symbol: Asset symbol
    
Returns:
    Dictionary with current and historical price data

**Type Hints:**

- **symbol**: `str`
- **returns**: `Dict[str, Any]`

##### `_extract_relevant_transcript_content(transcripts, symbol, asset_info)`

Extract content from transcripts that's relevant to a specific asset.

Args:
    transcripts: List of transcript data
    symbol: Asset symbol to filter for
    asset_info: Asset information from config
    
Returns:
    String with relevant transcript content

**Type Hints:**

- **transcripts**: `List[Dict[str, Any]]`
- **symbol**: `str`
- **asset_info**: `Dict[str, Any]`
- **returns**: `str`

##### `_query_deepseek_r1(prompt)`

Send a prompt to DeepSeek R1 and get the structured analysis response.

Args:
    prompt: Prompt to send to DeepSeek
    
Returns:
    Structured analysis data or None if the request fails

**Type Hints:**

- **prompt**: `str`
- **returns**: `Optional[Dict[str, Any]]`

##### `_dummy_query_deepseek_r1(prompt)`

Dummy implementation of DeepSeek R1 API for fallback.

Args:
    prompt: Prompt that would be sent to DeepSeek
    
Returns:
    Dummy structured analysis based on asset symbol

**Type Hints:**

- **prompt**: `str`
- **returns**: `Dict[str, Any]`

##### `_process_analysis_with_v3(analysis_data, symbol, current_price)`

Process the analysis using DeepSeek V3 for function calling.

Args:
    analysis_data: The structured analysis from DeepSeek R1
    symbol: The asset symbol
    current_price: Current price of the asset
    
Returns:
    Function call result with trading decision

**Type Hints:**

- **analysis_data**: `Dict[str, Any]`
- **symbol**: `str`
- **current_price**: `float`
- **returns**: `Dict[str, Any]`

##### `_dummy_process_analysis(analysis_data, symbol, current_price)`

Dummy implementation for function calling based on analysis.

Args:
    analysis_data: The structured analysis
    symbol: The asset symbol
    current_price: Current price of the asset
    
Returns:
    Dummy function call result

**Type Hints:**

- **analysis_data**: `Dict[str, Any]`
- **symbol**: `str`
- **current_price**: `float`
- **returns**: `Dict[str, Any]`

##### `analyze_asset(symbol)`

Analyze a single asset using available data, then generate trading decisions.

Args:
    symbol: Asset symbol to analyze
    
Returns:
    Analysis results dictionary with trading decision

**Type Hints:**

- **symbol**: `str`
- **returns**: `Dict[str, Any]`

##### `_save_analysis(symbol, analysis)`

Save analysis results to storage.

Args:
    symbol: Asset symbol
    analysis: Analysis data to save
    
Returns:
    True if saved successfully, False otherwise

**Type Hints:**

- **symbol**: `str`
- **analysis**: `Dict[str, Any]`
- **returns**: `bool`

##### `analyze_all_crypto()`

Analyze all cryptocurrencies in the assets config.

Returns:
    Dictionary of symbol -> analysis results

**Type Hints:**

- **returns**: `Dict[str, Dict[str, Any]]`

##### `get_latest_recommendation(symbol)`

Get the most recent analysis for a symbol.

Args:
    symbol: Asset symbol
    
Returns:
    Latest analysis data or None if not found

**Type Hints:**

- **symbol**: `str`
- **returns**: `Optional[Dict[str, Any]]`

##### `extract_trade_signals(analysis)`

Extract actionable trade signals from an analysis.

Args:
    analysis: Analysis data dictionary
    
Returns:
    Dictionary with trade signal information

**Type Hints:**

- **analysis**: `Dict[str, Any]`
- **returns**: `Dict[str, Any]`

