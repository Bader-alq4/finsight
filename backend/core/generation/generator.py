# Calls GPT-4o-mini to generate answers grounded in retrieved SEC filing chunks
# Two modes: blocking (for evaluation) and async streaming (for the frontend)
# Temperature=0 ensures deterministic factual responses with no creative deviation

from openai import OpenAI
from backend.config import OPENAI_API_KEY
from backend.core.generation.prompt_builder import build_prompt_safe
import json

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_answer(query, chunks):
    system_prompt, user_prompt = build_prompt_safe(query, chunks)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content

async def generate_answer_stream(query, chunks):
    system_prompt, user_prompt = build_prompt_safe(query, chunks)

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0,
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content