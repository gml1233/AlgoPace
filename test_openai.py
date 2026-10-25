from openai import OpenAI

client = OpenAI(
    base_url="https://api.jiekou.ai/openai",
    api_key="sk_Sj24uPRx3d_Q3KU1SQ6ldLmG_w54xXhzZsHE31vFRos"
)

response = client.chat.completions.create(
    model="gemini-3.1-pro-preview",
    messages=[{"role": "user", "content": "你是什么模型"}]
)

print(response.choices[0].message.content)
