import re

# Supported Language Definitions
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "bcp47": "en-IN"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "bcp47": "kn-IN"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "bcp47": "hi-IN"},
    "te": {"name": "Telugu", "native": "తెలుగు", "bcp47": "te-IN"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "bcp47": "ta-IN"},
    "ml": {"name": "Malayalam", "native": "മലയാളം", "bcp47": "ml-IN"}
}

def detect_language(text):
    """
    Detects language based on Unicode script blocks.
    Accurate, fast, and completely offline.
    """
    if not text:
        return "en"

    counts = {
        "kn": len(re.findall(r"[\u0C80-\u0CFF]", text)),
        "hi": len(re.findall(r"[\u0900-\u097F]", text)),
        "te": len(re.findall(r"[\u0C00-\u0C7F]", text)),
        "ta": len(re.findall(r"[\u0B80-\u0BFF]", text)),
        "ml": len(re.findall(r"[\u0D00-\u0D7F]", text)),
    }

    max_lang = max(counts, key=counts.get)
    if counts[max_lang] > 0:
        return max_lang

    return "en"

# Multilingual intent mappings to English for classification
INTENT_TRANSLATIONS = {
    # Kannada
    "kn": [
        (r"(ನನ್ನ|ನಂ)?\s*ಟೋಕನ್\s*(ಯಾವುದು|ಎಷ್ಟು|ಏನು|ಸಂಖ್ಯೆ)", "what is my token"),
        (r"(ಮುಂದೆ|ಮುಂಚೆ)\s*(ಎಷ್ಟು|ಎಷ್ಟು\s*ಜನ|ಜನರಿದ್ದಾರೆ)", "how many people are ahead"),
        (r"(ನನ್ನ\s*)?ಸರದಿ\s*(ಯಾವಾಗ|ಬರುತ್ತದೆ)", "when will my turn come"),
        (r"ಕಾಯುವ\s*ಸಮಯ", "when will my turn come"),
        (r"ಪ್ರಸ್ತುತ\s*(ಸಂಖ್ಯೆ|ಟೋಕನ್|ಯಾರು)", "what is the current number"),
        (r"(ನನಗಾಗಿ|ನನಗೆ)?\s*ಟೋಕನ್\s*(ತೆಗೆದುಕೊಳ್ಳಿ|ಪಡೆಯಿರಿ|ಕೊಡಿ|ಹಾಕಿ|ತೆಗೆದುಕೊ)", "collect a token for me"),
        (r"ಕೌಂಟರ್\s*(\d+)\s*(ಎಲ್ಲಿದೆ|ಯಾವುದು)", r"where is counter \1"),
        (r"(ಕಚೇರಿ|ಆಫೀಸ್|ಶಾಖೆ)\s*(ಯಾವಾಗ\s*ಮುಚ್ಚುತ್ತದೆ|ಸಮಯ|ಯಾವಾಗ\s*ತೆರೆಯುತ್ತದೆ)", "what time does this office close"),
        (r"(ಯಾವ|ಏನು)\s*(ದಾಖಲೆಗಳು|ಡಾಕ್ಯುಮೆಂಟ್|ದಾಖಲೆ)\s*(ಬೇಕು|ತರ್ಬೇಕು)", "what documents do I need"),
        (r"(ಫಾರ್ಮಸಿ|ಔಷಧಾಲಯ|ಮೆಡಿಕಲ್)\s*ಎಲ್ಲಿದೆ", "where is the pharmacy"),
        (r"(ನಿಮ್ಮ|ನಿನ್ನ)?\s*ಹೆಸರೇನು", "what is your name"),
        (r"ಹೇಗಿದ್ದೀರ|ಹೇಗಿದ್ದೀರಿ", "how are you"),
        (r"(ಊಟ\s*ಆಯ್ತಾ|ತಿಂಡಿ\s*ಆಯ್ತಾ|ಊಟ\s*ಮಾಡಿದಿರಾ)", "had your dinner"),
        (r"ಧನ್ಯವಾದಗಳು|ಧನ್ಯವಾದ|ಥ್ಯಾಂಕ್ಸ್", "thank you"),
    ],
    # Hindi
    "hi": [
        (r"(मेरा|मेरी)?\s*टोकन\s*(क्या\s*है|नंबर\s*क्या\s*है|संख्या)", "what is my token"),
        (r"(आगे|सामने)\s*कितने\s*(लोग|व्यक्ति)\s*हैं", "how many people are ahead"),
        (r"(मेरी\s*)?बारी\s*कब\s*आएगी", "when will my turn come"),
        (r"प्रतीक्षा\s*समय|इंतजार\s*कितना", "when will my turn come"),
        (r"वर्तमान\s*(नंबर|टोकन|संख्या|कौन\s*सा)\s*है", "what is the current number"),
        (r"(मेरे\s*लिए)?\s*टोकन\s*(लें|निकालें|दीजिए|बनाएं|प्राप्त\s*करें)", "collect a token for me"),
        (r"काउंटर\s*(\d+)\s*कहाँ\s*है", r"where is counter \1"),
        (r"(कार्यालय|दफ्तर|ऑफिस)\s*(कब\s*बंद\s*होता\s*है|का\s*समय\s*क्या\s*है|खुलता\s*है)", "what time does this office close"),
        (r"(कौन\s*से|क्या)\s*(दस्तावेज|कागजात|डॉक्यूमेंट्स)\s*(चाहिए|लगेंगे)", "what documents do I need"),
        (r"(फार्मेसी|दवा\s*की\s*दुकान|मेडिकल)\s*कहाँ\s*है", "where is the pharmacy"),
        (r"आपका\s*नाम\s*क्या\s*है", "what is your name"),
        (r"आप\s*कैसे\s*हैं|क्या\s*हाल\s*है", "how are you"),
        (r"(खाना\s*खाया|डिनर\s*किया|भोजन\s*किया)", "had your dinner"),
        (r"धन्यवाद|शुक्रिया", "thank you"),
    ],
    # Telugu
    "te": [
        (r"(నా\s*)?టోకెన్\s*(ఏమిటి|ఎంత|నంబర్\s*ఏమిటి)", "what is my token"),
        (r"ముందు\s*ఎంతమంది\s*(ఉన్నారు|ప్రజలు)", "how many people are ahead"),
        (r"నా\s*వంతు\s*ఎప్పుడు\s*(వస్తుంది|ఉంటుంది)", "when will my turn come"),
        (r"ప్రస్తుత\s*(నంబర్|టోకెన్)\s*ఏమిటి", "what is the current number"),
        (r"(నా\s*కోసం)?\s*టోకెన్\s*(తీసుకోండి|ఇవ్వండి|పొందండి)", "collect a token for me"),
        (r"కౌంటర్\s*(\d+)\s*ఎక్కడ\s*ఉంది", r"where is counter \1"),
        (r"(ఆఫీస్|కార్యాలయం)\s*(ఎప్పుడు\s*మూసివేస్తారు|సమయం)", "what time does this office close"),
        (r"(ఏ|ఏమి)\s*(పత్రాలు|డాక్యుమెంట్లు)\s*(కావాలి|తీసుకురావాలి)", "what documents do I need"),
        (r"(ఫార్మసీ|మందుల\s*దుకాణం)\s*ఎక్కడ\s*ఉంది", "where is the pharmacy"),
        (r"మీ\s*పేరు\s*ఏమిటి", "what is your name"),
        (r"మీరు\s*ఎలా\s*ఉన్నారు", "how are you"),
        (r"(భోజనం\s*చేశారా|డిన్నర్\s*చేశారా)", "had your dinner"),
        (r"ధన్యవాదాలు|థాంక్స్", "thank you"),
    ],
    # Tamil
    "ta": [
        (r"(என்|என்னுடைய)?\s*டோக்கன்\s*(என்ன|எண்\s*என்ன)", "what is my token"),
        (r"முன்னால்\s*எத்தனை\s*(பேர்\s*உள்ளனர்|நபர்கள்)", "how many people are ahead"),
        (r"(என்\s*)?முறை\s*எப்போது\s*வரும்", "when will my turn come"),
        (r"தற்போதைய\s*(எண்|டோக்கன்)\s*என்ன", "what is the current number"),
        (r"(எனக்கு|எனக்காக)?\s*டோக்கன்\s*(எடுக்கவும்|கொடுக்கவும்|வாங்கவும்)", "collect a token for me"),
        (r"கவுண்டர்\s*(\d+)\s*எங்கே\s*உள்ளது", r"where is counter \1"),
        (r"(அலுவலகம்|ஆபீஸ்)\s*(எப்போது\s*மூடப்படும்|நேரம்)", "what time does this office close"),
        (r"(என்ன|எந்த)\s*(ஆவணங்கள்|சான்றிதழ்கள்)\s*(தேவை)", "what documents do I need"),
        (r"(மருந்தகம்|பார்மசி)\s*எங்கே\s*உள்ளது", "where is the pharmacy"),
        (r"உங்கள்\s*பெயர்\s*என்ன", "what is your name"),
        (r"எப்படி\s*இருக்கிறீர்கள்", "how are you"),
        (r"(சாப்பிட்டீர்களா|இரவு\s*உணவு\s*சாப்பிட்டீர்களா)", "had your dinner"),
        (r"நன்றி", "thank you"),
    ],
    # Malayalam
    "ml": [
        (r"(എന്റെ|എന്റെ\s*)?ടോക്കൺ\s*(ഏതാണ്|എന്താണ്|നമ്പർ)", "what is my token"),
        (r"മുന്നിൽ\s*എത്ര\s*(പേരുണ്ട്|ആളുകളുണ്ട്)", "how many people are ahead"),
        (r"എന്റെ\s*ഊഴം\s*എപ്പോഴാണ്", "when will my turn come"),
        (r"ഇപ്പോഴത്തെ\s*(നമ്പർ|ടോക്കൺ)\s*ഏതാണ്", "what is the current number"),
        (r"(എനിക്കായി)?\s*ടോക്കൺ\s*(എടുക്കുക|നൽകുക|എടുക്കൂ)", "collect a token for me"),
        (r"കൗണ്ടർ\s*(\d+)\s*എവിടെയാണ്", r"where is counter \1"),
        (r"(ഓഫീസ്|സ്ഥാപനം)\s*(എപ്പോഴാണ്\s*അടയ്ക്കുന്നത്|സമയം)", "what time does this office close"),
        (r"(ഏതൊക്കെ|എന്ത്)\s*(രേഖകൾ|ഡോക്യുമെന്റുകൾ)\s*(ആവശ്യമാണ്|വേണം)", "what documents do I need"),
        (r"(ഫാർമസി|മെഡിക്കൽ\s*ഷോപ്പ്)\s*എവിടെയാണ്", "where is the pharmacy"),
        (r"നിങ്ങളുടെ\s*പേര്\s*എന്താണ്", "what is your name"),
        (r"സുഖമാണോ|എങ്ങനെയുണ്ട്", "how are you"),
        (r"(ഭക്ഷണം\s*കഴിച്ചോ|അത്താഴം\s*കഴിച്ചോ)", "had your dinner"),
        (r"നന്ദി", "thank you"),
    ]
}

