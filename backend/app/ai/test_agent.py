from backend.app.ai.agent import assistant

response = assistant.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Build an AI that summarizes YouTube videos."
            }
        ]
    }
)

final_message = response["messages"][-1]
print(final_message.content)