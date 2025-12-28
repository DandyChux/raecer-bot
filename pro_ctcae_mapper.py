"""
PRO-CTCAE Symptom Mapper
Maps patient-reported symptoms from conversation JSON to PRO-CTCAE codes
"""

import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Severity(Enum):
    """PRO-CTCAE severity levels"""

    NONE = 0
    MILD = 1
    MODERATE = 2
    SEVERE = 3
    VERY_SEVERE = 4


class Frequency(Enum):
    """PRO-CTCAE frequency levels"""

    NEVER = 0
    RARELY = 1
    OCCASIONALLY = 2
    FREQUENTLY = 3
    ALMOST_CONSTANTLY = 4


class Interference(Enum):
    """PRO-CTCAE interference levels"""

    NOT_AT_ALL = 0
    A_LITTLE_BIT = 1
    SOMEWHAT = 2
    QUITE_A_BIT = 3
    VERY_MUCH = 4


@dataclass
class ProCtcaeItem:
    """Represents a PRO-CTCAE item with its attributes"""

    symptom_term: str
    code: str
    attributes: list[str]  # Can be: Frequency, Severity, Interference, Presence
    description: str


@dataclass
class ProCtcaeEntry:
    """Represents a patient's PRO-CTCAE entry"""

    symptom_term: str
    code: str
    severity: int | None = None
    frequency: int | None = None
    interference: int | None = None
    presence: bool | None = None
    raw_text: str | None = None  # Original patient-reported text


