import whisper

# Load once when the server starts
model = whisper.load_model("small")   # Better accuracy than "base"

def speech_to_text(audio_path: str):
    """
    Convert speech audio to text.
    """

    result = model.transcribe(
        audio_path,
        language="en",      # Interview language
        fp16=False,         # Required for CPU
        temperature=0       # More stable transcription
    )

    return result["text"].strip()