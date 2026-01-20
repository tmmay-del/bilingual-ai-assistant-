import os
from groq import Groq
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_CHAIN = [
    "llama-3.3-70b-versatile",
    "qwen-2.5-32b",
    "llama-3.1-8b-instant"
]

pdf_path = r"C:\Users\tm359\OneDrive\Desktop\JARVIS\bilingual-ai-assistant-\WEBEL BOOKLET-1 (1).pdf"
PDF_PAGES = []

def load_memory_smart(path):
    print(f"📖 Indexing memory from {path}...")
    if not os.path.exists(path):
        return []
    
    pages_content = []
    try:
        reader = PdfReader(path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                text = " ".join(text.split())
                pages_content.append(f"[Page {i+1}]: {text}")
        print(f"✅ Indexed {len(pages_content)} pages.")
        return pages_content
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return []

PDF_PAGES = load_memory_smart(pdf_path)

def find_relevant_context(user_query):
    """Finds the SINGLE most relevant page to save tokens."""
    if not PDF_PAGES: return ""
    
    user_words = [w.lower() for w in user_query.split() if len(w) > 3]
    if not user_words: return "" 

    best_page = ""
    max_score = 0
    
    for page in PDF_PAGES:
        score = sum(1 for word in user_words if word in page.lower())
        if score > max_score:
            max_score = score
            best_page = page
            
    if max_score > 0:
        return best_page
    return "" 

def transcribe_audio(filename="input.wav"):
    if not os.path.exists(filename): return None
    with open(filename, "rb") as file:
        try:
            return groq_client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="whisper-large-v3-turbo", 
                response_format="json"
            ).text
        except: return None

def get_smart_answer(user_text):
    relevant_context = find_relevant_context(user_text)
    
    if relevant_context:
        print(f"💡 Found info in PDF (Saving tokens...)")
        context_block = f"--- RELEVANT INFO ---\n{relevant_context}\n--- END INFO ---"
    else:
        print("🌍 Using General Knowledge...")
        context_block = ""

    system_instruction = (
        "You are Animatronic, a helpful AI assistant. "
        "Use the 'RELEVANT INFO' (if provided) to answer. "
        "If the answer isn't there, use your general knowledge. "
        f"{context_block}\n"
        "**LANGUAGE RULE:** Speak in a natural mix of Bengali (Bangla Script) and English."
        "Keep technical terms in English (e.g., 'Fees', 'Course', 'Computer')."
        "Example: 'এই Course-এর Fee হলো 6000 টাকা।'"
    )

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_text}
    ]

    for model_name in MODEL_CHAIN:
        print(f"🧠 Thinking ({model_name})...")
        try:
            completion = groq_client.chat.completions.create(
                messages=messages,
                model=model_name,
            )
            return completion.choices[0].message.content
        
        except Exception as e:
            print(f"⚠️ {model_name} Failed: {e}")
            print("🔄 Switching to next brain...")
            continue 

    return "আমার সবকটি Brain কাজ করছে না। আমি দুঃখিত।"

def save_answer_to_file(answer):
    with open("answer.txt", "w", encoding="utf-8") as f: f.write(answer)