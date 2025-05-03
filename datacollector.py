from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
import requests
import xml.etree.ElementTree as ET
import json
import time
from datetime import datetime, timedelta
from litellm import RateLimitError
from litellm import completion

llm = LLM(model="openrouter/deepseek/deepseek-r1",base_url="https://openrouter.ai/api/v1", api_key="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")

source_names = {
    "https://news.google.com/rss/search?q=crypto": "Google News",
    "https://www.coindesk.com/arc/outboundfeeds/rss/": "CoinDesk",
    "https://cointelegraph.com/rss": "CoinTelegraph"
}

@tool("Fetch Crypto News")
def fetchNews():
    """Son 24 saatteki en son 15 kripto haberini RSS feed'lerinden çeker ve başlık ile kaynağı JSON formatında döndürür."""
    news_sources = list(source_names.keys())
    collectedNews = []
    max_news = 20  
    cutoff_time = datetime.now() - timedelta(hours=24)  # Son 24 saat sınırı

    for url in news_sources:
        source_name = source_names[url]
        response = requests.get(url)
        if response.status_code == 200:
            try:
                root = ET.fromstring(response.text)
                for item in root.findall(".//item"):
                    if len(collectedNews) >= max_news:  
                        break
                    title = item.find("title").text if item.find("title") is not None else "No Title"
                    pub_date_elem = item.find("pubDate")
                    pub_date = pub_date_elem.text if pub_date_elem is not None else None
                    
                    if pub_date:
                        try:
                          
                            pub_date_dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                            if pub_date_dt < cutoff_time:
                                continue
                        except ValueError:
                            continue 
                    
                    collectedNews.append({
                        "title": title,
                        "source": source_name
                    })
            except ET.ParseError:
                continue
        if len(collectedNews) >= max_news:
            break
    
    return json.dumps(collectedNews, indent=4, ensure_ascii=False)



collector_agent = Agent(
    role="Data Collector and Market Analyst",
    goal="Son 24 saatteki kripto haberlerini toplayıp piyasa yorumu (buy/sell) yapmak.",
    backstory="Sen, kripto piyasasındaki son 24 saatteki haberleri analiz ederek alım veya satım önerisi sunan bir piyasa analistisin.",
    verbose=True,  # Adımları görmek için açık bırakıyorum, istersen False yap
    allow_delegation=False,
    llm=llm,
    max_iter=2,
    use_system_prompt = False
)

news_task = Task(
    description="""Kripto haber sitelerinden son 24 saatteki en son 15 haberi çek ve bu haberlere dayanarak piyasa yorumu yap.
    Haber başlıklarını ve kaynaklarını analiz et""",
    agent=collector_agent,
    expected_output="""Son 24 saatteki haberlerde, [belirli faktörler] nedeniyle fiyatların yükselmesi bekleniyor; bu nedenle alım yapmak mantıklı (buy).
            veya
            Son 24 saatteki haberlerde, [belirli faktörler] nedeniyle fiyatların düşeceği öngörülüyor; bu nedenle satım yapmak uygun (sell).""",
    tools=[fetchNews]
)

crew = Crew(
    agents=[collector_agent],
    tasks=[news_task],
    verbose=True,
)

try:
    news_results = crew.kickoff()
    
except RateLimitError as e:
    print(f"Rate limit hatası: {e}. 60 saniye bekleniyor...")
    time.sleep(60)
    news_results = crew.kickoff()
    