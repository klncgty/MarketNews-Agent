from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta

# Aracın input şeması: Burada ekstra bir parametreye gerek yoktur, fakat tool dekoratörü input beklediği için dummy tanımlıyoruz.
class FetchNewsInput(BaseModel):
    dummy: str = Field("", description="Dummy argument (unused)")

class FetchNewsTool(BaseTool):
    name: str = "Fetch Crypto News"
    description: str = ("Son 24 saatteki en son 15 kripto haberini RSS feed'lerinden çeker "
                        "ve başlık ile kaynağı JSON formatında döndürür.")
    args_schema: Type[BaseModel] = FetchNewsInput

    def _run(self, dummy: str) -> str:
        source_names = {
            "https://news.google.com/rss/search?q=crypto": "Google News",
            "https://www.coindesk.com/arc/outboundfeeds/rss/": "CoinDesk",
            "https://cointelegraph.com/rss": "Cointelegraph"
        }
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
