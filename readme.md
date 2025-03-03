# AI Portfolio Manager

An intelligent portfolio management system that analyzes YouTube content from financial influencers to inform cryptocurrency and stock trading decisions.

## Overview

This project enables automated portfolio management by:
- Fetching and analyzing transcripts from YouTube financial content creators
- Tracking market prices and trends for configured assets
- Using DeepSeek R1 AI model to generate trading recommendations
- Creating and (optionally) executing trades on exchanges

The system is designed to run on a Raspberry Pi with 8GB RAM and follows an incremental development approach, starting with core features and expanding over time.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Raspberry Pi with 8GB RAM (or any system with enough resources)
- API keys for KuCoin (and eventually IBKR)
- API keys for DeepSeek R1 (and eventually Perplexity)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-portfolio-manager.git
   cd ai-portfolio-manager
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your settings:
   - Update `config/settings.yaml` with your API keys
   - Customize `config/assets.yaml` with your tracked assets
   - Adjust `config/narratives.yaml` with your trading strategies

## ⚙️ Configuration

### Settings (`settings.yaml`)

The main configuration file contains:
- YouTube channels to follow
- API credentials for exchanges and AI services
- System settings (refresh intervals, allocation limits, etc.)

Example:
```yaml
youtube:
  channels:
    - name: "Coin Bureau"
      channel_id: "UCqK_GSMbpiV8spgD3ZGloSw"
      relevance: 9

apis:
  kucoin:
    api_key: "YOUR_KUCOIN_API_KEY"
    api_secret: "YOUR_KUCOIN_API_SECRET"
    api_passphrase: "YOUR_KUCOIN_PASSPHRASE"
    sandbox_mode: true  # Set to false for real trading
```

### Assets (`assets.yaml`)

Define the cryptocurrencies and stocks you want to track:

```yaml
crypto:
  - symbol: BTC
    name: Bitcoin
    exchange: kucoin
    description: "Leading cryptocurrency by market cap"
    tags: [large_cap, store_of_value]
```

### Narratives (`narratives.yaml`)

Define market narratives and trading strategies:

```yaml
narratives:
  - name: ai_adoption
    description: "Growth of AI technology across industries"
    importance: 9
    assets_affected: [NVDA, ETH]
    keywords: [artificial intelligence, machine learning, neural networks]
```

## 🎮 Usage

### Basic Operations

```bash
# Fetch data (YouTube transcripts and price data)
python main.py --fetch

# Run analysis on all cryptocurrencies
python main.py --analyze

# Run analysis on a specific cryptocurrency
python main.py --analyze --symbol BTC

# Generate order recommendations
python main.py --generate

# Print a summary of your portfolio
python main.py --summary

# Place a market buy order
python main.py --buy --symbol BTC --amount 100

# Place a limit buy order
python main.py --buy --symbol BTC --amount 100 --price 55000

# Place a market buy order with confirmation
python main.py --buy --symbol BTC --amount 100 --confirm

# Place a market sell order
python main.py --sell --symbol BTC --amount 100

# Place a limit sell order
python main.py --sell --symbol BTC --amount 100 --price 65000

# Place a market sell order with confirmation
python main.py --sell --symbol BTC --amount 100 --confirm
```

### Running a Complete Cycle

```bash
# Run a full cycle (fetch, analyze, generate orders)
python main.py --cycle

# Run a full cycle and execute orders with confirmation
python main.py --cycle --execute --confirm

# Run a full cycle and execute orders automatically
python main.py --cycle --execute --auto
```

### Scheduled Operation

For automated operation on your Raspberry Pi:

```bash
# Run on a schedule with the default interval from config
python main.py --schedule

# Run on a schedule with a custom interval (e.g., 4 hours)
python main.py --schedule --interval 4
```

### Setting Up as a Service

To run as a background service on your Raspberry Pi, create a systemd service:

1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/portfolio-manager.service
   ```

2. Add the following configuration:
   ```
   [Unit]
   Description=AI Portfolio Manager
   After=network.target

   [Service]
   User=pi
   WorkingDirectory=/home/pi/ai-portfolio-manager
   ExecStart=/usr/bin/python3 /home/pi/ai-portfolio-manager/main.py --schedule
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl enable portfolio-manager.service
   sudo systemctl start portfolio-manager.service
   ```

## 📁 Project Structure

```
ai_portfolio_manager/
├── config/
│   ├── assets.yaml      # Stocks and crypto you follow
│   ├── narratives.yaml  # Trading strategies/narratives
│   └── settings.yaml    # API keys and general settings
├── data/
│   ├── transcripts/     # Stored YouTube transcripts
│   ├── prices/          # Historical price data
│   ├── analysis/        # AI-generated analysis results
│   └── orders/          # Trading orders and history
├── modules/
│   ├── transcript_fetcher.py  # YouTube transcript fetching
│   ├── price_fetcher.py       # Price data retrieval
│   ├── analysis_engine.py     # DeepSeek R1 integration
│   └── order_manager.py       # Order generation and execution
├── main.py                    # Main application entry point
└── requirements.txt           # Python dependencies
```

## 🛣️ Development Roadmap

### Phase 1: Core Infrastructure (Current)
- ✅ YouTube transcript fetching
- ✅ Configuration system
- ✅ Basic KuCoin API integration
- ✅ Simple DeepSeek R1 analysis

### Phase 2: Enhanced Trading
- Portfolio tracking and balancing
- Real API integrations
- Trade execution with proper risk management
- Dollar-cost averaging strategies

### Phase 3: Advanced Features
- Perplexity API integration for research
- IBKR integration for stocks
- Technical indicators and sentiment analysis
- Backtesting framework
- Web dashboard for monitoring

## ⚠️ Disclaimer

This software is for educational purposes only. Trading cryptocurrencies and stocks involves significant risk. Always perform your own research before making investment decisions. The creators of this software are not responsible for any financial losses incurred from its use.

## 📝 License

Copyright (c) 2025 Alexander Isaev - see the LICENSE file for details.