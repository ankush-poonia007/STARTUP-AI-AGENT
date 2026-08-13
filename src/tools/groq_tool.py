from groq import Groq
from src.config.settings import (
    GROQ_API_KEYS,
    GROQ_MODEL
)

def text_call ( prompt: list):
    client = Groq(api_key=GROQ_API_KEYS[0])
    
    return client.chat.completions.create(
        model=GROQ_MODEL,
        messages= prompt,
        temperature=0.3,
        max_completion_tokens=4096
    ).choices[0].message.content


if __name__=="__main__":
    print("Done")
    
    response = text_call("what is LangChain and LangGraph. Can you diffrientiate them on bases of usecase?")
    print(response)