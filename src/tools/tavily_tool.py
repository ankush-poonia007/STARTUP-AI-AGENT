from tavily import TavilyClient
from src.config.settings import (
    TAVILY_API_KEY,
    TAVILY_MAX_RESULTS,
)


def ask_tavily(user_query:str, country:str = "global"):
    
    client = TavilyClient(api_key=TAVILY_API_KEY)
    return client.search(
        query=user_query,
        include_answer="advanced",
        search_depth="basic",
        country = country,
        exclude_domains= ["facebook.com","instagram.com","x.com","youtube.com"],
        max_results=TAVILY_MAX_RESULTS
    )["results"]

if __name__ == "__main__":
    
    user_input = input("Enter Your Query : ").strip()
    
    print(ask_tavily(user_query=user_input,country="india"))
    