class ProCtcaeMapper:
    """Maps patient symptoms to PRO-CTCAE codes"""

    def __init__(self):
        # Define PRO-CTCAE items relevant to contrast reactions
        self.pro_ctcae_items: dict[str, ProCtcaeItem] = {
            # Cutaneous symptoms
            "hives": ProCtcaeItem(
                symptom_term="Hives",
                code="PRO-CTCAE_hives",
                attributes=["Presence"],
                description="Hives (urticaria)",
            ),
            "itching": ProCtcaeItem(
                symptom_term="Itching",
                code="PRO-CTCAE_itching",
                attributes=["Severity"],
                description="Pruritus (itching)",
            ),
            "rash": ProCtcaeItem(
                symptom_term="Rash",
                code="PRO-CTCAE_rash",
                attributes=["Presence"],
                description="Skin rash",
            ),
            "skin_redness": ProCtcaeItem(
                symptom_term="Skin redness",
                code="PRO-CTCAE_erythema",
                attributes=["Presence"],
                description="Erythema or skin redness",
            ),
            # Respiratory symptoms
            "shortness_of_breath": ProCtcaeItem(
                symptom_term="Shortness of breath",
                code="PRO-CTCAE_dyspnea",
                attributes=["Severity", "Interference"],
                description="Dyspnea (shortness of breath)",
            ),
            "wheezing": ProCtcaeItem(
                symptom_term="Wheezing",
                code="PRO-CTCAE_wheezing",
                attributes=["Severity"],
                description="Wheezing",
            ),
            "cough": ProCtcaeItem(
                symptom_term="Cough",
                code="PRO-CTCAE_cough",
                attributes=["Severity", "Interference"],
                description="Cough",
            ),
            # Circulatory symptoms
            "swelling": ProCtcaeItem(
                symptom_term="Swelling",
                code="PRO-CTCAE_swelling",
                attributes=["Frequency", "Severity", "Interference"],
                description="Edema (swelling)",
            ),
            "heart_palpitations": ProCtcaeItem(
                symptom_term="Heart palpitations",
                code="PRO-CTCAE_palpitations",
                attributes=["Frequency", "Severity"],
                description="Heart palpitations",
            ),
            # Gastrointestinal symptoms
            "nausea": ProCtcaeItem(
                symptom_term="Nausea",
                code="PRO-CTCAE_nausea",
                attributes=["Frequency", "Severity"],
                description="Nausea",
            ),
            "vomiting": ProCtcaeItem(
                symptom_term="Vomiting",
                code="PRO-CTCAE_vomiting",
                attributes=["Frequency", "Severity"],
                description="Vomiting",
            ),
            # General symptoms
            "chills": ProCtcaeItem(
                symptom_term="Chills",
                code="PRO-CTCAE_chills",
                attributes=["Frequency", "Severity"],
                description="Chills",
            ),
            "dizziness": ProCtcaeItem(
                symptom_term="Dizziness",
                code="PRO-CTCAE_dizziness",
                attributes=["Severity", "Interference"],
                description="Dizziness",
            ),
            "headache": ProCtcaeItem(
                symptom_term="Headache",
                code="PRO-CTCAE_headache",
                attributes=["Frequency", "Severity", "Interference"],
                description="Headache",
            ),
            "anxiety": ProCtcaeItem(
                symptom_term="Anxious",
                code="PRO-CTCAE_anxiety",
                attributes=["Frequency", "Severity", "Interference"],
                description="Anxiety",
            ),
            "chest_tightness": ProCtcaeItem(
                symptom_term="Chest pain",
                code="PRO-CTCAE_chest_pain",
                attributes=["Frequency", "Severity", "Interference"],
                description="Chest tightness or pain",
            ),
        }

        # Symptom mapping dictionary (maps various terms to standardized keys)
        self.symptom_mappings: dict[str, str] = {
            # Hives variations
            "hives": "hives",
            "urticaria": "hives",
            "welts": "hives",
            # Itching variations
            "itching": "itching",
            "itchy": "itching",
            "pruritus": "itching",
            "itch": "itching",
            # Swelling variations
            "swelling": "swelling",
            "edema": "swelling",
            "puffiness": "swelling",
            "angioedema": "swelling",
            "facial swelling": "swelling",
            "throat swelling": "swelling",
            # Breathing variations
            "shortness of breath": "shortness_of_breath",
            "difficulty breathing": "shortness_of_breath",
            "breathlessness": "shortness_of_breath",
            "dyspnea": "shortness_of_breath",
            "trouble breathing": "shortness_of_breath",
            # Wheezing
            "wheezing": "wheezing",
            "wheeze": "wheezing",
            # Rash variations
            "rash": "rash",
            "skin reaction": "rash",
            "eruption": "rash",
            # Other symptoms
            "nausea": "nausea",
            "vomiting": "vomiting",
            "dizziness": "dizziness",
            "dizzy": "dizziness",
            "headache": "headache",
            "chest tightness": "chest_tightness",
            "chest pain": "chest_tightness",
            "anxiety": "anxiety",
            "anxious": "anxiety",
            "palpitations": "heart_palpitations",
            "heart racing": "heart_palpitations",
        }

    def normalize_symptom(self, symptom: str) -> str | None:
        """Normalize a symptom string to match PRO-CTCAE terminology"""
        symptom_lower = symptom.lower().strip()
        return self.symptom_mappings.get(symptom_lower)

    def estimate_severity(self, symptom: str, context: dict[str, Any]) -> int | None:
        """
        Estimate severity based on symptom and context
        Returns severity level (0-4) or None if not applicable
        """
        # Check if patient had a previous reaction (might indicate more severe)
        has_previous = context.get("has_previous_reaction", False)

        # Default severity mappings based on common patterns
        severity_keywords = {
            "mild": Severity.MILD.value,
            "moderate": Severity.MODERATE.value,
            "severe": Severity.SEVERE.value,
            "very severe": Severity.VERY_SEVERE.value,
            "slight": Severity.MILD.value,
            "bad": Severity.MODERATE.value,
            "terrible": Severity.SEVERE.value,
            "extreme": Severity.VERY_SEVERE.value,
        }

        # Check full summary for severity indicators
        full_summary = context.get("full_summary", "").lower()

        for keyword, level in severity_keywords.items():
            if keyword in full_summary:
                return level

        # Default severity based on symptom type and history
        if has_previous:
            # Previous reactions might be more severe
            critical_symptoms = [
                "shortness_of_breath",
                "chest_tightness",
                "throat_swelling",
            ]
            normalized = self.normalize_symptom(symptom)
            if normalized in critical_symptoms:
                return Severity.MODERATE.value
            return Severity.MILD.value

        return Severity.MILD.value  # Default to mild if unknown

    def parse_patient_json(self, json_file_path: str) -> list[ProCtcaeEntry]:
        """Parse patient JSON file and extract PRO-CTCAE entries"""
        entries = []

        # Load the JSON file
        with open(json_file_path, "r") as f:
            data = json.load(f)

        # Extract reported symptoms
        reported_symptoms = data.get("reported_symptoms", [])

        for symptom in reported_symptoms:
            normalized = self.normalize_symptom(symptom)

            if normalized and normalized in self.pro_ctcae_items:
                item = self.pro_ctcae_items[normalized]
                entry = ProCtcaeEntry(
                    symptom_term=item.symptom_term, code=item.code, raw_text=symptom
                )

                # Set attributes based on what's available for this symptom
                if "Severity" in item.attributes:
                    entry.severity = self.estimate_severity(symptom, data)

                if "Presence" in item.attributes:
                    entry.presence = True  # If reported, it's present

                if "Frequency" in item.attributes:
                    # Default to occasionally for reported symptoms
                    entry.frequency = Frequency.OCCASIONALLY.value

                if "Interference" in item.attributes:
                    # Estimate based on severity
                    if entry.severity is not None:
                        if entry.severity >= Severity.SEVERE.value:
                            entry.interference = Interference.QUITE_A_BIT.value
                        elif entry.severity >= Severity.MODERATE.value:
                            entry.interference = Interference.SOMEWHAT.value
                        else:
                            entry.interference = Interference.A_LITTLE_BIT.value

                entries.append(entry)
            elif symptom and not normalized:
                # Log unmapped symptoms for future improvement
                print(f"Warning: Unmapped symptom '{symptom}'")

        # Check for anxiety if patient has concerns
        concerns = data.get("patient_concerns", "")
        if (
            concerns
            and "concern" in concerns.lower()
            and concerns.lower() != "no concerns"
        ):
            anxiety_item = self.pro_ctcae_items["anxiety"]
            anxiety_entry = ProCtcaeEntry(
                symptom_term=anxiety_item.symptom_term,
                code=anxiety_item.code,
                severity=Severity.MILD.value,
                frequency=Frequency.OCCASIONALLY.value,
                interference=Interference.A_LITTLE_BIT.value,
                raw_text="Patient expressed concerns",
            )
            entries.append(anxiety_entry)

        return entries

    def format_for_ehr_entry(self, entries: list[ProCtcaeEntry]) -> dict[str, Any]:
        """
        Format PRO-CTCAE entries for EHR system entry
        Returns structured data ready for clinical documentation
        """
        ehr_data: dict[str, Any] = {
            "pro_ctcae_version": "1.0",
            "assessment_date": None,  # Will be set when processing
            "entries": [],
        }

        for entry in entries:
            entry_dict: dict[str, Any] = {
                "symptom_term": entry.symptom_term,
                "code": entry.code,
                "patient_reported_text": entry.raw_text,
            }

            # Add attributes with their values
            if entry.severity is not None:
                entry_dict["severity"] = {
                    "value": entry.severity,
                    "label": Severity(entry.severity).name.replace("_", " ").title(),
                }

            if entry.frequency is not None:
                entry_dict["frequency"] = {
                    "value": entry.frequency,
                    "label": Frequency(entry.frequency).name.replace("_", " ").title(),
                }

            if entry.interference is not None:
                entry_dict["interference"] = {
                    "value": entry.interference,
                    "label": Interference(entry.interference)
                    .name.replace("_", " ")
                    .title(),
                }

            if entry.presence is not None:
                entry_dict["presence"] = entry.presence

            ehr_data["entries"].append(entry_dict)

        return ehr_data

    def generate_clinical_summary(self, entries: list[ProCtcaeEntry]) -> str:
        """Generate a clinical summary from PRO-CTCAE entries"""
        if not entries:
            return "No PRO-CTCAE symptoms reported."

        summary = "PRO-CTCAE Assessment Summary:\n"
        summary += "-" * 40 + "\n"

        # Group by severity for summary
        severe_symptoms = []
        moderate_symptoms = []
        mild_symptoms = []

        for entry in entries:
            symptom_text = f"{entry.symptom_term} ({entry.code})"

            if entry.severity is not None:
                if entry.severity >= Severity.SEVERE.value:
                    severe_symptoms.append(symptom_text)
                elif entry.severity >= Severity.MODERATE.value:
                    moderate_symptoms.append(symptom_text)
                else:
                    mild_symptoms.append(symptom_text)
            else:
                # For presence-only symptoms
                mild_symptoms.append(symptom_text)

        if severe_symptoms:
            summary += f"SEVERE: {', '.join(severe_symptoms)}\n"
        if moderate_symptoms:
            summary += f"MODERATE: {', '.join(moderate_symptoms)}\n"
        if mild_symptoms:
            summary += f"MILD: {', '.join(mild_symptoms)}\n"

        summary += "-" * 40 + "\n"
        summary += f"Total symptoms reported: {len(entries)}\n"

        return summary

    def process_all_patient_files(
        self, data_directory: str = "data"
    ) -> list[dict[str, str]]:
        """
        Process all patient JSON files in the data directory
        Returns a list of processed PRO-CTCAE data for each patient
        """
        results = []

        # Get all JSON files in the data directory
        json_files = [
            f
            for f in os.listdir(data_directory)
            if f.startswith("patient_summary_") and f.endswith(".json")
        ]

        for filename in json_files:
            file_path = os.path.join(data_directory, filename)
            print(f"\nProcessing: {filename}")

            # Parse and extract PRO-CTCAE entries
            entries = self.parse_patient_json(file_path)

            # Format for EHR
            ehr_data = self.format_for_ehr_entry(entries)

            # Add metadata
            ehr_data["source_file"] = filename
            ehr_data["assessment_date"] = filename.split("_")[2].split(".")[
                0
            ]  # Extract date from filename

            # Generate summary
            clinical_summary = self.generate_clinical_summary(entries)
            ehr_data["clinical_summary"] = clinical_summary

            results.append(ehr_data)

            # Print summary
            print(clinical_summary)

            # Save PRO-CTCAE formatted file
            output_filename = filename.replace("patient_summary_", "pro_ctcae_")
            output_path = os.path.join(data_directory, output_filename)

            with open(output_path, "w") as f:
                json.dump(ehr_data, f, indent=2)

            print(f"Saved PRO-CTCAE data to: {output_filename}")

        return results


