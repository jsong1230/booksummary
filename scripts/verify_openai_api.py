import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
# override=True ensures we pick up the latest file content even if env var exists
load_dotenv(override=True)

def verify_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables.")
        return

    print(f"🔑 API Key found: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {e}")
        return

    print("\n" + "=" * 50)
    print("🧪 Testing Chat Completion (gpt-4o)...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello, say 'API works'!"}],
            max_tokens=10
        )
        print("✅ Chat Completion Success!")
        print(f"   Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Chat Completion Failed: {e}")

    print("\n" + "=" * 50)
    print("🧪 Testing TTS (tts-1-hd)...")
    try:
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice="alloy",
            input="Hello, this is a test."
        )
        # Just check if we got bytes
        content_length = len(response.read())
        print(f"✅ TTS Success! (Received {content_length} bytes)")
    except Exception as e:
        print(f"❌ TTS Failed: {e}")

    print("\n" + "=" * 50)
    print("🧪 Testing Embeddings (text-embedding-3-small)...")
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="Test text"
        )
        print("✅ Embeddings Success!")
    except Exception as e:
        print(f"❌ Embeddings Failed: {e}")
        
    print("\n" + "=" * 50)
    print("🏁 Verification Complete")

if __name__ == "__main__":
    verify_openai()
