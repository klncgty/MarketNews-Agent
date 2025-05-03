# CryptoNewsTrader

A Python project that collects the latest cryptocurrency news from RSS feeds (Google News, CoinDesk, Cointelegraph) and analyzes them using an AI agent to provide a "buy" or "sell" market decision.

## Features
- Fetches crypto news from multiple RSS sources.
- Analyzes news sentiment using CrewAI and Grok LLM.
- Outputs a simple JSON decision: {"decision": "buy"} or {"decision": "sell"}.

## Requirements
- Python 3.8+
- Install dependencies: `pip install crewai requests`

## Usage
1. Clone the repo: `git clone [https://github.com/<your-username>/CryptoNewsTrader.git](https://github.com/klncgty/MarketNews-Agent/tree/main)`
2. Set up your Grok API key in the script.
3. Run the script: `python main.py`

## Notes
- Ensure a valid Grok API key is provided.
- Handles rate-limiting with a retry mechanism.

## License
MIT
