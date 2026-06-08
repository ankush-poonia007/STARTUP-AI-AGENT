"""
app.py starts
↓
User asked about document upload
↓
User provides pitch_deck.pdf path
↓
ingest_pdf() called → flat chunks list returned
↓
embed_and_store() called → vectors stored in ChromaDB
↓
While True loop starts
↓
User asks "What is the revenue projection in my pitch deck?"
↓
agent.py receives message
↓
LLM decides to call search_documents
because user explicitly referenced their document
↓
search_documents calls query_rag()
↓
query_rag converts question to vector via Gemini
↓
ChromaDB returns top 5 relevant chunks via cosine similarity
↓
search_documents returns chunks to agent
↓
LLM generates final grounded answer from retrieved chunks
↓
No hallucination — answer comes only from the document

"""

from agent import StartupAgent
from context_manager import add_message
from rag import (
    ingest_pdf,
    embed_and_store
)
agent = StartupAgent()

print("\n🚀 BizRadar AI Started")
print("Type 'exit' to quit.\n")

file_choice = input("Do you have a document to upload? ( YES / NO ) :\t").lower().strip()

if "yes" == file_choice:
    file_path = input("Enter Your File Path : \t ").strip()
    file_chunks = ingest_pdf(file_path=file_path)
    
    response = embed_and_store(file_chunks)
    print(response)
else:
    print("You have not selected any files")
    
    
while True:

    user_input = input("You: ").strip()

    if not user_input:
        continue
    
    if user_input.lower() == "exit":
        print("\n👋 Exiting BizRadar AI...")
        break

    # Store user message
    add_message("user", user_input)

    try:
        # Generate AI response
        print("\n🤖 Thinking...\n")

        response = agent.run(user_input)

        # Store assistant response
        add_message("assistant", response)

        # Display response
        print("\n📊 BizRadar AI:\n")
        print(response)

    except Exception as e:
        print("\n❌ Error:")
        print(e)

    print("\n" + "=" * 60 + "\n")

