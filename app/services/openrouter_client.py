import requests
from ..config import OPENROUTER_API_KEY

def query_openrouter(prompt: str, model: str = "deepseek/deepseek-r1-distill-llama-70b:free"):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    res = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
    res.raise_for_status()
    return res.json()
