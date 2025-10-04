import re, hashlib

def normalize_text(s: str) -> str:
    s = s or ""
    s = re.sub(r"\s+", " ", s.strip())
    return s

def stable_paragraph_id(text: str, index: int, heading_level: int) -> str:
    # Use a short stable hash from normalized text + level + index for tie-breaker
    norm = normalize_text(text)
    payload = f"{norm}|{heading_level}|{index}"
    h = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:10]
    prefix = f"h{heading_level}" if heading_level>0 else "p"
    return f"{prefix}-{h}"
