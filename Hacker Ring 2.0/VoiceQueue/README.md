# 📢 VoiceQueue - Smart Queue Management MVP with AI Assistant

VoiceQueue is a lightweight, mobile-friendly queue management web application built with **Python Flask** and **SQLite**, equipped with a **context-aware AI Assistant** and **QR code check-in**.

Customers can take a digital token, track their real-time position in line, and chat with the AI Assistant to check their wait time, ask about office hours or counter locations, and even collect a token using plain English.

---

## 🌟 Key Features

1. **🤖 Context-Aware AI Assistant (`ai_assistant.py`)**:
   - Runs locally without requiring any paid external AI APIs.
   - Mobile-friendly chat drawer on the customer page (`templates/index.html`) with quick-action suggestion chips.
   - Automatically classifies queries into 4 distinct categories:
     1. **`QUEUE`**:
        - Real-time queue answers: *"What's my token?"*, *"How many people are ahead?"*, *"When will my turn come?"*, *"What's the current number?"*.
        - Natural language token creation: *"Collect a token for me"* or *"Get a token for Alex"*.
     2. **`ORGANIZATION`**:
        - Factual answers derived **only** from staff-configured facility information: *"Where is counter 2?"*, *"What time does this office close?"*, *"What documents do I need?"*, *"Where is the pharmacy?"*.
        - **Strict Safety Rule**: Never hallucinates. If the question is not answered in the organization profile, it strictly replies: *"I don't have that information. Please ask the staff."*
     3. **`CASUAL_CONVERSATION`**:
        - Polite small talk: *"What's your name?"*, *"How are you?"*, *"Thank you"*, *"Had your dinner?"*.
     4. **`OUT_OF_SCOPE`**:
        - Politely deflects unrelated web searches, homework, or general trivia: *"I can help with your queue and information about this organization, but I can't help with that request."*

2. **🏢 Admin Organization & Facility Profile (`/admin`)**:
   - Staff can easily update:
     - Organization Name
     - Opening & Closing Hours
     - Counter Directory (Counter 1, Counter 2, etc.)
     - Services Offered
     - Dynamic FAQ list (add, edit, and delete Q&A pairs)
   - Changes are immediately reflected in the assistant's responses.

3. **📱 QR-Code-Based Queue Joining**:
   - Staff can display the generated QR code on the admin dashboard or counter kiosk (`/kiosk`).
   - Automatically discovers the local Wi-Fi / LAN IP so smartphones on the same network can scan and join instantly (`/join`).

4. **🎟️ Customer Token Page (`/` or `/join`)**:
   - Instant token issuance.
   - Large display of user's token number, currently serving token, people ahead, and estimated wait time.
   - Real-time auto-polling every 3 seconds.
   - Preserves tokens in `localStorage`.
   - Audio chime and visual alert when it's the customer's turn.

5. **⚙️ Staff Admin Dashboard (`/admin`)**:
   - One-click **"Call Next Customer"** button.
   - Live waiting queue table and metrics.
   - Average service time adjustment and daily queue reset.

6. **📺 Fullscreen Counter Kiosk & Poster (`/kiosk`)**:
   - Distraction-free display for front desks or tablets with a printable poster view.

---

## 🚀 How to Run the Application

### 1. Open Terminal in Project Directory
```powershell
cd c:\Users\venky\OneDrive\Desktop\VoiceQueue
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Start the Flask App
```powershell
python app.py
```
Output:
```text
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://10.x.x.x:5000
```

### 4. Open in Your Browser
- **Customer View**: [http://127.0.0.1:5000](http://127.0.0.1:5000) or [http://127.0.0.1:5000/join](http://127.0.0.1:5000/join)
- **Staff Admin View**: [http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)
- **Counter Kiosk & Poster**: [http://127.0.0.1:5000/kiosk](http://127.0.0.1:5000/kiosk)

---

## 🤖 Testing the AI Assistant

1. Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** on your computer or smartphone.
2. Click the floating **"🤖 Ask Assistant"** button at the bottom right.
3. Try asking questions across all 4 categories:
   - **Queue Query**: *"Collect a token for me"* &rarr; Assistant immediately issues your token and loads your tracker!
   - **Queue Query**: *"How many people are ahead?"* &rarr; Assistant calculates your real wait position.
   - **Organization Query**: *"What time does this office close?"* &rarr; Reads official office hours.
   - **Organization Query**: *"Where is counter 2?"* &rarr; Reads counter directory.
   - **Safety Rule Test**: *"Where is the cafeteria?"* &rarr; Replies: *"I don't have that information. Please ask the staff."*
   - **Casual Chat**: *"Had your dinner?"* &rarr; Gives a friendly polite response.
   - **Out of Scope**: *"Solve my math homework"* &rarr; Replies: *"I can help with your queue and information about this organization, but I can't help with that request."*

---

## 🧪 Running Automated Tests

Run the comprehensive test suite to verify queue calculations, QR generation, and all 4 assistant classification categories:
```powershell
python test_app.py
```

---

## 📁 Project Structure

```
VoiceQueue/
│
├── app.py                # Flask backend, REST API, SQLite database connection
├── ai_assistant.py       # Context-aware NLP intent classifier and response engine
├── requirements.txt      # Dependencies (Flask, qrcode, pillow)
├── test_app.py           # Automated unit and integration tests (5 test suites)
├── voicequeue.db         # Persistent SQLite database (tokens, settings, org info)
├── README.md             # Complete documentation
│
├── static/
│   └── style.css         # Modern, mobile-responsive CSS and assistant chat styles
│
└── templates/
    ├── index.html        # Customer page with live queue tracker & AI assistant drawer
    ├── admin.html        # Staff dashboard (queue manager, QR card, org info editor)
    └── kiosk.html        # Fullscreen counter kiosk & printable poster
```


## Language behavior
- User input is English-only.
- The assistant does not detect or interpret Kannada/Hindi/Telugu/etc. as commands.
- Users can select a preferred reply language; the English answer is translated for display and speech.
- Pressing the microphone button stops current TTS playback before listening, preventing the assistant from hearing its own voice.
