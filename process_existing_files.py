"""
Utility script to process existing patient summary files and generate PRO-CTCAE mappings
Run this to batch process all your existing patient conversation JSONs
"""

import os
import sys
import json
from pro_ctcae_mapper import ProCtcaeMapper


def process_single_file(
    mapper: ProCtcaeMapper, file_path: str, output_dir: str = "data"
) -> bool:
    """
    Process a single patient summary file
    Returns True if successful, False otherwise
    """
    try:
        filename = os.path.basename(file_path)

        # Parse and extract PRO-CTCAE entries
        entries = mapper.parse_patient_json(file_path)

        if not entries:
            print("  ⚠️  No symptoms found to map")
            return False

        # Format for EHR
        ehr_data = mapper.format_for_ehr_entry(entries)

        # Extract timestamp from filename (patient_summary_YYYYMMDD_HHMMSS.json)
        timestamp = filename.replace("patient_summary_", "").replace(".json", "")

        # Add metadata
        ehr_data["source_file"] = filename
        ehr_data["assessment_date"] = timestamp

        # Generate clinical summary
        clinical_summary = mapper.generate_clinical_summary(entries)
        ehr_data["clinical_summary"] = clinical_summary

        # Save PRO-CTCAE formatted file
        output_filename = filename.replace("patient_summary_", "pro_ctcae_")
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "w") as f:
            json.dump(ehr_data, f, indent=2)

        print(f"  ✅ PRO-CTCAE mapping saved to: {output_filename}")
        print(f"  📊 Mapped {len(entries)} symptom(s)")

        return True

    except Exception as e:
        print(f"  ❌ Error processing file: {e}")
        return False


def main():
    """Process all existing patient summary files"""

    # Check if data directory exists
    if not os.path.exists("data"):
        print("Error: 'data' directory not found.")
        print("Please run this script from the raecer-bot directory.")
        sys.exit(1)

    # Initialize mapper
    print("🔧 Initializing PRO-CTCAE mapper...")
    mapper = ProCtcaeMapper()

    # Get all patient summary files
    json_files = [
        f
        for f in os.listdir("data")
        if f.startswith("patient_summary_") and f.endswith(".json")
    ]

    if not json_files:
        print("No patient summary files found in the data directory.")
        sys.exit(0)

    print(f"\n📁 Found {len(json_files)} patient summary file(s) to process.\n")
    print("=" * 60)

    successful = 0
    skipped = 0
    failed = 0

    # Process each file
    for filename in sorted(json_files):
        file_path = os.path.join("data", filename)

        # Check if PRO-CTCAE file already exists
        pro_ctcae_filename = filename.replace("patient_summary_", "pro_ctcae_")
        pro_ctcae_path = os.path.join("data", pro_ctcae_filename)

        print(f"\n📄 Processing: {filename}")

        if os.path.exists(pro_ctcae_path):
            print("  ⏭️  Skipping (PRO-CTCAE file already exists)")
            skipped += 1
            continue

        if process_single_file(mapper, file_path):
            successful += 1
        else:
            failed += 1

    # Print summary
    print("\n" + "=" * 60)
    print("✅ Processing complete!\n")
    print(f"  Successful: {successful}")
    print(f"  Skipped:    {skipped}")
    print(f"  Failed:     {failed}")
    print(f"  Total:      {len(json_files)}")


if __name__ == "__main__":
    main()