def normalize_to_english(text, detected_lang):
    """
    Translates known regional phrases to standard English queries for intent analysis.
    """
    if detected_lang == "en" or detected_lang not in INTENT_TRANSLATIONS:
        return text

    patterns = INTENT_TRANSLATIONS[detected_lang]
    for pattern, replacement in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text

# High quality native translations for system replies
STANDARD_TRANSLATIONS = {
    "OUT_OF_SCOPE": {
        "en": "I can help with your queue and information about this organization, but I can't help with that request.",
        "kn": "ನಾನು ನಿಮ್ಮ ಕ್ಯೂ ಮತ್ತು ಈ ಸಂಸ್ಥೆಯ ಮಾಹಿತಿಯೊಂದಿಗೆ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ, ಆದರೆ ಆ ವಿನಂತಿಗೆ ಸಹಾಯ ಮಾಡಲು ಸಾಧ್ಯವಿಲ್ಲ.",
        "hi": "मैं आपकी कतार और इस संगठन की जानकारी में मदद कर सकता हूँ, लेकिन मैं उस अनुरोध में मदद नहीं कर सकता।",
        "te": "నేను మీ క్యూ మరియు ఈ సంస్థ సమాచారంతో సహాయం చేయగలను, కానీ ఆ అభ్యర్థనకు సహాయం చేయలేను.",
        "ta": "உங்கள் வரிசை மற்றும் இந்த நிறுவனம் பற்றிய தகவல்களுக்கு நான் உதவ முடியும், ஆனால் அந்த கோரிக்கைக்கு உதவ முடியாது.",
        "ml": "നിങ്ങളുടെ ക്യൂവിനും ഈ സ്ഥാപനത്തെക്കുറിച്ചുള്ള വിവരങ്ങൾക്കും എന്നെ സഹായിക്കാൻ കഴിയും, എന്നാൽ ആ അഭ്യർത്ഥനയിൽ സഹായിക്കാൻ കഴിയില്ല."
    },
    "MISSING_ORG_INFO": {
        "en": "I don't have that information. Please ask the staff.",
        "kn": "ನನ್ನ ಬಳಿ ಆ ಮಾಹಿತಿ ಇಲ್ಲ. ದಯವಿಟ್ಟು ಸಿಬ್ಬಂದಿಯನ್ನು ಕೇಳಿ.",
        "hi": "मेरे पास वह जानकारी नहीं है। कृपया कर्मचारियों से पूछें।",
        "te": "నా వద్ద ఆ సమాచారం లేదు. దయచేసి సిబ్బందిని అడగండి.",
        "ta": "என்னிடம் அந்த தகவல் இல்லை. தயவுசெய்து ஊழியர்களிடம் கேளுங்கள்.",
        "ml": "എന്റെ പക്കൽ ആ വിവരമില്ല. ദയവായി ജീവനക്കാരോട് ചോദിക്കുക."
    },
    "NAME_REPLY": {
        "en": "I am the VoiceQueue Assistant! I'm here to help you manage your queue token and answer questions about this organization.",
        "kn": "ನಾನು ವಾಯ್ಸ್‌ಕ್ಯೂ ಅಸಿಸ್ಟೆಂಟ್! ನಿಮ್ಮ ಟೋಕನ್ ಮತ್ತು ಸಂಸ್ಥೆಯ ವಿವರಗಳನ್ನು ನಿರ್ವಹಿಸಲು ನಾನು ಇಲ್ಲಿದ್ದೇನೆ.",
        "hi": "मैं वॉयसक्यू असिस्टेंट हूँ! मैं आपके कतार टोकन को प्रबंधित करने और संगठन की जानकारी देने के लिए यहाँ हूँ।",
        "te": "నేను వాయిస్‌క్యూ అసిస్టెంట్‌ని! మీ టೋకెన్ మరియు సంస్థ వివరాల కోసం నేను ఇక్కడ ఉన్నాను.",
        "ta": "நான் VoiceQueue உதவியாளர்! உங்கள் டோக்கன் மற்றும் நிறுவனம் பற்றிய தகவல்களுக்கு உதவ நான் இங்கே இருக்கிறேன்.",
        "ml": "ഞാൻ വോയ്‌സ്ക്യൂ അസിസ്റ്റന്റാണ്! നിങ്ങളുടെ ടോക്കണിനും സ്ഥാപനത്തിന്റെ വിവരങ്ങൾക്കും ഞാൻ ഇവിടെയുണ്ട്."
    },
    "HOW_ARE_YOU": {
        "en": "I'm doing great, thank you for asking! How can I assist you with your queue today?",
        "kn": "ನಾನು ಉತ್ತಮವಾಗಿದ್ದೇನೆ, ವಿಚಾರಿಸಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದಗಳು! ಇಂದು ನಿಮ್ಮ ಕ್ಯೂಗೆ ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",
        "hi": "मैं बहुत अच्छा हूँ, पूछने के लिए धन्यवाद! आज मैं आपकी कतार में कैसे सहायता कर सकता हूँ?",
        "te": "నేను చాలా బాగున్నాను, అడిగినందుకు ధన్యవాదాలు! ఈరోజు మీ క్యూలో నేను ఎలా సహాయపడగలను?",
        "ta": "நான் நலமாக உள்ளேன், கேட்டதற்கு நன்றி! இன்று உங்கள் வரிசையில் நான் எவ்வாறு உதவ முடியும்?",
        "ml": "ഞാൻ സുഖമായിരിക്കുന്നു, ചോദിച്ചതിന് നന്ദി! ഇന്ന് നിങ്ങളുടെ ക്യൂവിൽ എന്നെ എങ്ങനെ സഹായിക്കാനാകും?"
    },
    "DINNER_REPLY": {
        "en": "Haha, thank you for caring! As an AI assistant, I don't eat food, but I'm fully energized and ready to help you with your queue!",
        "kn": "ವಿಚಾರಿಸಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದಗಳು! ನಾನು AI ಅಸಿಸ್ಟೆಂಟ್ ಆಗಿರುವುದರಿಂದ ಆಹಾರ ಸೇವಿಸುವುದಿಲ್ಲ, ಆದರೆ ನಿಮಗೆ ಸಹಾಯ ಮಾಡಲು ಸಂಪೂರ್ಣ ಸಿದ್ಧನಾಗಿದ್ದೇನೆ!",
        "hi": "पूछने के लिए धन्यवाद! एक एआई सहायक होने के नाते मैं खाना नहीं खाता, लेकिन आपकी मदद के लिए पूरी ऊर्जा से तैयार हूँ!",
        "te": "అడిగినందుకు ధన్యవాదాలు! AI అసిస్టెంట్‌గా నేను ఆహారం తీసుకోను, కానీ మీకు సహాయం చేయడానికి సిద్ధంగా ఉన్నాను!",
        "ta": "அக்கறைக்கு நன்றி! AI உதவியாளராக நான் உணவு உண்பதில்லை, ஆனால் உங்களுக்கு உதவ முழுமையாக தயாராக உள்ளேன்!",
        "ml": "ചോദിച്ചതിന് നന്ദി! ഒരു AI അസിസ്റ്റന്റ് എന്ന നിലയിൽ ഞാൻ ഭക്ഷണം കഴിക്കാറില്ല, എന്നാൽ നിങ്ങളെ സഹായിക്കാൻ ഞാൻ പൂർണ്ണ സജ്ജനാണ്!"
    },
    "THANK_YOU": {
        "en": "You're very welcome! Let me know if you need anything else.",
        "kn": "ನಿಮಗೆ ಸುಸ್ವಾಗತ! ಇನ್ನೇನಾದರೂ ಸಹಾಯ ಬೇಕಿದ್ದರೆ ದಯವಿಟ್ಟು ತಿಳಿಸಿ.",
        "hi": "आपका बहुत-बहुत स्वागत है! यदि आपको किसी और चीज़ की आवश्यकता हो तो मुझे बताएं।",
        "te": "మీకు స్వాగతం! మీకు ఇంకా ఏదైనా సహాయం కావాలంటే నాకు చెప్పండి.",
        "ta": "உங்களை வரவேற்கிறேன்! வேறு ஏதேனும் தேவைப்பட்டால் எனக்குத் தெரியப்படுத்துங்கள்.",
        "ml": "തീർച്ചയായും സ്വാഗതം! മറ്റെന്തെങ്കിലും ആവശ്യമുണ്ടെങ്കിൽ എന്നോട് പറയുക."
    }
}

