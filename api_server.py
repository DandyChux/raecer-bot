import datetime
import json
import os
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

import config
from ner_extractor import NERExtractor
from pro_ctcae_mapper import ProCtcaeMapper
from session_manager import ConversationSession, SessionManager

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize global components
load_dotenv()
session_manager = SessionManager()
openai_client: Optional[OpenAI] = None
ner_client: Optional[NERExtractor] = None
pro_ctcae_mapper: Optional[ProCtcaeMapper] = None


def initialize_services():
    """Initialize OpenAI, NER, and PRO-CTCAE services"""
    global openai_client, ner_client, pro_ctcae_mapper

    try:
        openai_client = OpenAI()
        print("✅ OpenAI client initialized")
    except Exception as e:
        print(f"❌ Error initializing OpenAI client: {e}")
        raise

    try:
        ner_client = NERExtractor(model_name=config.NER_MODEL_NAME)
        print("✅ NER client initialized")
    except Exception as e:
        print(f"❌ Error initializing NER client: {e}")
        raise

    try:
        pro_ctcae_mapper = ProCtcaeMapper()
        print("✅ PRO-CTCAE mapper initialized")
    except Exception as e:
        print(f"❌ Error initializing PRO-CTCAE mapper: {e}")
        raise


def generate_summary(
    session: ConversationSession,
) -> tuple[Optional[dict], Optional[dict], Optional[str]]:
    """
    Generate patient summary and PRO-CTCAE mapping from conversation history
    Returns: (patient_data, pro_ctcae_data, error_message)
    """
    try:
        # Add the extraction prompt
        extraction_message: ChatCompletionMessageParam = {
            "role": "user",
            "content": config.JSON_EXTRACTION_PROMPT,
        }
        conversation_history = session.messages + [extraction_message]

        # Get summary from OpenAI
        response = openai_client.chat.completions.create(
            model=config.CONVERSATIONAL_MODEL,
            messages=conversation_history,
            temperature=0.0,
        )

        message_content = response.choices[0].message.content
        if message_content is None:
            return None, None, "Model returned no content"

        # Parse JSON
        cleaned_json_string = (
            message_content.strip().replace("```json", "").replace("```", "")
        )
        patient_data = json.loads(cleaned_json_string)

        # Save patient data to file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("data", exist_ok=True)

        file_name = f"data/patient_summary_{timestamp}.json"
        with open(file_name, "w") as f:
            json.dump(patient_data, f, indent=4)

        # Generate PRO-CTCAE mapping
        pro_ctcae_data = None
        entries = pro_ctcae_mapper.parse_patient_json(file_name)

        if entries:
            ehr_data = pro_ctcae_mapper.format_for_ehr_entry(entries)
            ehr_data["source_file"] = file_name
            ehr_data["assessment_date"] = timestamp

            clinical_summary = pro_ctcae_mapper.generate_clinical_summary(entries)
            ehr_data["clinical_summary"] = clinical_summary

            # Save PRO-CTCAE file
            pro_ctcae_file = f"data/pro_ctcae_{timestamp}.json"
            with open(pro_ctcae_file, "w") as f:
                json.dump(ehr_data, f, indent=2)

            pro_ctcae_data = ehr_data

        return patient_data, pro_ctcae_data, None

    except json.JSONDecodeError as e:
        return None, None, f"Could not parse JSON: {str(e)}"
    except Exception as e:
        return None, None, f"Error generating summary: {str(e)}"


# ==================== API Routes ====================


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "services": {
                "openai": openai_client is not None,
                "ner": ner_client is not None and ner_client.pipeline is not None,
                "pro_ctcae": pro_ctcae_mapper is not None,
            },
        }
    )


@app.route("/api/conversation/start", methods=["POST"])
def start_conversation():
    """
    Start a new conversation session

    Returns:
        session_id: Unique identifier for this conversation
        initial_message: The bot's greeting
    """
    try:
        # Create system prompt message
        system_message: ChatCompletionMessageParam = {
            "role": "system",
            "content": config.SYSTEM_PROMPT,
        }

        # Create new session
        session = session_manager.create_session(initial_message=system_message)

        # Generate initial greeting
        initial_greeting = "Hello! I'm Cornelius. To help prepare for your upcoming exam, could you tell me a little about your medical history, especially concerning any past allergies or imaging scans?"

        assistant_message: ChatCompletionMessageParam = {
            "role": "assistant",
            "content": initial_greeting,
        }
        session_manager.add_message(session.session_id, assistant_message)

        return jsonify(
            {
                "session_id": session.session_id,
                "message": initial_greeting,
                "status": "active",
            }
        ), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/conversation/<session_id>/message", methods=["POST"])
