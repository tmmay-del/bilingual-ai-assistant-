import os
import struct
import pyaudio
import pvporcupine
import sounddevice as sd
from scipy.io.wavfile import write
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
porcupine_key = os.getenv("PICOVOICE_ACCESS_KEY")

def wait_for_wake_word():
    """Listens for the wake word (e.g., 'Jarvis') efficiently."""
    print("💤 Doll is sleeping... Say 'Jarvis' to wake me up.")
    
    try:
        porcupine = pvporcupine.create(access_key=porcupine_key, keywords=['jarvis'])
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print(" Wake Word Detected!")
                audio_stream.close()
                pa.terminate()
                porcupine.delete()
                return True
    except Exception as e:
        print(f"Wake Word Error: {e}")
        return False

def listen_and_transcribe():
    """Records audio and sends it to Groq Whisper."""
    fs = 44100
    seconds = 5
    filename = "input.wav"

    print("🎤 Listening...")
    my_recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
    sd.wait()
    write(filename, fs, my_recording)
    
    with open(filename, "rb") as file:
        try:
            transcription = client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="whisper-large-v3",
                response_format="json"
            )
            return transcription.text
        except Exception as e:
            print(f"Transcription Error: {e}")
            return None
        
if __name__ == "__main__":
    print("--- 🤖 System Starting ---")
    
    while True:
        if wait_for_wake_word():
            
            user_text = listen_and_transcribe()
            
            if user_text:
                print(f"👂 You said: {user_text}")
            
            print("💤 Going back to sleep...")