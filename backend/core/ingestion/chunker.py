# Takes the sections from the parser and splits them into 400-token chunks with 50-token overlap
# We can't embed an entire 100 page filing as one unit so we need smaller pieces that are semantically coherent

import tiktoken

encoder = tiktoken.get_encoding("cl100k_base")

def chunk_sections(sections, chunk_size=400, overlap=50):
    all_chunks = []

    for section in sections:
        tokens = encoder.encode(section["text"])
        start = 0
        chunk_index = 0

        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = encoder.decode(chunk_tokens)

            all_chunks.append({
                "content": chunk_text,
                "section_label": section["section_label"],
                "token_count": len(chunk_tokens),
                "chunk_index": chunk_index
            })

            start += (chunk_size - overlap)
            chunk_index += 1

    return all_chunks