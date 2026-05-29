from agent import StartupAgent
from context_manager import add_message

agent = StartupAgent()

print("\n🚀 BizRadar AI Started")
print("Type 'exit' to quit.\n")

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

