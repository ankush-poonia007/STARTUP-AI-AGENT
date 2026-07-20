from groq import Groq
from src.config.settings import (
    GROQ_API_KEYS,
    GROQ_MODEL
)

def text_call ( prompt: str):
    client = Groq(api_key=GROQ_API_KEYS[0])
    
    return client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ],
        temperature=0.3,
        max_completion_tokens=4096
    )


if __name__=="__main__":
    print("Done")
    
    print(text_call("What is ai").choices[0].message.content)