from ollama import chat

response = chat(
    model="llama3.2",
    messages=[
        {
            "role": "user",
            "content": "Classify Google Chrome"
        }
    ]
)

print(response["message"]["content"])