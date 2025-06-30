import csv
import random

def generate_annotation_row():
    return {
        "poi_id": random.randint(1, 10000),
        "user_id": random.randint(1, 10),
        "classification_id": random.randint(1, 13),
        "comments": "this is a comment",
        "confidence_id": None,
        "target_id": None,
        "date": None,
    }

# Number of rows to generate
num_rows = 100000  # adjust as needed

# Output file
output_file = "animal_annotations.csv"

# Field names (CSV headers)
fieldnames = ["id", "comments", "poi_id", "classification_id", "confidence_id", "target_id", "user_id", "date"]

# Write to CSV
with open(output_file, mode="w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for _ in range(num_rows):
        writer.writerow(generate_annotation_row())

print(f"✅ Wrote {num_rows} rows to {output_file}")
