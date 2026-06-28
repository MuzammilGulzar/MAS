def evaluate_communication(transcript: str):
    """
    Basic communication analysis.
    """

    words = transcript.split()

    word_count = len(words)

    return {
        "clarity": 8,
        "confidence": 8,
        "fluency": 8,
        "word_count": word_count
    }