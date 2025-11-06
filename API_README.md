# Raecer Bot API Documentation

A RESTful API for conducting medical conversations with cancer patients, extracting clinical entities, and mapping symptoms to PRO-CTCAE codes.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Data Storage](#data-storage)
- [Session Management](#session-management)
- [Error Handling](#error-handling)
- [Security Considerations](#security-considerations)
- [Architecture](#architecture)

## Features

- 🤖 **Conversational AI** powered by GPT-4
- 🧠 **Real-time clinical entity extraction** using ClinicalBERT
- 📊 **Automatic PRO-CTCAE symptom mapping**
- 🔐 **Session-based conversation management**
- 🌐 **CORS-enabled** for web applications
- 📝 **Persistent data storage** in JSON format
- 🏥 **Medical-grade conversation tracking**

## Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key
- pip or conda package manager

### Installation

1. **Clone the repository** (if applicable):
   ```bash
   cd raecer-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   # Create a .env file
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

4. **Start the server**:
   ```bash
   python api_server.py
   ```

The API will be available at `http://localhost:8000`

### Quick Test

Once the server is running:

```bash
# Health check
curl http://localhost:8000/api/health

# Start a conversation
curl -X POST http://localhost:8000/api/conversation/start
```

## API Endpoints

### Health Check

**Endpoint:** `GET /api/health`

Check if the API and all services are running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00",
  "services": {
    "openai": true,
    "ner": true,
    "pro_ctcae": true
  }
}
```

---

### Start Conversation

**Endpoint:** `POST /api/conversation/start`

Create a new conversation session with Cornelius, the AI medical assistant.

**Request:** No body required

**Response (201 Created):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Hello! I'm Cornelius. To help prepare for your upcoming exam, could you tell me a little about your medical history, especially concerning any past allergies or imaging scans?",
  "status": "active"
}
```

**Fields:**
- `session_id` (string): Unique identifier for this conversation session
- `message` (string): Initial greeting from Cornelius
- `status` (string): Current session status ("active")

---

### Send Message

**Endpoint:** `POST /api/conversation/<session_id>/message`

Send a user message and receive the bot's response with entity extraction.

**Request Body:**
```json
{
  "message": "I had hives after my last CT scan with contrast dye"
}
```

**Response (200 OK):**
```json
{
  "response": "I'm sorry to hear that you experienced hives. Can you tell me more about when this happened and if you had any other symptoms?",
  "entities": {
    "PROBLEM": ["hives"],
    "TEST": ["CT scan"]
  },
  "conversation_ended": false,
  "message_count": 4
}
```

**Fields:**
- `response` (string): The bot's conversational response
- `entities` (object): Clinical entities detected by ClinicalBERT NER
- `conversation_ended` (boolean): Whether the bot has concluded the conversation
- `message_count` (integer): Total messages in the conversation

**Errors:**
- `404`: Session not found
- `400`: Session is not active or message is missing
- `500`: Server error during processing

---

### End Conversation

**Endpoint:** `POST /api/conversation/<session_id>/end`

End the conversation and generate final structured summaries.

**Request:** No body required

**Response (200 OK):**
```json
{
  "patient_data": {
    "has_previous_reaction": true,
    "has_kidney_issues": false,
    "takes_metformin": false,
    "reported_symptoms": ["hives", "itching"],
    "patient_concerns": "Worried about having another reaction to contrast dye",
    "full_summary": "Patient reports previous allergic reaction to contrast dye during CT scan approximately 6 months ago, manifesting as hives and itching. No kidney problems or metformin use reported. Patient expresses concern about potential future reactions."
  },
  "pro_ctcae_data": {
    "patient_id": "unknown",
    "assessment_date": "20250115_103000",
    "symptoms": [
      {
        "symptom_term": "Hives",
        "code": "PRO-CTCAE_hives",
        "presence": true,
        "raw_text": "hives"
      },
      {
        "symptom_term": "Itching",
        "code": "PRO-CTCAE_itching",
        "severity": 2,
        "raw_text": "itching"
      }
    ],
    "clinical_summary": "Patient reports 2 symptoms:\n- Hives (urticaria): Present\n- Itching (Severity: MODERATE)",
    "source_file": "data/patient_summary_20250115_103000.json"
  }
}
```

**Fields:**
- `patient_data` (object): Structured patient information extracted from conversation
- `pro_ctcae_data` (object): PRO-CTCAE symptom mappings (if symptoms detected)

---

### Get Conversation Status

**Endpoint:** `GET /api/conversation/<session_id>/status`

Get the current status and metadata of a conversation.

**Response (200 OK):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:35:00",
  "message_count": 6,
  "patient_data": null,
  "pro_ctcae_data": null,
  "error_message": null
}
```

**Status Values:**
- `active`: Conversation is ongoing
- `completed`: Conversation ended and summary generated
- `error`: An error occurred during processing

---

### Get Conversation History

**Endpoint:** `GET /api/conversation/<session_id>/history`

Retrieve the full conversation history (excludes system prompts).

**Response (200 OK):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "messages": [
    {
      "role": "assistant",
      "content": "Hello! I'm Cornelius..."
    },
    {
      "role": "user",
      "content": "I had hives after my last CT scan"
    },
    {
      "role": "assistant",
      "content": "I'm sorry to hear that..."
    }
  ]
}
```

---

### Delete Conversation

**Endpoint:** `DELETE /api/conversation/<session_id>`

Delete a conversation session and free up resources.

**Response (200 OK):**
```json
{
  "message": "Session deleted"
}
```

**Errors:**
- `404`: Session not found

---

### List All Conversations

**Endpoint:** `GET /api/conversations`

List all active conversation sessions (useful for debugging and monitoring).

**Response (200 OK):**
```json
{
  "count": 2,
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "active",
      "created_at": "2025-01-15T10:30:00",
      "updated_at": "2025-01-15T10:35:00",
      "message_count": 6
    },
    {
      "session_id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "completed",
      "created_at": "2025-01-15T09:00:00",
      "updated_at": "2025-01-15T09:15:00",
      "message_count": 12
    }
  ]
}
```

---

### Cleanup Old Sessions

**Endpoint:** `POST /api/cleanup`

Remove sessions older than specified hours (default: 24).

**Request Body (optional):**
```json
{
  "max_age_hours": 48
}
```

**Response (200 OK):**
```json
{
  "message": "Cleaned up 5 old session(s)",
  "deleted_count": 5
}
```

---

### Root Endpoint

**Endpoint:** `GET /`

Get API documentation and available endpoints.

**Response (200 OK):**
```json
{
  "name": "Raecer Bot API",
  "version": "1.0.0",
  "description": "Medical conversation API for patient history collection and PRO-CTCAE mapping",
  "endpoints": {
    "GET /api/health": "Health check",
    "POST /api/conversation/start": "Start a new conversation",
    "POST /api/conversation/<session_id>/message": "Send a message",
    ...
  }
}
```

## Usage Examples

### Python Client

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def chat_with_cornelius():
    # Start conversation
    response = requests.post(f"{BASE_URL}/api/conversation/start")
    data = response.json()
    session_id = data["session_id"]
    print(f"🤖 Cornelius: {data['message']}\n")

    # Conversation loop
    while True:
        user_input = input("You: ")

        if user_input.lower() in ["quit", "done", "exit"]:
            break

        # Send message
        response = requests.post(
            f"{BASE_URL}/api/conversation/{session_id}/message",
            json={"message": user_input}
        )
        data = response.json()

        print(f"\n🤖 Cornelius: {data['response']}\n")

        # Show detected entities
        if data.get("entities"):
            print(f"🧠 Detected entities: {data['entities']}\n")

        # Check if conversation ended
        if data.get("conversation_ended"):
            print("Conversation concluded by Cornelius.\n")
            break

    # Get final summary
    print("Generating final summary...\n")
    response = requests.post(f"{BASE_URL}/api/conversation/{session_id}/end")
    summary = response.json()

    print("=" * 60)
    print("📋 PATIENT SUMMARY")
    print("=" * 60)
    print(json.dumps(summary["patient_data"], indent=2))

    if summary.get("pro_ctcae_data"):
        print("\n" + "=" * 60)
        print("📊 PRO-CTCAE MAPPING")
        print("=" * 60)
        print(summary["pro_ctcae_data"]["clinical_summary"])

if __name__ == "__main__":
    chat_with_cornelius()
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

async function startConversation() {
  const response = await axios.post(`${BASE_URL}/api/conversation/start`);
  return response.data;
}

async function sendMessage(sessionId, message) {
  const response = await axios.post(
    `${BASE_URL}/api/conversation/${sessionId}/message`,
    { message }
  );
  return response.data;
}

async function endConversation(sessionId) {
  const response = await axios.post(
    `${BASE_URL}/api/conversation/${sessionId}/end`
  );
  return response.data;
}

// Example usage
(async () => {
  try {
    // Start
    const { session_id, message } = await startConversation();
    console.log(`Bot: ${message}`);

    // Send messages
    const response1 = await sendMessage(
      session_id,
      "I had hives after my last CT scan"
    );
    console.log(`Bot: ${response1.response}`);
    console.log(`Entities:`, response1.entities);

    // End and get summary
    const summary = await endConversation(session_id);
    console.log('Patient Summary:', summary.patient_data);

  } catch (error) {
    console.error('Error:', error.message);
  }
})();
```

### cURL Examples

**Start conversation:**
```bash
curl -X POST http://localhost:8000/api/conversation/start
```

**Send message:**
```bash
curl -X POST http://localhost:8000/api/conversation/<SESSION_ID>/message \
  -H "Content-Type: application/json" \
  -d '{"message": "I had hives after my last CT scan with contrast dye"}'
```

**End conversation:**
```bash
curl -X POST http://localhost:8000/api/conversation/<SESSION_ID>/end
```

**Get status:**
```bash
curl http://localhost:8000/api/conversation/<SESSION_ID>/status
```

**List all conversations:**
```bash
curl http://localhost:8000/api/conversations
```

**Delete conversation:**
```bash
curl -X DELETE http://localhost:8000/api/conversation/<SESSION_ID>
```

### Web Frontend Example (HTML + JavaScript)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Raecer Bot Chat</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; }
        #chat { border: 1px solid #ccc; height: 400px; overflow-y: auto; padding: 10px; }
        .message { margin: 10px 0; }
        .user { color: blue; }
        .bot { color: green; }
        input { width: 80%; padding: 10px; }
        button { padding: 10px 20px; }
    </style>
</head>
<body>
    <h1>Cornelius - Medical Assistant</h1>
    <div id="chat"></div>
    <input id="userInput" type="text" placeholder="Type your message...">
    <button onclick="sendMessage()">Send</button>
    <button onclick="endConversation()">End & Get Summary</button>

    <script>
        const BASE_URL = 'http://localhost:8000';
        let sessionId = null;

        async function startConversation() {
            const response = await fetch(`${BASE_URL}/api/conversation/start`, {
                method: 'POST'
            });
            const data = await response.json();
            sessionId = data.session_id;
            addMessage('bot', data.message);
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;

            addMessage('user', message);
            input.value = '';

            const response = await fetch(
                `${BASE_URL}/api/conversation/${sessionId}/message`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message })
                }
            );
            const data = await response.json();
            addMessage('bot', data.response);

            if (data.conversation_ended) {
                alert('Conversation concluded by Cornelius');
            }
        }

        async function endConversation() {
            const response = await fetch(
                `${BASE_URL}/api/conversation/${sessionId}/end`,
                { method: 'POST' }
            );
            const data = await response.json();

            console.log('Patient Summary:', data.patient_data);
            alert('Summary generated! Check console for details.');
        }

        function addMessage(role, text) {
            const chat = document.getElementById('chat');
            const div = document.createElement('div');
            div.className = `message ${role}`;
            div.innerHTML = `<strong>${role === 'user' ? 'You' : 'Cornelius'}:</strong> ${text}`;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        // Start conversation on page load
        startConversation();
    </script>
</body>
</html>
```

## Data Storage

All conversation data is persisted to the `data/` directory:

### Patient Summary Files
**Format:** `data/patient_summary_YYYYMMDD_HHMMSS.json`

```json
{
  "has_previous_reaction": true,
  "has_kidney_issues": false,
  "takes_metformin": false,
  "reported_symptoms": ["hives", "itching"],
  "patient_concerns": "Worried about having another reaction",
  "full_summary": "Patient reports previous allergic reaction..."
}
```

### PRO-CTCAE Files
**Format:** `data/pro_ctcae_YYYYMMDD_HHMMSS.json`

```json
{
  "patient_id": "unknown",
  "assessment_date": "20250115_103000",
  "symptoms": [
    {
      "symptom_term": "Hives",
      "code": "PRO-CTCAE_hives",
      "presence": true,
      "raw_text": "hives"
    }
  ],
  "clinical_summary": "Patient reports 1 symptom...",
  "source_file": "data/patient_summary_20250115_103000.json"
}
```

## Session Management

### In-Memory Sessions

Sessions are stored in memory using a thread-safe `SessionManager` class:

- Each session has a unique UUID
- Sessions include full conversation history
- Status tracking (active, completed, error)
- Timestamps for creation and updates
- Generated summaries and mappings

### Session Lifecycle

1. **Created** - via `/api/conversation/start`
2. **Active** - messages sent via `/api/conversation/<id>/message`
3. **Completed** - ended via `/api/conversation/<id>/end`
4. **Deleted** - manually via `/api/conversation/<id>` or cleanup

### Automatic Cleanup

Use the cleanup endpoint to remove old sessions:

```bash
curl -X POST http://localhost:8000/api/cleanup \
  -H "Content-Type: application/json" \
  -d '{"max_age_hours": 24}'
```

**Note:** Sessions are cleared when the server restarts. For production use, consider implementing persistent storage (Redis, PostgreSQL, etc.).

## Error Handling

### HTTP Status Codes

- `200 OK` - Successful request
- `201 Created` - New resource created
- `400 Bad Request` - Invalid input or inactive session
- `404 Not Found` - Session doesn't exist
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
  "error": "Descriptive error message"
}
```

### Common Errors

**Session not found:**
```json
{
  "error": "Session not found"
}
```

**Session not active:**
```json
{
  "error": "Session is completed, not active"
}
```

**Missing message:**
```json
{
  "error": "Message is required"
}
```

**Model error:**
```json
{
  "error": "Model returned no response"
}
```

## Security Considerations

### Current Implementation

The current API is designed for development and testing. For production deployment, implement:

### 1. Authentication & Authorization

```python
# Example: API Key authentication
from functools import wraps
from flask import request

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('API_KEY'):
            return jsonify({"error": "Invalid API key"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/conversation/start', methods=['POST'])
@require_api_key
def start_conversation():
    # ...
```

### 2. Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/conversation/<session_id>/message', methods=['POST'])
@limiter.limit("30 per minute")
def send_message(session_id):
    # ...
```

### 3. HTTPS

Always use HTTPS in production:

```python
# Use a production WSGI server
# gunicorn --certfile=cert.pem --keyfile=key.pem api_server:app
```

### 4. Input Validation

```python
from flask import request
import bleach

def sanitize_input(text):
    # Remove HTML tags, limit length, etc.
    return bleach.clean(text, strip=True)[:1000]
```

### 5. HIPAA Compliance

For handling Protected Health Information (PHI):

- Encrypt data at rest and in transit
- Implement audit logging
- Use secure session storage (encrypted database)
- Implement access controls
- Regular security audits
- Business Associate Agreements (BAA) with cloud providers
- Patient consent management

### 6. Environment Variables

Never commit secrets to version control:

```bash
# .env file (add to .gitignore)
OPENAI_API_KEY=sk-...
API_SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://...
```

## Architecture

### System Components

```
┌─────────────┐
│   Client    │ (Web, Mobile, CLI)
└──────┬──────┘
       │ HTTP/JSON
┌──────▼──────────┐
│  Flask Server   │ (api_server.py)
│  - Routes       │
│  - CORS         │
└──────┬──────────┘
       │
┌──────▼────────────────────────┐
│    Session Manager            │
│  - In-memory storage          │
│  - Thread-safe operations     │
└──────┬────────────────────────┘
       │
┌──────▼──────────┬──────────────┬────────────────┐
│                 │              │                │
▼                 ▼              ▼                ▼
OpenAI API    ClinicalBERT   PRO-CTCAE      File Storage
(GPT-4)       (NER)          Mapper         (JSON)
```

### File Structure

```
raecer-bot/
├── api_server.py          # Flask API server
├── session_manager.py     # Session management
├── app.py                 # Original CLI tool
├── config.py              # Configuration
├── ner_extractor.py       # ClinicalBERT NER
├── pro_ctcae_mapper.py    # PRO-CTCAE mapping
├── process_existing_files.py  # Batch processor
├── test_client.py         # Test client
├── requirements.txt       # Python dependencies
├── API_README.md          # This file
├── .env                   # Environment variables
└── data/                  # Data storage
    ├── patient_summary_*.json
    └── pro_ctcae_*.json
```

### Technology Stack

- **Web Framework:** Flask 3.1.0
- **AI/ML:** OpenAI GPT-4, Hugging Face Transformers
- **NER Model:** ClinicalBERT (medicalai/ClinicalBERT)
- **Medical Standards:** PRO-CTCAE (Patient-Reported Outcomes)
- **Data Format:** JSON
- **API Style:** RESTful

## Original CLI Tool

The original command-line interface is still available and unchanged:

```bash
python app.py
```

This runs an interactive conversation directly in your terminal, useful for:
- Testing the conversation flow
- Debugging prompts
- Offline usage
- Direct data collection

## Testing

### Run the Test Client

```bash
python test_client.py
```

This will:
1. Check API health
2. Start a conversation
3. Send test messages
4. Generate summary
5. Display results

### Manual Testing

```bash
# Terminal 1: Start server
python api_server.py

# Terminal 2: Test endpoints
curl http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/conversation/start
```

## Troubleshooting

### Server won't start

**Problem:** "Error initializing OpenAI client"
- **Solution:** Check that `OPENAI_API_KEY` is set in `.env`

**Problem:** "Error loading NER model"
- **Solution:** Ensure sufficient disk space and memory for model download

### Session not found

**Problem:** Getting 404 errors
- **Solution:** Sessions are cleared on server restart; start a new conversation

### Slow responses

**Problem:** API takes a long time to respond
- **Solution:**
  - First request loads models (can take 30-60 seconds)
  - Subsequent requests should be faster
  - Consider using GPU for faster inference

## Contributing

To extend the API:

1. Add new routes in `api_server.py`
2. Update session schema in `session_manager.py`
3. Modify prompts in `config.py`
4. Add new PRO-CTCAE mappings in `pro_ctcae_mapper.py`

## License

[Your License Here]

## Contact

[Your Contact Information]

---

**Version:** 1.0.0
**Last Updated:** January 2025
