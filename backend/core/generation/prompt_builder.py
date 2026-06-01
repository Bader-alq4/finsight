# Formats retrieved chunks into a structured prompt for GPT-4o-mini
# Builds numbered source citations with company, filing, and section metadata
# Enforces strict grounding rules to prevent hallucination
# Includes token budgeting to stay within model context limits

def build_prompt(query, chunks):
    context = ""
    for i, chunk in enumerate(chunks):
        context += f"""
[Source {i+1}]
Company: {chunk['company_name']} ({chunk['ticker']})
Filing: {chunk['document_type']} {chunk['fiscal_year']}
Section: {chunk['section_label']}
Content: {chunk['content']}
---
"""

    system_prompt = """You are a financial document analyst specializing in SEC filings.

STRICT RULES:
1. Answer ONLY using the provided sources below
2. Cite every single claim using [Source N] notation
3. Include company name, filing type, year and section for key claims
4. If information is not in the sources say exactly: "This information is not available in the provided filings"
5. Never make up numbers, dates, or facts
6. For comparative questions structure your answer to directly contrast the companies
7. For temporal questions explicitly compare language across years"""

    user_prompt = f"""Sources:
{context}

Question: {query}

Answer with citations for every claim:"""

    return system_prompt, user_prompt

def count_tokens(text):
    import tiktoken
    encoder = tiktoken.get_encoding("cl100k_base")
    return len(encoder.encode(text))

def build_prompt_safe(query, chunks, max_context_tokens=6000):
    filtered_chunks = []
    total_tokens = 0

    for chunk in chunks:
        chunk_tokens = count_tokens(chunk['content'])
        if total_tokens + chunk_tokens > max_context_tokens:
            break
        filtered_chunks.append(chunk)
        total_tokens += chunk_tokens

    return build_prompt(query, filtered_chunks)