def translate_queue_response(category, queue_data, target_lang):
    """
    Constructs high-quality regional responses for dynamic queue statistics.
    """
    token = queue_data.get("token_number")
    ahead = queue_data.get("people_ahead", 0)
    mins = queue_data.get("estimated_wait_mins", 0)
    status = queue_data.get("status", "waiting")
    serving = queue_data.get("currently_serving")
    waiting_total = queue_data.get("waiting_count", 0)
    customer_name = queue_data.get("customer_name") or "Guest"

    q_type = queue_data.get("queue_query_type")

    # 1. Action: Token Created
    if q_type == "TOKEN_CREATED":
        templates = {
            "en": f"Done! I collected token #{token} for {customer_name}. There are {ahead} people ahead of you, with an estimated wait of ~{mins} minutes.",
            "kn": f"ಮುಗಿದಿದೆ! ನಾನು {customer_name} ಅವರಿಗಾಗಿ ಟೋಕನ್ #{token} ಪಡೆದಿದ್ದೇನೆ. ನಿಮ್ಮ ಮುಂದೆ {ahead} ಜನರಿದ್ದಾರೆ, ಅಂದಾಜು ಕಾಯುವ ಸಮಯ ~{mins} ನಿಮಿಷಗಳು.",
            "hi": f"हो गया! मैंने {customer_name} के लिए टोकन #{token} प्राप्त कर लिया है। आपके आगे {ahead} लोग हैं, अनुमानित प्रतीक्षा समय ~{mins} मिनट है।",
            "te": f"పూర్తయింది! నేను {customer_name} కోసం టోకెన్ #{token} తీసుకున్నాను. మీ ముందు {ahead} మంది ఉన్నారు, అంచనా వేసిన నిరీక్షణ సమయం ~{mins} నిమిషాలు.",
            "ta": f"முடிந்தது! நான் {customer_name} க்காக டோக்கன் #{token} எடுத்துள்ளேன். உங்களுக்கு முன்னால் {ahead} பேர் உள்ளனர், காத்திருப்பு நேரம் ~{mins} நிமிடங்கள்.",
            "ml": f"പൂർത്തിയായി! ഞാൻ {customer_name} നായി ടോക്കൺ #{token} ശേഖരിച്ചു. നിങ്ങൾക്ക് മുന്നിൽ {ahead} ആളുകളുണ്ട്, പ്രതീക്ഷിക്കുന്ന കാത്തിരിപ്പ് സമയം ~{mins} മിനിറ്റ്."
        }
        return templates.get(target_lang, templates["en"])

    # 2. My Token Query
    if q_type == "MY_TOKEN":
        if not token:
            templates = {
                "en": "You haven't collected a token yet. Would you like me to collect a token for you? Just say 'Collect a token for me'.",
                "kn": "ನೀವು ಇನ್ನೂ ಟೋಕನ್ ಪಡೆದಿಲ್ಲ. ನಾನೇ ನಿಮಗಾಗಿ ಟೋಕನ್ ತೆಗೆದುಕೊಳ್ಳಲೇ? 'ನನಗಾಗಿ ಟೋಕನ್ ತೆಗೆದುಕೊಳ್ಳಿ' ಎಂದು ಹೇಳಿ.",
                "hi": "आपने अभी तक टोकन नहीं लिया है। क्या आप चाहते हैं कि मैं आपके लिए टोकन लूँ? बस कहें 'मेरे लिए टोकन लें'。",
                "te": "మీరు ఇంకా టోకెన్ తీసుకోలేదు. నేను మీ కోసం టోకెన్ తీసుకోవాలా? 'నా కోసం టోకెన్ తీసుకోండి' అని చెప్పండి.",
                "ta": "நீங்கள் இன்னும் டோக்கன் எடுக்கவில்லை. நான் உங்களுக்காக டோக்கன் எடுக்கவா? 'எனக்கு டோக்கன் எடுக்கவும்' என்று சொல்லுங்கள்.",
                "ml": "നിങ്ങൾ ഇതുവരെ ടോക്കൺ എടുത്തിട്ടില്ല. നിങ്ങൾക്കായി ഞാൻ ടോക്കൺ എടുക്കണോ? 'എനിക്കായി ടോക്കൺ എടുക്കുക' എന്ന് പറയുക."
            }
            return templates.get(target_lang, templates["en"])

        if status == "serving":
            templates = {
                "en": f"Your token is #{token}, and it's your turn right now! Please proceed to the service desk.",
                "kn": f"ನಿಮ್ಮ ಟೋಕನ್ #{token} ಆಗಿದೆ, ಮತ್ತು ಈಗ ನಿಮ್ಮದೇ ಸರದಿ! ದಯವಿಟ್ಟು ಸೇವಾ ಡೆಸ್ಕ್‌ಗೆ ತೆರಳಿ.",
                "hi": f"आपका टोकन #{token} है, और अभी आपकी ही बारी है! कृपया सेवा काउंटर पर जाएं।",
                "te": f"మీ టోకెన్ #{token}, మరియు ఇప్పుడు మీ వంతు వచ్చింది! దయచేసి సర్వీస్ డెస్క్‌కు వెళ్లండి.",
                "ta": f"உங்கள் டோக்கன் #{token}, இப்போது உங்கள் முறை! தயவுசெய்து சேவை கவுண்டருக்கு செல்லவும்.",
                "ml": f"നിങ്ങളുടെ ടോക്കൺ #{token} ആണ്, ഇപ്പോൾ നിങ്ങളുടെ ഊഴമാണ്! ദയവായി സേവന കൗണ്ടറിലേക്ക് പോകുക."
            }
            return templates.get(target_lang, templates["en"])

        templates = {
            "en": f"Your token is #{token}. You are currently waiting with {ahead} {'person' if ahead == 1 else 'people'} ahead.",
            "kn": f"ನಿಮ್ಮ ಟೋಕನ್ #{token} ಆಗಿದೆ. ನಿಮ್ಮ ಮುಂದೆ {ahead} ಜನರಿದ್ದಾರೆ.",
            "hi": f"आपका टोकन #{token} है। आपके आगे वर्तमान में {ahead} लोग प्रतीक्षा कर रहे हैं।",
            "te": f"మీ టోకెన్ #{token}. మీ ముందు ప్రస్తుతం {ahead} మంది వేచి ఉన్నారు.",
            "ta": f"உங்கள் டோக்கன் #{token}. உங்களுக்கு முன்னால் {ahead} பேர் காத்திருக்கிறார்கள்.",
            "ml": f"നിങ്ങളുടെ ടോക്കൺ #{token} ആണ്. ഇപ്പോൾ നിങ്ങൾക്ക് മുന്നിൽ {ahead} ആളുകൾ കാത്തിരിക്കുന്നു."
        }
        return templates.get(target_lang, templates["en"])

    # 3. People Ahead Query
    if q_type == "PEOPLE_AHEAD":
        if status == "serving":
            templates = {
                "en": "It's your turn right now! You are currently being served.",
                "kn": "ಈಗ ನಿಮ್ಮ ಸರದಿಯಾಗಿದೆ! ಕೌಂಟರ್‌ನಲ್ಲಿ ನಿಮಗೆ ಸೇವೆ ನೀಡಲಾಗುತ್ತಿದೆ.",
                "hi": "अभी आपकी बारी है! वर्तमान में आपको सेवा दी जा रही है।",
                "te": "ఇప్పుడు మీ వంతు! ప్రస్తుతం మీకు సేవ అందిస్తున్నారు.",
                "ta": "இப்போது உங்கள் முறை! தற்போது உங்களுக்கு சேவை வழங்கப்படுகிறது.",
                "ml": "ഇപ്പോൾ നിങ്ങളുടെ ഊഴമാണ്! ഇപ്പോൾ നിങ്ങളെ സേവിക്കുന്നു."
            }
            return templates.get(target_lang, templates["en"])

        if ahead == 0 and token:
            templates = {
                "en": "You are next in line! Please be ready near the service desk.",
                "kn": "ಮುಂದಿನ ಸರದಿ ನಿಮ್ಮದೇ! ದಯವಿಟ್ಟು ಸೇವಾ ಕೌಂಟರ್ ಬಳಿ ಸಿದ್ಧರಾಗಿರಿ.",
                "hi": "कतार में अगला नंबर आपका है! कृपया सेवा काउंटर के पास तैयार रहें।",
                "te": "తదుపరి వంతు మీదే! దయచేసి సర్వీస్ కౌంటర్ వద్ద సిద్ధంగా ఉండండి.",
                "ta": "வரிசையில் அடுத்தது நீங்கள்தான்! தயவுசெய்து சேவை கவுண்டர் அருகில் தயாராக இருங்கள்.",
                "ml": "അടുത്തത് നിങ്ങളുടെ ഊഴമാണ്! ദയവായി സേവന കൗണ്ടറിന് സമീപം തയ്യാറായിരിക്കുക."
            }
            return templates.get(target_lang, templates["en"])

        templates = {
            "en": f"There {'is' if ahead == 1 else 'are'} currently {ahead} {'person' if ahead == 1 else 'people'} ahead of you.",
            "kn": f"ಪ್ರಸ್ತುತ ನಿಮ್ಮ ಮುಂದೆ {ahead} ಜನರಿದ್ದಾರೆ.",
            "hi": f"वर्तमान में आपके आगे {ahead} लोग हैं।",
            "te": f"ప్రస్తుతం మీ ముందు {ahead} మంది ఉన్నారు.",
            "ta": f"தற்போது உங்களுக்கு முன்னால் {ahead} பேர் உள்ளனர்.",
            "ml": f"ഇപ്പോൾ നിങ്ങൾക്ക് മുന്നിൽ {ahead} ആളുകളുണ്ട്."
        }
        return templates.get(target_lang, templates["en"])

    # 4. Wait Time Query
    if q_type == "WAIT_TIME":
        if status == "serving":
            templates = {
                "en": "Your turn is right now! Please head to the counter.",
                "kn": "ನಿಮ್ಮ ಸರದಿ ಈಗಲೇ ಬಂದಿದೆ! ದಯವಿಟ್ಟು ಕೌಂಟರ್‌ಗೆ ತೆರಳಿ.",
                "hi": "आपकी बारी आ गई है! कृपया काउंटर पर जाएं।",
                "te": "ఇది మీ వంతు! దయచేసి కౌంటర్‌కు వెళ్లండి.",
                "ta": "உங்கள் முறை வந்துவிட்டது! தயவுசெய்து கவுண்டருக்கு செல்லவும்.",
                "ml": "നിങ്ങളുടെ ഊഴം എത്തിക്കഴിഞ്ഞു! ദയവായി കൗണ്ടറിലേക്ക് പോകുക."
            }
            return templates.get(target_lang, templates["en"])

        templates = {
            "en": f"Your estimated waiting time is approximately ~{mins} minutes.",
            "kn": f"ನಿಮ್ಮ ಅಂದಾಜು ಕಾಯುವ ಸಮಯ ಸುಮಾರು ~{mins} ನಿಮಿಷಗಳು.",
            "hi": f"आपका अनुमानित प्रतीक्षा समय लगभग ~{mins} मिनट है।",
            "te": f"మీ అంచనా వేసిన నిరీక్షణ సమయం దాదాపు ~{mins} నిమిషాలు.",
            "ta": f"உங்கள் மதிப்பிடப்பட்ட காத்திருப்பு நேரம் சுமார் ~{mins} நிமிடங்கள்.",
            "ml": f"നിങ്ങൾ പ്രതീക്ഷിക്കുന്ന കാത്തിരിപ്പ് സമയം ഏകദേശം ~{mins} മിനിറ്റാണ്."
        }
        return templates.get(target_lang, templates["en"])

    # 5. Currently Serving Query
    if q_type == "CURRENT_NUMBER":
        if serving:
            templates = {
                "en": f"Token #{serving} is currently being served at the counter. There are {waiting_total} customers waiting in line.",
                "kn": f"ಕೌಂಟರ್‌ನಲ್ಲಿ ಪ್ರಸ್ತುತ ಟೋಕನ್ #{serving} ಅನ್ನು ಕರೆಯಲಾಗುತ್ತಿದೆ. ಕ್ಯೂನಲ್ಲಿ {waiting_total} ಜನರು ಕಾಯುತ್ತಿದ್ದಾರೆ.",
                "hi": f"काउंटर पर वर्तमान में टोकन #{serving} को बुलाया जा रहा है। कतार में {waiting_total} लोग प्रतीक्षा कर रहे हैं।",
                "te": f"కౌంటర్‌లో ప్రస్తుతం టోకెన్ #{serving} నంబర్‌కు సేవ చేస్తున్నారు. క్యూలో {waiting_total} మంది వేచి ఉన్నారు.",
                "ta": f"கவுண்டரில் தற்போது டோக்கன் #{serving} அழைக்கப்படுகிறது. வரிசையில் {waiting_total} பேர் காத்திருக்கிறார்கள்.",
                "ml": f"കൗണ്ടറിൽ ഇപ്പോൾ ടೋക്കൺ #{serving} വിളിക്കുന്നു. ക്യൂവിൽ {waiting_total} ആളുകൾ കാത്തിരിക്കുന്നു."
            }
            return templates.get(target_lang, templates["en"])
        else:
            templates = {
                "en": f"No token is currently being called. There are {waiting_total} customers waiting in line.",
                "kn": f"ಪ್ರಸ್ತುತ ಯಾವುದೇ ಟೋಕನ್ ಕರೆಯುತ್ತಿಲ್ಲ. ಕ್ಯೂನಲ್ಲಿ {waiting_total} ಜನರು ಕಾಯುತ್ತಿದ್ದಾರೆ.",
                "hi": f"वर्तमान में कोई टोकन नहीं बुलाया जा रहा है। कतार में {waiting_total} लोग प्रतीक्षा कर रहे हैं।",
                "te": f"ప్రస్తుతం ఏ టోకెన్‌నూ పిలవడం లేదు. క్యూలో {waiting_total} మంది వేచి ఉన్నారు.",
                "ta": f"தற்போது எந்த டோக்கனும் அழைக்கப்படவில்லை. வரிசையில் {waiting_total} பேர் காத்திருக்கிறார்கள்.",
                "ml": f"ഇപ്പോൾ ടോക്കണുകളൊന്നും വിളിക്കുന്നില്ല. ക്യൂവിൽ {waiting_total} ആളുകൾ കാത്തിരിക്കുന്നു."
            }
            return templates.get(target_lang, templates["en"])

    return None

