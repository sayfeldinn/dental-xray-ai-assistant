import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
docs_dir = BASE_DIR / "documents"
docs_dir.mkdir(exist_ok=True)

jsonl_file = BASE_DIR / "Dental_Cases_TrainingData.jsonl"

if not jsonl_file.exists():
    print(f"Error: Could not find '{jsonl_file.name}' in {BASE_DIR}")
    exit(1)

count = 0
skipped = 0

with open(jsonl_file, "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
            
        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Warning: Skipping line {line_num} due to JSON decode error: {e}")
            skipped += 1
            continue

        messages = data.get("messages", [])
        
        user_content = ""
        assistant_content = ""
        
        for msg in messages:
            if msg.get("role") == "user":
                user_content = msg.get("content", "")
            elif msg.get("role") == "assistant":
                assistant_content = msg.get("content", "")
        
        # Combine into clean clinical context
        clean_text = f"PATIENT CASE & CLINICAL PRESENTATION:\n{user_content}\n\nMANAGEMENT PLAN & DRUG DECISION:\n{assistant_content}"
        
        count += 1
        output_file = docs_dir / f"case_{count}.txt"
        output_file.write_text(clean_text, encoding="utf-8")

print(f"Success! Converted {count} clinical cases into individual text files in '{docs_dir.relative_to(BASE_DIR)}/'.")
if skipped > 0:
    print(f"Skipped {skipped} invalid lines.")