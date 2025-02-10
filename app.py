from flask import Flask, request, jsonify, render_template, send_file
import google.generativeai as genai
from gtts import gTTS
import pyttsx3
import os
import time
from langdetect import detect
from indic_transliteration.sanscript import transliterate

app = Flask(__name__)

# Google Gemini API Key
GENAI_API_KEY = "AIzaSyAOM0Ki0spGjiP3s1dZQ82b3Jb_MXSH__k"  # Replace with your actual API key
genai.configure(api_key=GENAI_API_KEY)

# Initialize TTS Engine
engine = pyttsx3.init()

# Define bot personalities with voices and backstories
bot_personalities = {
    "rude_banker": {
        "description": "A rude banker who hesitates to answer customer queries.",
        "prompt": "You are a rude banker working in a high-stress environment. You answer customers' banking questions but in a short, grumpy, and unhelpful way. Stay in character and do not respond to unrelated topics.",
        "avatar": "banker.png",
        "voice": "male_rude"
    },
    "humble_actor": {
        "description": "A humble actor who loves talking to fans. Name: Dhanush",
        "prompt": "You are a famous but humble actor named Dhanush who enjoys engaging with fans. You answer warmly and enthusiastically. Share stories when asked, and do not respond to unrelated topics.",
        "avatar": "actor.png",
        "voice": "male_humble"
    },
    "byte": {
        "description": "An AI software engineer who provides logical and structured answers.",
        "prompt": "You are an AI software engineer. Answer questions with precise, technical, and informative responses. Do not answer unrelated queries.",
        "avatar": "byte.jpg",
        "voice": "robotic"
    },
    "elara": {
        "description": "A storyteller who helps improve communication skills.",
        "prompt": "You are a storyteller and communication expert. Share thoughtful, well-structured, and expressive answers. Do not respond to unrelated topics.",
        "avatar": "elara.png",
        "voice": "female"
    }
}

@app.route("/")
def select_bot():
    return render_template("select_bot.html", bots=bot_personalities)

@app.route("/chat/<bot_type>")
def chat(bot_type):
    if bot_type not in bot_personalities:
        return redirect(url_for("select_bot"))
    return render_template("chat.html", bot_type=bot_type, bot_info=bot_personalities[bot_type])

@app.route("/chat_api", methods=["POST"])
def chat_api():
    data = request.get_json()
    user_input = data.get("message", "").strip()
    bot_type = data.get("botType", "").strip().lower()

    print("\n--- Received User Input ---")
    print("User Message:", user_input)
    print("Bot Type:", bot_type)
    print("----------------------------------\n")

    if not user_input or bot_type not in bot_personalities:
        return jsonify({"response": "I didn't understand that. Please select a bot first.", "audio": None})

    # Detect language (English, Marathi, or Hindi)
    language = detect(user_input)
    # Convert Marathi/Hindi from Romanized to Devanagari
    if language in ["mr", "hi"]:
        user_input_devanagari = transliterate(user_input, "itrans", "devanagari")
    else:
        user_input_devanagari = user_input  # Keep English input unchanged

    
    # Get bot-specific prompt and voice
    bot_prompt = bot_personalities[bot_type]["prompt"]
    bot_voice = bot_personalities[bot_type]["voice"]
    full_prompt = f"{bot_prompt}\nUser ({language}): {user_input_devanagari}\nBot ({language}): Reply strictly in {language}. Do not use English if the user input is in Marathi or Hindi."
    
    print("\n--- AI Prompt Sent to Gemini ---")
    print(full_prompt)
    print("----------------------------------\n")

    try:
        # Generate AI response using Gemini
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(full_prompt)
        
        print("\n--- Full API Response ---")
        print(response)
        print("--------------------------------\n")
        
        if not hasattr(response, 'text') or not response.text:
            raise ValueError("No text response received from Gemini API")
        
        bot_reply = response.text.strip()
        
        print("\n--- AI Response from Gemini ---")
        print(bot_reply)
        print("--------------------------------\n")
    
    except Exception as e:
        print("\n--- ERROR: Gemini API Request Failed ---")
        print(str(e))
        print("--------------------------------------\n")
        return jsonify({"response": "I'm having trouble processing that request. Please try again later.", "audio": None})
    
    if not bot_reply or "i don't understand" in bot_reply.lower():
        bot_reply = "I am unsure how to respond to that within my expertise."

    # Convert response to speech using gTTS (for both English & Marathi)
    timestamp = str(int(time.time()))
    audio_filename = f"static/response_{timestamp}.mp3"

    # ✅ Apply gTTS for all bots, ensuring Marathi & English speech works correctly
    try:
        tts = gTTS(text=bot_reply, lang="mr" if language == "mr" else "en", slow=False)
        tts.save(audio_filename)
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        audio_filename = None  # Prevents crash if TTS fails

    return jsonify({
        "response": bot_reply,
        "audio": "/" + audio_filename if audio_filename else None,
        "language": language,
        "user_input_display": user_input_devanagari
       })


    return jsonify({"response": bot_reply, "audio": "/" + audio_filename, "language": language})

if __name__ == "__main__":
    app.run(debug=True)
