# To install: pip install tavily-python
from tavily import TavilyClient

client = TavilyClient("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")
response = client.crawl(url="https://paris-brest.be", extract_depth="advanced", timeout=180)
print(response)
