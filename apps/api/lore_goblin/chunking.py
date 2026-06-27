import re


def chunk_note(content: str, max_words: int = 180, overlap_words: int = 35) -> list[str]:
    words = re.findall(r"\S+", content.strip())
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(0, end - overlap_words)
    return chunks