def translate_text(english_text, target_lang, category=None, queue_meta=None):
    """
    Main translation router. Translates English text to target_lang.
    """
    if target_lang == "en":
        return english_text

    # 1. Check Standard Exact Matches
    if english_text in STANDARD_TRANSLATIONS["OUT_OF_SCOPE"]["en"] or category == "OUT_OF_SCOPE":
        return STANDARD_TRANSLATIONS["OUT_OF_SCOPE"].get(target_lang, english_text)

    if english_text in STANDARD_TRANSLATIONS["MISSING_ORG_INFO"]["en"] or "don't have that information" in english_text.lower():
        return STANDARD_TRANSLATIONS["MISSING_ORG_INFO"].get(target_lang, english_text)

    if "voicequeue assistant" in english_text.lower():
        return STANDARD_TRANSLATIONS["NAME_REPLY"].get(target_lang, english_text)

    if "doing great" in english_text.lower():
        return STANDARD_TRANSLATIONS["HOW_ARE_YOU"].get(target_lang, english_text)

    if "don't eat food" in english_text.lower() or "caring" in english_text.lower():
        return STANDARD_TRANSLATIONS["DINNER_REPLY"].get(target_lang, english_text)

    if "very welcome" in english_text.lower():
        return STANDARD_TRANSLATIONS["THANK_YOU"].get(target_lang, english_text)

    # 2. Check Dynamic Queue Translations
    if queue_meta and queue_meta.get("queue_query_type"):
        queue_res = translate_queue_response(category, queue_meta, target_lang)
        if queue_res:
            return queue_res

    # 3. Known organization translations
    if "counter 2" in english_text.lower():
        c2 = {
            "kn": "ಕೌಂಟರ್ 2: ಪಾವತಿಗಳು ಮತ್ತು ದಾಖಲೆ ಸಲ್ಲಿಕೆ",
            "hi": "काउंटर 2: भुगतान और दस्तावेज जमा करना",
            "te": "కౌంటర్ 2: చెల్లింపులు మరియు పత్రాల సమర్పణ",
            "ta": "கவுண்டர் 2: கட்டணங்கள் மற்றும் ஆவண சமர்ப்பிப்பு",
            "ml": "കൗണ്ടർ 2: പേയ്‌മെന്റുകളും ഡോക്യുമെന്റ് സമർപ്പണവും"
        }
        if target_lang in c2:
            return c2[target_lang]

    if "pharmacy" in english_text.lower() and "ground floor" in english_text.lower():
        pharm = {
            "kn": "ಫಾರ್ಮಸಿಯು ಕೌಂಟರ್ 3 ರ ಪಕ್ಕದಲ್ಲಿ ನೆಲಮಹಡಿಯಲ್ಲಿದೆ.",
            "hi": "फार्मेसी काउंटर 3 के बगल में भूतल पर स्थित है।",
            "te": "ఫార్మసీ కౌంటర్ 3 పక్కన గ్రౌండ్ ఫ్లోర్‌లో ఉంది.",
            "ta": "மருந்தகம் தரைத்தளத்தில் கவுண்டர் 3 அருகில் அமைந்துள்ளது.",
            "ml": "ഫാർമസി ഗ്രൗണ്ട് ഫ്ലോറിൽ കൗണ്ടർ 3 ന് അടുത്തായി സ്ഥിതി ചെയ്യുന്നു."
        }
        if target_lang in pharm:
            return pharm[target_lang]

    if "government photo id" in english_text.lower():
        docs = {
            "kn": "ದಯವಿಟ್ಟು ಮಾನ್ಯ ಸರ್ಕಾರಿ ಫೋಟೋ ಐಡಿ ಮತ್ತು ನಿಮ್ಮ ಸೇವಾ ಉಲ್ಲೇಖ ಸಂಖ್ಯೆ ಅಥವಾ ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಸ್ಲಿಪ್ ಅನ್ನು ತನ್ನಿ.",
            "hi": "कृपया एक वैध सरकारी फोटो पहचान पत्र और अपना संदर्भ नंबर या अपॉइंटमेंट पर्ची साथ लाएं।",
            "te": "దయచేసి చెల్లుబాటు అయ్యే ప్రభుత్వ ఫోటో ID మరియు మీ అపాయింట్‌మెంట్ రసీదుని తీసుకురండి.",
            "ta": "தயவுசெய்து செல்லுபடியாகும் அரசு புகைப்பட அடையாள அட்டை மற்றும் உங்கள் ரசீதை கொண்டு வாருங்கள்.",
            "ml": "സാധുവായ സർക്കാർ ഫോട്ടോ ഐഡിയും നിങ്ങളുടെ അപ്പോയിന്റ്മെന്റ് സ്ലിപ്പും കൊണ്ടുവരിക."
        }
        if target_lang in docs:
            return docs[target_lang]

    if "operating hours" in english_text.lower() or "monday to friday" in english_text.lower():
        hours = {
            "kn": "ಸೇವಾ ಕೇಂದ್ರದ ಕೆಲಸದ ಸಮಯ:\nಸೋಮವಾರದಿಂದ ಶುಕ್ರವಾರ: ಬೆಳಿಗ್ಗೆ 9:00 - ಸಂಜೆ 5:00\nಶನಿವಾರ: ಬೆಳಿಗ್ಗೆ 9:00 - ಮಧ್ಯಾಹ್ನ 1:00\nಭಾನುವಾರ: ರಜೆ",
            "hi": "सेवा केंद्र का समय:\nसोमवार से शुक्रवार: सुबह 9:00 बजे - शाम 5:00 बजे\nशनिवार: सुबह 9:00 बजे - दोपहर 1:00 बजे\nरविवार: बंद",
            "te": "సేవా కేంద్రం పని వేళలు:\nసోమవారం నుండి శుక్రవారం: ఉదయం 9:00 - సాయంత్రం 5:00\nశనివారం: ఉదయం 9:00 - మధ్యాహ్నం 1:00\nఆదివారం: సెలవు",
            "ta": "சேவை மையத்தின் வேலை நேரம்:\nதிங்கள் முதல் வெள்ளி: காலை 9:00 - மாலை 5:00\nசனிக்கிழமை: காலை 9:00 - மதியம் 1:00\nஞாயிறு: விடுமுறை",
            "ml": "സേവന കേന്ദ്രത്തിന്റെ പ്രവർത്തന സമയം:\nതിങ്കൾ മുതൽ വെള്ളി വരെ: രാവിലെ 9:00 - വൈകുന്നേരം 5:00\nശനിയാഴ്ച: രാവിലെ 9:00 - ഉച്ചയ്ക്ക് 1:00\nഞായർ: അവധി"
        }
        if target_lang in hours:
            return hours[target_lang]

    # Return english as default fallback
    return english_text
