# context_manager.py

conversation_history = []


def add_message(role, content):
    """
    Add a message to conversation memory.
    """

    conversation_history.append({
        "role": role,
        "content": content
    })


def get_context():
    """
    Return latest conversation context.
    """

    return conversation_history[-6:]