import environments
from langchain_openai import ChatOpenAI

configure = {
    "model": "gpt-4o-2024-11-20",
    "base_url": "https://vip.apiyi.com/v1"
}

llm = ChatOpenAI(**configure)
