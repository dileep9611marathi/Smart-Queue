import re
import json
from multilingual_engine import (
    translate_text,
    SUPPORTED_LANGUAGES
)
from datetime import datetime

class VoiceQueueAssistant:
    def get_date_time(self):
        now = datetime.now()
        return now.strftime("Today is %A, %d %B %Y. The time is %I:%M %p.")

    def __init__(self):
    
        # Strict predefined safety and out-of-scope messages required by system
        self.MSG_OUT_OF_SCOPE = (
            "I can help with your queue and information about this organization, "
            "but I can't help with that request."
        )
        self.MSG_MISSING_ORG_INFO = "I don't have that information. Please ask the staff."

    def classify_and_respond(self, user_message, queue_context, org_info, create_token_fn=None, output_language="en"):
        """
        Classifies user_message into:
        - 'QUEUE'
        - 'ORGANIZATION'
        - 'CASUAL_CONVERSATION'
        - 'OUT_OF_SCOPE'
        
        Translates response to target output_language.
        """
        raw_msg = (user_message or "").strip()
        if any(word in raw_msg.lower() for word in ["date", "today", "day", "time"]):
         return {    
        "category": "CASUAL_CONVERSATION",
        "reply": self.get_date_time(),
        "english_reply": self.get_date_time()
    }

        # VoiceQueue accepts QUESTIONS/COMMANDS in English only.
        # The assistant can still translate its English answer into the
        # user's selected reply language.
        if not output_language or output_language == "auto" or output_language == "same":
            target_lang = "en"
        elif output_language in SUPPORTED_LANGUAGES:
            target_lang = output_language
        else:
            target_lang = "en"

        if not raw_msg:
            greeting_en = "Hello! How can I help you with your queue or this facility today?"
            greeting_local = translate_text(greeting_en, target_lang, category="CASUAL_CONVERSATION")
            return {
                "category": "CASUAL_CONVERSATION",
                "reply": greeting_local,
                "english_reply": greeting_en,
                "detected_language": "en",
                "output_language": target_lang,
                "bcp47": SUPPORTED_LANGUAGES.get(target_lang, {}).get("bcp47", "en-IN"),
                "action": None
            }

        # Reject non-English script input. We do NOT translate or interpret
        # Kannada/Hindi/Telugu/etc. as commands.
        if any((0x80 <= ord(ch) <= 0x10FFFF) for ch in raw_msg):
            english_reply = (
                "Please ask your question in English. You can choose your preferred "
                "language for my answer from the Reply in menu."
            )
            localized_reply = translate_text(english_reply, target_lang, category="OUT_OF_SCOPE")
            return {
                "category": "INPUT_LANGUAGE_NOT_SUPPORTED",
                "reply": localized_reply,
                "english_reply": english_reply,
                "detected_language": "non_en",
                "output_language": target_lang,
                "bcp47": SUPPORTED_LANGUAGES.get(target_lang, {}).get("bcp47", "en-IN"),
                "action": None
            }

        normalized_msg = raw_msg.lower()

        category = None
        english_reply = None
        action = None
        queue_meta = None

        # 1. Check CASUAL_CONVERSATION first
        is_casual, casual_reply = self._check_casual(normalized_msg)
        if is_casual:
            category = "CASUAL_CONVERSATION"
            english_reply = casual_reply

        # 2. Check QUEUE queries and actions
        if not category:
            is_queue, queue_reply, queue_action, q_meta = self._check_queue(normalized_msg, queue_context, create_token_fn)
            if is_queue:
                category = "QUEUE"
                english_reply = queue_reply
                action = queue_action
                queue_meta = q_meta

        # 3. Check ORGANIZATION queries
        if not category:
            is_org, org_reply = self._check_organization(normalized_msg, org_info)
            if is_org:
                category = "ORGANIZATION"
                english_reply = org_reply

        # 4. Default: OUT_OF_SCOPE
        if not category:
            category = "OUT_OF_SCOPE"
            english_reply = self.MSG_OUT_OF_SCOPE

        # Translate reply to the requested output language
        localized_reply = translate_text(english_reply, target_lang, category=category, queue_meta=queue_meta)

        return {
            "category": category,
            "reply": localized_reply,
            "english_reply": english_reply,
            "detected_language": "en",
            "output_language": target_lang,
            "bcp47": SUPPORTED_LANGUAGES.get(target_lang, {}).get("bcp47", "en-IN"),
            "action": action
        }

    # ------------------ Helper: CASUAL_CONVERSATION ------------------
    def _check_casual(self, msg):
        clean_msg = re.sub(r"[^\w\s]", "", msg).strip()

        # Greetings
        greeting_patterns = [
            r"^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening|day)|yo|namaste)\b"
        ]
        for p in greeting_patterns:
            if re.search(p, clean_msg):
                return True, "Hello! I am your VoiceQueue Assistant. How can I help you with your token or our services today?"

        # Name / Identity
        if any(phrase in clean_msg for phrase in [
            "whats your name", "what is your name", "who are you",
            "what are you", "your name", "tell me your name", "who created you"
        ]):
            return True, "I am the VoiceQueue Assistant! I'm here to help you manage your queue token and answer questions about this organization."

        # How are you / Well-being
        if any(phrase in clean_msg for phrase in [
            "how are you", "how are you doing", "how are things",
            "how do you do", "how is it going", "hows it going"
        ]):
            return True, "I'm doing great, thank you for asking! How can I assist you with your queue today?"

        # Dinner / Meals / Personal friendly questions
        if any(phrase in clean_msg for phrase in [
            "had your dinner", "had dinner", "did you have dinner",
            "did you eat", "have you eaten", "had lunch", "had breakfast", "are you hungry"
        ]):
            return True, "Haha, thank you for caring! As an AI assistant, I don't eat food, but I'm fully energized and ready to help you with your queue!"

        # Gratitude & Politeness
        if any(phrase in clean_msg for phrase in [
            "thank you", "thanks", "thank u", "thx", "appreciate it", "much appreciated"
        ]):
            return True, "You're very welcome! Let me know if you need anything else."

        # Farewells
        if any(phrase in clean_msg for phrase in [
            "bye", "goodbye", "see you", "have a nice day", "have a good day", "catch you later"
        ]):
            return True, "Goodbye! Have a wonderful day, and make sure to keep an eye on your token!"

        return False, None

    # ------------------ Helper: QUEUE ------------------
    def _check_queue(self, msg, ctx, create_token_fn):
        clean_msg = re.sub(r"[^\w\s]", "", msg).strip()

        # Action: Request to take/collect a token
        token_action_patterns = [
            r"(collect|take|get|book|give|issue|generate|grab)\s+(me\s+)?(a\s+)?token",
            r"join(\s+the)?\s+queue",
            r"i\s+need\s+(a\s+)?token",
            r"put\s+me\s+in(\s+the)?\s+line",
            r"sign\s+me\s+up"
        ]
        for p in token_action_patterns:
            if re.search(p, clean_msg):
                if ctx.get("token_number"):
                    q_meta = {**ctx, "queue_query_type": "MY_TOKEN"}
                    return True, f"You already have an active token: #{ctx['token_number']}! Your status is {ctx.get('status', 'waiting')}.", None, q_meta
                
                if create_token_fn:
                    name_match = re.search(r"for\s+([a-zA-Z\s]+)$", clean_msg)
                    customer_name = name_match.group(1).strip().title() if name_match else "Guest"
                    new_token = create_token_fn(customer_name)
                    q_meta = {**new_token, "queue_query_type": "TOKEN_CREATED"}
                    return True, (
                        f"Done! I collected token #{new_token['token_number']} for {customer_name}. "
                        f"There are {new_token['people_ahead']} people ahead of you, "
                        f"with an estimated wait of ~{new_token['estimated_wait_mins']} minutes."
                    ), {"type": "TOKEN_CREATED", "token": new_token}, q_meta
                else:
                    return True, "You can collect a token anytime using the 'Get My Queue Token' button on this page.", None, None

        # User's own token number
        if any(k in clean_msg for k in [
            "whats my token", "what is my token", "my token", "my number",
            "check my token", "what token do i have", "tell me my token",
            "which token is mine", "my token number"
        ]):
            q_meta = {**ctx, "queue_query_type": "MY_TOKEN"}
            if ctx.get("token_number"):
                num = ctx["token_number"]
                status = ctx.get("status", "waiting")
                if status == "serving":
                    return True, f"Your token is #{num}, and it's your turn right now! Please proceed to the service desk.", None, q_meta
                elif status == "completed":
                    return True, f"Your token #{num} has already been completed. Thank you!", None, q_meta
                else:
                    ahead = ctx.get("people_ahead", 0)
                    return True, f"Your token is #{num}. You are currently waiting with {ahead} {'person' if ahead == 1 else 'people'} ahead.", None, q_meta
            else:
                return True, "You haven't collected a token yet. Would you like me to collect a token for you? Just say 'Collect a token for me'.", None, q_meta

        # People ahead
        if any(k in clean_msg for k in [
            "how many people are ahead", "how many people ahead", "people ahead",
            "how many ahead", "who is ahead of me", "how many before me",
            "am i next", "is it my turn"
        ]):
            q_meta = {**ctx, "queue_query_type": "PEOPLE_AHEAD"}
            if ctx.get("token_number"):
                ahead = ctx.get("people_ahead", 0)
                status = ctx.get("status", "waiting")
                if status == "serving":
                    return True, "It's your turn right now! You are currently being served.", None, q_meta
                elif ahead == 0:
                    return True, "You are next in line! Please be ready near the service desk.", None, q_meta
                else:
                    return True, f"There {'is' if ahead == 1 else 'are'} currently {ahead} {'person' if ahead == 1 else 'people'} ahead of you.", None, q_meta
            else:
                waiting_total = ctx.get("waiting_count", 0)
                return True, f"You don't have a token yet, but there are currently {waiting_total} people waiting in the general queue. Would you like a token?", None, q_meta

        # Estimated wait time
        if any(k in clean_msg for k in [
            "when will my turn come", "when is my turn", "how long will it take",
            "how long do i have to wait", "estimated wait", "wait time", "waiting time",
            "how much time left", "when am i up"
        ]):
            q_meta = {**ctx, "queue_query_type": "WAIT_TIME"}
            if ctx.get("token_number"):
                wait_mins = ctx.get("estimated_wait_mins", 0)
                status = ctx.get("status", "waiting")
                if status == "serving":
                    return True, "Your turn is right now! Please head to the counter.", None, q_meta
                elif wait_mins == 0:
                    return True, "You are next in line! Your turn should be called momentarily.", None, q_meta
                else:
                    return True, f"Your estimated waiting time is approximately ~{wait_mins} minutes.", None, q_meta
            else:
                avg_time = ctx.get("avg_service_time_mins", 5)
                waiting_total = ctx.get("waiting_count", 0)
                est_total = waiting_total * avg_time
                return True, f"The current estimated wait is about ~{est_total} minutes based on {waiting_total} waiting customers (~{avg_time} mins/person). Take a token to get your exact spot!", None, q_meta

        # Currently serving / Current number
        if any(k in clean_msg for k in [
            "whats the current number", "what is the current number", "current number",
            "currently serving", "who is serving", "which number is serving",
            "what token is being served", "current token", "current queue",
            "queue status", "whats the queue", "how is the queue"
        ]):
            q_meta = {**ctx, "queue_query_type": "CURRENT_NUMBER"}
            serving = ctx.get("currently_serving")
            waiting = ctx.get("waiting_count", 0)
            if serving:
                serving_name = ctx.get("currently_serving_name")
                name_str = f" ({serving_name})" if serving_name and serving_name != "Guest" else ""
                return True, f"Token #{serving}{name_str} is currently being served at the counter. There are {waiting} customers waiting in line.", None, q_meta
            else:
                return True, f"No token is currently being called. There are {waiting} customers waiting in line.", None, q_meta

        # General queue inquiry keywords
        queue_keywords = ["token", "queue", "line", "counter wait", "ticket", "spot in line"]
        if any(kw in clean_msg for kw in queue_keywords):
            q_meta = {**ctx, "queue_query_type": "CURRENT_NUMBER"}
            serving = ctx.get("currently_serving")
            waiting = ctx.get("waiting_count", 0)
            token_num = ctx.get("token_number")
            token_info = f" Your token is #{token_num}." if token_num else " You have not taken a token yet."
            serving_info = f" Currently serving: #{serving}." if serving else " No active token is currently serving."
            return True, f"The queue currently has {waiting} people waiting.{serving_info}{token_info}", None, q_meta

        return False, None, None, None

    # ------------------ Helper: ORGANIZATION ------------------
    def _check_organization(self, msg, org_info):
        clean_msg = re.sub(r"[^\w\s]", "", msg).strip()

        org_triggers = [
            "counter", "desk", "room", "floor", "where", "location", "address",
            "time", "hours", "timing", "open", "close", "opening", "closing",
            "document", "documents", "requirement", "requirements", "paper", "papers",
            "service", "services", "offer", "facility", "hospital", "clinic",
            "office", "center", "centre", "pharmacy", "doctor", "lab", "billing",
            "cashier", "payment", "fees", "fee", "cost", "price", "parking",
            "wifi", "contact", "phone", "email", "manager", "staff", "rules",
            "appointment", "policy", "policies", "bring", "id"
        ]

        is_org_query = any(trigger in clean_msg.split() or trigger in clean_msg for trigger in org_triggers)

        faqs = org_info.get("faqs") or []
        if isinstance(faqs, str):
            try:
                faqs = json.loads(faqs)
            except Exception:
                faqs = []

        # Check FAQ matches first
        for faq in faqs:
            q_clean = re.sub(r"[^\w\s]", "", faq.get("question", "").lower()).strip()
            q_words = set(q_clean.split())
            user_words = set(clean_msg.split())
            meaningful_overlap = (q_words & user_words) - {"is", "the", "a", "an", "what", "where", "how", "do", "i", "to", "this", "my", "your"}
            if len(meaningful_overlap) >= 2 or (len(meaningful_overlap) >= 1 and len(q_words - {"is", "the", "a", "an", "what", "where", "how", "do", "i"}) <= 2):
                return True, faq.get("answer", "")

        # Check Opening / Closing Hours
        if any(w in clean_msg for w in ["hours", "open", "close", "closing", "opening", "timing", "what time", "when do you close", "when do you open"]):
            hours = org_info.get("opening_hours", "").strip()
            if hours:
                org_name = org_info.get("org_name", "Our office")
                return True, f"Operating hours for {org_name}:\n{hours}"
            else:
                return True, self.MSG_MISSING_ORG_INFO

        # Check Counter Directory
        if "counter" in clean_msg:
            counter_match = re.search(r"counter\s*(\d+)", clean_msg)
            counter_info = org_info.get("counter_info", "").strip()
            
            if counter_info:
                if counter_match:
                    target_c = f"counter {counter_match.group(1)}"
                    for line in counter_info.split("\n"):
                        if target_c in line.lower():
                            return True, line.strip()
                return True, f"Here is the counter information:\n{counter_info}"
            else:
                return True, self.MSG_MISSING_ORG_INFO

        # Check Services Offered
        if any(w in clean_msg for w in ["services", "service", "what do you do", "what can i do here", "what do you offer"]):
            services = org_info.get("services", "").strip()
            if services:
                org_name = org_info.get("org_name", "This facility")
                return True, f"Services offered at {org_name}:\n{services}"
            else:
                return True, self.MSG_MISSING_ORG_INFO

        # Check Organization Name / Identity
        if any(w in clean_msg for w in ["what organization", "what place is this", "name of this place", "where am i"]):
            name = org_info.get("org_name", "").strip()
            if name:
                return True, f"You are at {name}."
            else:
                return True, self.MSG_MISSING_ORG_INFO

        # Keyword search
        keywords_to_check = [w for w in clean_msg.split() if len(w) > 3 and w not in ["where", "what", "which", "there", "about", "could", "would", "please"]]
        all_org_text = (
            (org_info.get("org_name") or "") + "\n" +
            (org_info.get("counter_info") or "") + "\n" +
            (org_info.get("opening_hours") or "") + "\n" +
            (org_info.get("services") or "")
        ).lower()

        for kw in keywords_to_check:
            if kw in all_org_text:
                for line in all_org_text.split("\n"):
                    if kw in line:
                        return True, line.strip()

        # Strict safety fallback
        if is_org_query:
            return True, self.MSG_MISSING_ORG_INFO

        return False, None
