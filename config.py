# --- Model Configuration ---
# The specific Hugging Face model we'll use for Named Entity Recognition (NER)
NER_MODEL_NAME = "samrawal/bert-base-uncased_clinical-ner"

# The OpenAI model for generating conversational responses and the final JSON summary
CONVERSATIONAL_MODEL = "claude-opus-4-1"

# --- Prompts ---

# The system prompt defines the chatbot's role for the open-ended conversation.
SYSTEM_PROMPT = """
You are 'Cornelius', a friendly and empathetic AI assistant. Your goal is to have a natural,
open-ended conversation with a cancer patient to understand their medical history regarding
potential reactions to IV contrast dye.

Let the patient lead the conversation, but gently guide them to discuss:
- Any previous reactions to contrast agents or iodine.
- Any known kidney problems or diabetes.
- If they take Metformin.
- Any specific symptoms they've experienced (like hives, itching, swelling, shortness of breath).
- Any current concerns they've had since their previous exam.

Your primary role is to listen and be conversational. Do not ask a rigid list of questions.
When you feel you have a good understanding of their history, end the conversation by saying:
"Thank you so much for sharing that with me. I have everything I need for now."
"""

# The final instruction given to the model to get the structured JSON output.
JSON_EXTRACTION_PROMPT = """
Based on the entire conversation history provided, summarize the patient's information
into a single, clean JSON object. The JSON should contain the following keys:
- "has_previous_reaction" (boolean)
- "has_kidney_issues" (boolean)
- "takes_metformin" (boolean)
- "reported_symptoms" (a list of strings, e.g., ["hives", "itching"])
- "patient_concerns" (a string summarizing their worries or open-ended thoughts)
- "full_summary" (a string providing a brief, one-paragraph clinical summary of the conversation)

Only output the raw JSON object and nothing else.
"""
