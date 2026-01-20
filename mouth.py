import os
import asyncio
import edge_tts

# Voice Config: "Bashkar" is best for Benglish
VOICE = "bn-IN-BashkarNeural"

def generate_response(text):
    """Generates the MP3 file but does NOT play it. Returns filename."""
    print(f"🗣️ Generating audio for: '{text[:30]}...'")
    output_file = "reply.mp3"

    async def _gen():
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(output_file)

    try:
        # Run the async generator
        asyncio.run(_gen())
        return output_file
    except Exception as e:
        print(f"❌ Mouth Error: {e}")
        return None

# Test Block
if __name__ == "__main__":
    print("Testing Audio Generation...")
    file = generate_response("Hello, this is a test of the barge-in system.")
    if file:
        print(f"✅ Success! File saved at: {file}")
    else:
        print("❌ Failed to generate audio.")