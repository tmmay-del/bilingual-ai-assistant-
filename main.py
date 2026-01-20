import os
import struct
import time
import pyaudio
import pvporcupine
import pygame 
import sounddevice as sd
from scipy.io.wavfile import write
from dotenv import load_dotenv

# Import your modules
import brain
import mouth

load_dotenv()

# --- CONFIGURATION ---
WAKE_WORD = "jarvis"
ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")

def record_command(filename="input.wav", duration=5, fs=44100):
    print("\n🎤 Listening for command... (Speak now!)")
    try:
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        write(filename, fs, recording)
        print("✅ Command recorded.")
        return True
    except Exception as e:
        print(f"❌ Recording Error: {e}")
        return False

def play_audio_with_interruption(file_path, porcupine, audio_stream):
    """Plays audio but stops immediately if Wake Word is detected."""
    print(f"▶️ Playing Answer (Say '{WAKE_WORD}' to interrupt)...")
    
    if not os.path.exists(file_path):
        return False

    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

    interrupted = False

    # LOOP: Check Mic while Audio plays
    while pygame.mixer.music.get_busy():
        # 1. Read Mic Data
        pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
        
        # 2. Check for Wake Word
        keyword_index = porcupine.process(pcm)
        
        if keyword_index >= 0:
            print(f"\n⚡ INTERRUPTED! ({WAKE_WORD.upper()} detected)")
            pygame.mixer.music.stop()
            interrupted = True
            break # Stop loop
        
        pygame.time.Clock().tick(10) # Small delay to save CPU

    pygame.mixer.quit()
    return interrupted

def main():
    print(f"\n--- 🦅 SYSTEM ONLINE: Waiting for '{WAKE_WORD}' ---")
    
    if not ACCESS_KEY:
        print("❌ CRITICAL: PICOVOICE_ACCESS_KEY missing in .env!")
        return

    # 1. Initialize Porcupine
    try:
        porcupine = pvporcupine.create(access_key=ACCESS_KEY, keywords=[WAKE_WORD])
    except Exception as e:
        print(f"❌ Porcupine Error: {e}")
        return

    # 2. Setup Mic Stream (Persistent)
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    try:
        while True:
            # A. Wait for Wake Word (Idle Mode)
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)

            # B. Triggered!
            if keyword_index >= 0:
                print(f"\n⚡ {WAKE_WORD.upper()} DETECTED!")
                
                # LOOP: Conversation Mode
                while True:
                    # 1. Record
                    if record_command("input.wav"):
                        
                        # 2. Transcribe
                        user_text = brain.transcribe_audio("input.wav")
                        
                        if user_text:
                            print(f"📝 You said: '{user_text}'")
                            
                            # 3. Think
                            ai_reply = brain.get_smart_answer(user_text)
                            print(f"🤖 AI: {ai_reply}")
                            
                            # 4. Speak (With Interruption Check)
                            audio_file = mouth.generate_response(ai_reply)
                            was_interrupted = play_audio_with_interruption(audio_file, porcupine, audio_stream)
                            
                            if was_interrupted:
                                print("🔄 Restarting recording immediately...")
                                continue 
                            else:
                                print("💤 Conversation done. Waiting for wake word...")
                                break 
                        else:
                            print("❌ No voice detected.")
                            break

    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    finally:
        if audio_stream: audio_stream.close()
        if pa: pa.terminate()
        porcupine.delete()

if __name__ == "__main__":
    main()