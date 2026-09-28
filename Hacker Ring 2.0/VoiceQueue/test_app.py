import os
import unittest
import json
from app import app, init_db, DB_FILE

class VoiceQueueTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        init_db()
        self.client.post("/api/admin/reset")
        self.client.post("/api/admin/settings", json={"avg_service_time_mins": 5})
        # Reset organization info to standard default for clean test isolation
        from app import set_org_info, DEFAULT_ORG_DATA
        set_org_info(DEFAULT_ORG_DATA)

    def test_pages_render(self):
        """Test that user, join, admin, and kiosk HTML pages render correctly."""
        res_user = self.client.get("/")
        self.assertEqual(res_user.status_code, 200)
        self.assertIn(b"VoiceQueue", res_user.data)
        self.assertIn(b"Get My Queue Token", res_user.data)

        res_join = self.client.get("/join")
        self.assertEqual(res_join.status_code, 200)

        res_admin = self.client.get("/admin")
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b"Staff", res_admin.data)
        self.assertIn(b"Call Next Customer", res_admin.data)
        self.assertIn(b"Customer Check-in QR Code", res_admin.data)

        res_kiosk = self.client.get("/kiosk")
        self.assertEqual(res_kiosk.status_code, 200)
        self.assertIn(b"Scan to Join Queue", res_kiosk.data)

    def test_qr_code_endpoints(self):
        """Test QR code generation and info endpoints."""
        res_info = self.client.get("/api/qr/info")
        self.assertEqual(res_info.status_code, 200)
        data_info = res_info.get_json()
        self.assertTrue(data_info["success"])
        self.assertIn("network_url", data_info)

        res_qr = self.client.get("/api/qr")
        self.assertEqual(res_qr.status_code, 200)
        self.assertEqual(res_qr.content_type, "image/png")
        self.assertTrue(res_qr.data.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_queue_workflow(self):
        """Test queue lifecycle: creation, progression, wait times, reset."""
        # User 1 (Alice)
        res1 = self.client.post("/api/token/create", json={"name": "Alice"}).get_json()
        self.assertEqual(res1["token"]["token_number"], 101)

        # User 2 (Bob)
        res2 = self.client.post("/api/token/create", json={"name": "Bob"}).get_json()
        self.assertEqual(res2["token"]["token_number"], 102)
        self.assertEqual(res2["token"]["people_ahead"], 1)
        self.assertEqual(res2["token"]["estimated_wait_mins"], 5)

        # Admin call next
        call_res = self.client.post("/api/admin/call-next").get_json()
        self.assertEqual(call_res["currently_serving"]["token_number"], 101)

    def test_ai_assistant_classification(self):
        """Test the 4 assistant categories: QUEUE, ORGANIZATION, CASUAL_CONVERSATION, OUT_OF_SCOPE."""

        # ---------------- 1. QUEUE Category ----------------
        # 1a. User asks to collect a token
        res_token_req = self.client.post("/api/assistant/chat", json={
            "message": "Collect a token for me"
        }).get_json()
        self.assertEqual(res_token_req["category"], "QUEUE")
        self.assertIsNotNone(res_token_req.get("action"))
        self.assertEqual(res_token_req["action"]["type"], "TOKEN_CREATED")
        my_token_num = res_token_req["action"]["token"]["token_number"]
        self.assertEqual(my_token_num, 101)

        # 1b. User asks "What's my token?" with active token context
        res_my_token = self.client.post("/api/assistant/chat", json={
            "message": "What's my token?",
            "token_number": 101
        }).get_json()
        self.assertEqual(res_my_token["category"], "QUEUE")
        self.assertIn("#101", res_my_token["reply"])

        # 1c. "How many people are ahead?"
        res_ahead = self.client.post("/api/assistant/chat", json={
            "message": "How many people are ahead?",
            "token_number": 101
        }).get_json()
        self.assertEqual(res_ahead["category"], "QUEUE")

        # 1d. "When will my turn come?"
        res_turn = self.client.post("/api/assistant/chat", json={
            "message": "When will my turn come?",
            "token_number": 101
        }).get_json()
        self.assertEqual(res_turn["category"], "QUEUE")

        # 1e. "What's the current number?"
        res_curr = self.client.post("/api/assistant/chat", json={
            "message": "What's the current number?"
        }).get_json()
        self.assertEqual(res_curr["category"], "QUEUE")

        # ---------------- 2. ORGANIZATION Category ----------------
        # 2a. Counter question
        res_counter = self.client.post("/api/assistant/chat", json={
            "message": "Where is counter 2?"
        }).get_json()
        self.assertEqual(res_counter["category"], "ORGANIZATION")
        self.assertIn("counter 2", res_counter["reply"].lower())

        # 2b. Hours question
        res_hours = self.client.post("/api/assistant/chat", json={
            "message": "What time does this office close?"
        }).get_json()
        self.assertEqual(res_hours["category"], "ORGANIZATION")
        self.assertIn("5:00 pm", res_hours["reply"].lower())

        # 2c. Documents question (from FAQ)
        res_docs = self.client.post("/api/assistant/chat", json={
            "message": "What documents do I need?"
        }).get_json()
        self.assertEqual(res_docs["category"], "ORGANIZATION")
        self.assertIn("government photo id", res_docs["reply"].lower())

        # 2d. Pharmacy question (from FAQ)
        res_pharm = self.client.post("/api/assistant/chat", json={
            "message": "Where is the pharmacy?"
        }).get_json()
        self.assertEqual(res_pharm["category"], "ORGANIZATION")
        self.assertIn("ground floor", res_pharm["reply"].lower())

        # 2e. STRICT SAFETY CHECK: Unknown organization question
        res_unknown_org = self.client.post("/api/assistant/chat", json={
            "message": "Where is the cafeteria?"
        }).get_json()
        self.assertEqual(res_unknown_org["category"], "ORGANIZATION")
        self.assertEqual(
            res_unknown_org["reply"],
            "I don't have that information. Please ask the staff."
        )

        # ---------------- 3. CASUAL_CONVERSATION Category ----------------
        casual_queries = [
            ("What's your name?", "voicequeue assistant"),
            ("How are you?", "doing great"),
            ("Thank you.", "welcome"),
            ("Had your dinner?", "caring")
        ]
        for query, expected_snippet in casual_queries:
            res_casual = self.client.post("/api/assistant/chat", json={"message": query}).get_json()
            self.assertEqual(res_casual["category"], "CASUAL_CONVERSATION", f"Failed for: {query}")
            self.assertIn(expected_snippet, res_casual["reply"].lower())

        # ---------------- 4. OUT_OF_SCOPE Category ----------------
        out_of_scope_queries = [
            "What is the capital of Australia?",
            "Can you write a poem about autumn leaves?",
            "Solve my calculus equation x^2 + 4x + 4 = 0",
            "What is the score of the cricket match today?"
        ]
        expected_oos_message = "I can help with your queue and information about this organization, but I can't help with that request."
        for query in out_of_scope_queries:
            res_oos = self.client.post("/api/assistant/chat", json={"message": query}).get_json()
            self.assertEqual(res_oos["category"], "OUT_OF_SCOPE", f"Failed for: {query}")
            self.assertEqual(res_oos["reply"], expected_oos_message)

    def test_admin_org_info_management(self):
        """Test retrieving and updating organization info through admin API."""
        # Get existing
        res_get = self.client.get("/api/org-info").get_json()
        self.assertTrue(res_get["success"])
        self.assertIn("VoiceQueue", res_get["data"]["org_name"])

        # Update info
        updated_data = {
            "org_name": "Downtown Metro Clinic",
            "opening_hours": "8:00 AM - 8:00 PM Daily",
            "counter_info": "Counter 1: Triage\nCounter 2: Consultation",
            "services": "General Medicine, Diagnostics",
            "faqs": [
                {"question": "Is parking free?", "answer": "Yes, parking is free for visitors in lot B."}
            ]
        }
        res_post = self.client.post("/api/admin/org-info", json=updated_data).get_json()
        self.assertTrue(res_post["success"])

        # Verify assistant now answers parking question
        res_chat = self.client.post("/api/assistant/chat", json={
            "message": "Is parking free?"
        }).get_json()
        self.assertEqual(res_chat["category"], "ORGANIZATION")
        self.assertIn("parking is free", res_chat["reply"].lower())

    def test_multilingual_voice_assistant(self):
        """Test cross-lingual voice assistant: EN->EN, KN->KN, KN->HI, HI->EN, and TTS."""
        # First collect a token so queue inquiries have real data
        token_res = self.client.post("/api/token/create", json={"name": "Priya"}).get_json()
        token_num = token_res["token"]["token_number"]
        self.assertEqual(token_num, 101)

        # 1. English -> English
        res_en_en = self.client.post("/api/assistant/chat", json={
            "message": "What's my token?",
            "token_number": 101,
            "output_language": "en"
        }).get_json()
        self.assertEqual(res_en_en["category"], "QUEUE")
        self.assertEqual(res_en_en["output_language"], "en")
        self.assertIn("#101", res_en_en["reply"])

        # 2. Kannada -> Kannada (Auto or kn)
        res_kn_kn = self.client.post("/api/assistant/chat", json={
            "message": "ನನ್ನ ಟೋಕನ್ ಯಾವುದು?",
            "token_number": 101,
            "output_language": "kn"
        }).get_json()
        self.assertEqual(res_kn_kn["category"], "QUEUE")
        self.assertEqual(res_kn_kn["detected_language"], "kn")
        self.assertEqual(res_kn_kn["output_language"], "kn")
        self.assertIn("ಟೋಕನ್", res_kn_kn["reply"])
        self.assertIn("101", res_kn_kn["reply"])

        # 3. Kannada -> Hindi (Cross-lingual!)
        res_kn_hi = self.client.post("/api/assistant/chat", json={
            "message": "ನನ್ನ ಟೋಕನ್ ಯಾವುದು?",
            "token_number": 101,
            "output_language": "hi"
        }).get_json()
        self.assertEqual(res_kn_hi["category"], "QUEUE")
        self.assertEqual(res_kn_hi["detected_language"], "kn")
        self.assertEqual(res_kn_hi["output_language"], "hi")
        self.assertIn("टोकन", res_kn_hi["reply"])
        self.assertIn("101", res_kn_hi["reply"])

        # 4. Hindi -> English (Cross-lingual!)
        res_hi_en = self.client.post("/api/assistant/chat", json={
            "message": "आगे कितने लोग हैं?",
            "token_number": 101,
            "output_language": "en"
        }).get_json()
        self.assertEqual(res_hi_en["category"], "QUEUE")
        self.assertEqual(res_hi_en["detected_language"], "hi")
        self.assertEqual(res_hi_en["output_language"], "en")
        self.assertTrue("ahead" in res_hi_en["reply"].lower() or "next in line" in res_hi_en["reply"].lower())

        # 5. Out of scope in Kannada with Telugu output
        res_oos_te = self.client.post("/api/assistant/chat", json={
            "message": "ಕ್ಯಾಲ್ಕುಲಸ್ ಸಮೀಕರಣವನ್ನು ಪರಿಹರಿಸಿ",
            "output_language": "te"
        }).get_json()
        self.assertEqual(res_oos_te["category"], "OUT_OF_SCOPE")
        self.assertEqual(res_oos_te["output_language"], "te")
        self.assertIn("సహాయం", res_oos_te["reply"])

        # 6. Audio TTS Endpoint Test (Speaker ON audio generation)
        res_tts = self.client.get("/api/assistant/tts?text=ನಮಸ್ಕಾರ&lang=kn")
        self.assertEqual(res_tts.status_code, 200)
        self.assertEqual(res_tts.content_type, "audio/mpeg")
        self.assertGreater(len(res_tts.data), 100)

        # 7. Languages endpoint
        res_langs = self.client.get("/api/languages").get_json()
        self.assertTrue(res_langs["success"])
        self.assertIn("kn", res_langs["languages"])
        self.assertIn("hi", res_langs["languages"])
        self.assertIn("te", res_langs["languages"])
        self.assertIn("ta", res_langs["languages"])
        self.assertIn("ml", res_langs["languages"])
        self.assertIn("en", res_langs["languages"])

if __name__ == "__main__":
    unittest.main()
