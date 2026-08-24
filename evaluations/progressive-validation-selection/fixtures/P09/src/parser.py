def parse_record(text: str) -> tuple[str, str]:
    left, right = text.split(":")
    if not right.strip():
        raise ValueError("record value is required")
    return left.strip(), right.strip()
