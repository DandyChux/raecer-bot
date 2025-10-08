from transformers import TokenClassificationPipeline, pipeline, AutoTokenizer, AutoModelForTokenClassification
import logging

# Configure logging to suppress verbose outputs from transformers
logging.basicConfig(level=logging.ERROR)

class NERExtractor:
    """A class to handle Named Entity Recognition using a ClinicalBERT model."""
    def __init__(self, model_name: str) -> None:
        self.model_name: str = model_name
        self.pipeline: TokenClassificationPipeline | None = self._load_model()

    def _load_model(self):
        """Loads the NER model and tokenizer from Hugging Face."""
        print(f"Loading NER model: '{self.model_name}'... (This may take a moment)")
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            # We use aggregation_strategy="simple" to automatically group B- and I- tags.
            # For example, "shortness", "of", "breath" will be grouped into one entity.
            # Note: Using "token-classification" task instead of "ner" for proper typing
            return pipeline(
                "token-classification",  # Fixed: Changed from "ner" to "token-classification"
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="simple"
            )
        except Exception as e:
            print(f"Error loading NER model: {e}")
            return None

    def extract_entities(self, text: str) -> dict[str, list[str]]:
        """
        Extracts medical entities from a given text and returns them as a dictionary.
        """
        if not self.pipeline:
            return { "error": ["NER model not loaded."]}

        try:
            ner_results = self.pipeline(text)

            # Organize entities by their type (e.g., "DISEASE", "CHEMICAL")
            extracted_data: dict[str, list[str]] = {}
            for entity in ner_results:
                entity_type = entity['entity_group']
                entity_value = entity['word']

                if entity_type not in extracted_data:
                    extracted_data[entity_type] = []

                # Avoid duplicates
                if entity_value not in extracted_data[entity_type]:
                    extracted_data[entity_type].append(entity_value)

            return extracted_data
        except Exception as e:
            print(f"Error during entity extraction: {e}")
            return {}
