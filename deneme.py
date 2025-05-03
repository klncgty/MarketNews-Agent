from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
import requests
import xml.etree.ElementTree as ET
import json
import time
from datetime import datetime, timedelta
from litellm import RateLimitError
from litellm import completion
from pydantic import BaseModel

# Çıktıyı yapılandırmak için model tanımı
class MarketDecision(BaseModel):
    decision: str  # Beklenen değer "buy" veya "sell"

# LLM oluşturuluyor; response_format ile çıktının MarketDecision modeline parse edilmesi sağlanıyor.
llm = LLM(
    model="groq/llama3-8b-8192",
    api_key="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",
    response_format=MarketDecision
)

source_names = {
    "https://news.google.com/rss/search?q=crypto": "Google News",
    "https://www.coindesk.com/arc/outboundfeeds/rss/": "CoinDesk",
    "https://cointelegraph.com/rss": "Cointelegraph"
}

@tool("Fetch Crypto News")
def fetchNews(action_input: dict = None):
    # Eğer boş input gelirse varsayılan olarak boş sözlük kullan
    if action_input is None:
        action_input = {}
    news_sources = list(source_names.keys())
    collectedNews = []
    max_news = 15  # En fazla 15 haber
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

# Ajan tanımı: Hem veri toplayan hem de piyasa analizi yapacak
collector_agent = Agent(
    role="Data Collector and Market Analyst",
    goal="Son 24 saatteki kripto haberlerini toplayıp, bu haberlere dayanarak piyasaya yönelik 'buy' veya 'sell' önerisi oluşturmak.",
    backstory="Sen, kripto piyasasındaki haberleri detaylı analiz eden ve piyasa trendlerine göre stratejik kararlar üreten deneyimli bir finansal analistsin.",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    max_iter=2  # Tek bir deneme ile sınırlı
)

# Task tanımı: Haber listesini LLM'e verip, analiz sonucunda tek cümlelik piyasa kararı elde etmek
news_task = Task(
    description=(
        "Aşağıdaki JSON formatındaki haberleri analiz ederek piyasanın genel ruh haline dayanarak 'buy' veya 'sell' kararı ver. "
        "Cevabın tek bir cümle olarak, sadece {'decision': 'buy'} veya {'decision': 'sell'} formatında olmalıdır.\n\n"
        "Haberler: {news}"
    ),
    agent=collector_agent,
    expected_output="Tek bir cümle olacak ve 'buy' veya 'sell' kararı içeren JSON formatında cevap vereceksin.",
    tools=[fetchNews]
)

# Crew oluşturuluyor
crew = Crew(
    agents=[collector_agent],
    tasks=[news_task]
)

# Crew'u çalıştırma
try:
    news_results = crew.kickoff()
    print("Son 24 Saatteki Toplanan Haberler ve Analiz Sonucu:", news_results)
except RateLimitError as e:
    print(f"Rate limit hatası: {e}. 60 saniye bekleniyor...")
    time.sleep(60)
    news_results = crew.kickoff()
    print("Son 24 Saatteki Toplanan Haberler ve Analiz Sonucu:", news_results)
