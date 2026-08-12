from google import genai
from src.config.settings import ( 
    GEMINI_API_KEYS,
    EMBEDDING_MODEL,
    GEMINI_MODEL,
)
def embedding_call(chunks:list[str]):
    
    text = [ chunk['text'] for chunk in chunks]
    
    client = genai.Client(
        api_key=GEMINI_API_KEYS[0]
    )
    
    response =  client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text
    )
    
    client.close()
    
    return [
        content.values 
        for content  in response.embeddings 
    ]
    
def text_call(user_prompt,gemini_model=GEMINI_MODEL):
    client = genai.Client(api_key=GEMINI_API_KEYS[0])
    
    response = client.models.generate_content(
        model= gemini_model,
        contents=user_prompt
    )
    
    client.close()
    
    return response.text
    
    
if __name__ == "__main__":

    print("READY\n" + "=" * 20)

    # 1. Test Data for Embeddings
    mock_chunks = [
        {
            "id": 1,
            "text": "Artificial intelligence is transforming technology."
        },
        {
            "id": 2,
            "text": "Python is a versatile programming language."
        }
    ]

    # 2. Test Embedding Call
    print("Testing embedding_call()...")

    embed_response = embedding_call(mock_chunks)

    # Verify response structure
    for i, vector in enumerate(embed_response):

        print(
            f"-> Chunk {i + 1} vector length: "
            f"{len(vector)}"
        )

        print(
            f"-> Sample values: "
            f"{vector[:3]}..."
        )

    print("-" * 20)

    # 3. Test Text Generation Call
    print("Testing text_call()...")

    test_prompt = (
        "Write a one-sentence greeting to a developer."
    )

    text_response = text_call(test_prompt)

    print(
        f"-> Prompt: '{test_prompt}'"
    )

    print(
        f"-> Response: {text_response.strip()}"
    )