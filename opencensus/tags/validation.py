def is_legal_chars(value):
    return all(32 <= ord(char) <= 126 for char in value)