def send_message(session_id: str):
    """
    Send a message in an active conversation

    Request body:
        message: The user's message text

    Returns:
        response: The bot's response
        entities: Any clinical entities detected
        conversation_ended: Whether the conversation has concluded
    """
    try:
        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        if session.status != "active":
            return jsonify({"error": f"Session is {session.status}, not active"}), 400

        # Get user message from request
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Message is required"}), 400

        user_input = data["message"]

        # Extract entities using NER
        extracted_entities = {}
        if ner_client and ner_client.pipeline:
            extracted_entities = ner_client.extract_entities(user_input)

        # Add user message to session
        user_message: ChatCompletionMessageParam = {
            "role": "user",
            "content": user_input,
        }
        session_manager.add_message(session_id, user_message)

        # Get bot response from OpenAI
        response = openai_client.chat.completions.create(
            model=config.CONVERSATIONAL_MODEL, messages=session.messages
        )

        bot_response = response.choices[0].message.content
        if bot_response is None:
            return jsonify({"error": "Model returned no response"}), 500

        # Add bot message to session
        bot_message: ChatCompletionMessageParam = {
            "role": "assistant",
            "content": bot_response,
        }
        session_manager.add_message(session_id, bot_message)

        # Check if conversation should end
        conversation_ended = "i have everything i need" in bot_response.lower()

        return jsonify(
            {
                "response": bot_response,
                "entities": extracted_entities,
                "conversation_ended": conversation_ended,
                "message_count": len(session.messages),
            }
        ), 200

    except Exception as e:
        session_manager.update_session(session_id, status="error", error_message=str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/conversation/<session_id>/end", methods=["POST"])
def end_conversation(session_id: str):
    """
    End a conversation and generate the final summary

    Returns:
        patient_data: Structured patient information
        pro_ctcae_data: PRO-CTCAE mapping (if applicable)
    """
    try:
        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        if session.status == "completed":
            # Already completed, return existing data
            return jsonify(
                {
                    "patient_data": session.patient_data,
                    "pro_ctcae_data": session.pro_ctcae_data,
                }
            ), 200

        # Generate summary
        patient_data, pro_ctcae_data, error_message = generate_summary(session)

        if error_message:
            session_manager.update_session(
                session_id, status="error", error_message=error_message
            )
            return jsonify({"error": error_message}), 500

        # Update session
        session_manager.update_session(
            session_id,
            status="completed",
            patient_data=patient_data,
            pro_ctcae_data=pro_ctcae_data,
        )

        return jsonify(
            {"patient_data": patient_data, "pro_ctcae_data": pro_ctcae_data}
        ), 200

    except Exception as e:
        session_manager.update_session(session_id, status="error", error_message=str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/conversation/<session_id>/status", methods=["GET"])
def get_conversation_status(session_id: str):
    """Get the status of a conversation session"""
    session = session_manager.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify(session.to_dict()), 200


@app.route("/api/conversation/<session_id>/history", methods=["GET"])
def get_conversation_history(session_id: str):
    """Get the full conversation history"""
    session = session_manager.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    # Filter out system messages for cleaner output
    messages = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in session.messages
        if msg["role"] != "system"
    ]

    return jsonify(
        {
            "session_id": session.session_id,
            "status": session.status,
            "messages": messages,
        }
    ), 200


@app.route("/api/conversation/<session_id>", methods=["DELETE"])
def delete_conversation(session_id: str):
    """Delete a conversation session"""
    if session_manager.delete_session(session_id):
        return jsonify({"message": "Session deleted"}), 200
    return jsonify({"error": "Session not found"}), 404


@app.route("/api/conversations", methods=["GET"])
def list_conversations():
    """List all active conversation sessions"""
    sessions = session_manager.list_sessions()
    return jsonify({"count": len(sessions), "sessions": sessions}), 200


@app.route("/api/cleanup", methods=["POST"])
def cleanup_sessions():
    """Clean up old sessions (older than 24 hours by default)"""
    data = request.get_json() or {}
    max_age_hours = data.get("max_age_hours", 24)

    deleted_count = session_manager.cleanup_old_sessions(max_age_hours)

    return jsonify(
        {
            "message": f"Cleaned up {deleted_count} old session(s)",
            "deleted_count": deleted_count,
        }
    ), 200


@app.route("/", methods=["GET"])
def root():
    """API documentation"""
    return jsonify(
        {
            "name": "Raecer Bot API",
            "version": "1.0.0",
            "description": "Medical conversation API for patient history collection and PRO-CTCAE mapping",
            "endpoints": {
                "GET /api/health": "Health check",
                "POST /api/conversation/start": "Start a new conversation",
                "POST /api/conversation/<session_id>/message": "Send a message",
                "POST /api/conversation/<session_id>/end": "End conversation and get summary",
                "GET /api/conversation/<session_id>/status": "Get conversation status",
                "GET /api/conversation/<session_id>/history": "Get conversation history",
                "DELETE /api/conversation/<session_id>": "Delete a conversation",
                "GET /api/conversations": "List all conversations",
                "POST /api/cleanup": "Clean up old sessions",
            },
        }
    ), 200


# ==================== Application Startup ====================

if __name__ == "__main__":
    print("🚀 Starting Raecer Bot API Server...")
    print("=" * 60)

    try:
        initialize_services()
        print("=" * 60)
        print("✅ All services initialized successfully!")
        print("\n📡 Starting Flask server on http://0.0.0.0:8000")
        print("📚 API documentation available at http://localhost:8000/")
        print("\nPress CTRL+C to stop the server\n")

        app.run(host="0.0.0.0", port=8000, debug=True)

    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        exit(1)
