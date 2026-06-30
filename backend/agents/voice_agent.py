import whisper

# Load once when the server starts
model = whisper.load_model("medium")   # Better accuracy than "base" but slower.

def speech_to_text(audio_path: str):
    """
    Convert speech audio to text.
    """

    result = model.transcribe(
        audio_path,
        language="en",      # Interview language
        fp16=False,         # Required for CPU
        temperature=0,      # More stable transcription
        beam_size=5,
        best_of=5
    )

    return result["text"].strip()