# Example usage and integration
def main():
    """Demonstrate PRO-CTCAE mapping functionality"""
    mapper = ProCtcaeMapper()

    # Process a single file
    sample_file = "data/patient_summary_20250924_181332.json"

    if os.path.exists(sample_file):
        print(f"Processing single file: {sample_file}")
        entries = mapper.parse_patient_json(sample_file)

        print("\n=== PRO-CTCAE Entries ===")
        for entry in entries:
            print(f"\nSymptom: {entry.symptom_term}")
            print(f"  Code: {entry.code}")
            print(f"  Original text: {entry.raw_text}")
            if entry.severity is not None:
                print(f"  Severity: {Severity(entry.severity).name}")
            if entry.frequency is not None:
                print(f"  Frequency: {Frequency(entry.frequency).name}")
            if entry.interference is not None:
                print(f"  Interference: {Interference(entry.interference).name}")
            if entry.presence is not None:
                print(f"  Presence: {entry.presence}")

        # Generate EHR-ready format
        ehr_data = mapper.format_for_ehr_entry(entries)
        print("\n=== EHR-Ready Format ===")
        print(json.dumps(ehr_data, indent=2))

    # Process all files in the data directory
    print("\n" + "=" * 50)
    print("Processing all patient files...")
    print("=" * 50)
    results = mapper.process_all_patient_files("data")

    print(f"\n✅ Processed {len(results)} patient files")


if __name__ == "__main__":
    main()
