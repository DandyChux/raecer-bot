import os
import json
import datetime
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from ner_extractor import NERExtractor
from pro_ctcae_mapper import ProCtcaeMapper
import config
from dotenv import load_dotenv


def initialize_clients():
    """Initializes and returns the OpenAI client and NER extractor."""
    try:
        load_dotenv()
        openai_client = OpenAI()  # Looks for OPENAI_API_KEY environment variable
    except Exception:  # Fixed: Removed unused variable 'e'
        print(
            "Error: OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."
        )
        exit()

    ner_client = NERExtractor(model_name=config.NER_MODEL_NAME)
    pro_ctcae_mapper = ProCtcaeMapper()
    return openai_client, ner_client, pro_ctcae_mapper


def summarize_and_save(
    conversation_history: list[ChatCompletionMessageParam],
    openai_client: OpenAI,
    pro_ctcae_mapper: ProCtcaeMapper,
):
    """Appends the extraction prompt, gets the JSON summary, and saves it to a file."""
    print("\nConversation ended. Generating final JSON summary...")

    # Add the final extraction prompt to the conversation
    extraction_message: ChatCompletionMessageParam = {
        "role": "user",
        "content": config.JSON_EXTRACTION_PROMPT,
    }
    conversation_history.append(extraction_message)

    json_string = ""  # Fixed: Initialize json_string to avoid unbound variable error
    try:
        response = openai_client.chat.completions.create(
            model=config.CONVERSATIONAL_MODEL,
            messages=conversation_history,
            temperature=0.0,  # Low temperature for factual, deterministic output
        )

        # Fixed: Handle potential None value from response
        message_content = response.choices[0].message.content
        if message_content is None:
            print("\nError: Model returned no content.")
            return

        json_string = message_content

        # Clean the string in case the model adds markdown backticks
        cleaned_json_string = (
            json_string.strip().replace("```json", "").replace("```", "")
        )
        patient_data = json.loads(cleaned_json_string)

        # Save the data
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"data/patient_summary_{timestamp}.json"

        # Ensure the 'data' directory exists
        os.makedirs("data", exist_ok=True)

        with open(file_name, "w") as f:
            json.dump(patient_data, f, indent=4)

        print(f"\n✅ Success! Patient summary saved to '{file_name}'.")
        print("\n--- Summary Data ---")
        print(json.dumps(patient_data, indent=4))

        # Map to PRO-CTCAE codes
        print("\n--- Mapping to PRO-CTCAE ---")
        entries = pro_ctcae_mapper.parse_patient_json(file_name)

        if entries:
            ehr_data = pro_ctcae_mapper.format_for_ehr_entry(entries)
            ehr_data["source_file"] = file_name
            ehr_data["assessment_date"] = timestamp

            # Generate clinical summary
            clinical_summary = pro_ctcae_mapper.generate_clinical_summary(entries)
            ehr_data["clinical_summary"] = clinical_summary

            # Save PRO-CTCAE formatted file
            pro_ctcae_file = f"data/pro_ctcae_{timestamp}.json"
            with open(pro_ctcae_file, "w") as f:
                json.dump(ehr_data, f, indent=2)

            print(f"\n✅ PRO-CTCAE mapping saved to '{pro_ctcae_file}'.")
            print(clinical_summary)
        else:
            print("No symptoms found for PRO-CTCAE mapping.")

    except json.JSONDecodeError:
        print("\nError: Could not parse the JSON output from the model.")
        print("Model Output was:\n", json_string)
    except Exception as e:
        print(f"\nAn error occurred during final summary generation: {e}")


def run_conversation():
    """Main function to run the chatbot conversation."""
    openai_client, ner_client, pro_ctcae_mapper = initialize_clients()

    if ner_client.pipeline is None:
        print("Could not start conversation due to NER model loading failure.")
        return

    # Fixed: Properly type messages list for OpenAI API
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": config.SYSTEM_PROMPT}
    ]

    # Start the conversation
    initial_greeting = "Hello! I'm Cornelius. To help prepare for your upcoming exam, could you tell me a little about your medical history, especially concerning any past allergies or imaging scans?"
    print(f"\n🤖 Cornelius: {initial_greeting}")
    assistant_message: ChatCompletionMessageParam = {
        "role": "assistant",
        "content": initial_greeting,
    }
    messages.append(assistant_message)

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["quit", "done", "exit"]:
            break

        # --- Real-time Entity Extraction with ClinicalBERT ---
        extracted_entities = ner_client.extract_entities(user_input)
        if extracted_entities:
            print(f"🧠 ClinicalBERT Entities Detected: {extracted_entities}")
        # ----------------------------------------------------

        # Add user message to conversation history for GPT-4
        user_message: ChatCompletionMessageParam = {
            "role": "user",
            "content": user_input,
        }
        messages.append(user_message)

        # Get conversational response from GPT-4
        try:
            response = openai_client.chat.completions.create(
                model=config.CONVERSATIONAL_MODEL, messages=messages
            )

            # Fixed: Handle potential None value from response
            bot_response = response.choices[0].message.content
            if bot_response is None:
                print("Error: Model returned no response.")
                break

            print(f"🤖 Cornelius: {bot_response}")
            bot_message: ChatCompletionMessageParam = {
                "role": "assistant",
                "content": bot_response,
            }
            messages.append(bot_message)

            # Check for conversation end phrase
            if "i have everything i need" in bot_response.lower():
                break

        except Exception as e:
            print(f"An error occurred while communicating with OpenAI: {e}")
            break

    # Once the loop breaks, generate and save the summary
    summarize_and_save(messages, openai_client, pro_ctcae_mapper)


if __name__ == "__main__":
    run_conversation()
