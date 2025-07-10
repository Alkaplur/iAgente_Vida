from dotenv import load_dotenv
import os

load_dotenv()

from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a three sentence bedtime story about a unicorn."}
    ]
)

print(response.choices[0].message.content)
