import pandas as pd
import json

# Load JSON data
with open('backend\\llm_recommendation\\recommended_part.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Convert to DataFrame and save as CSV
if isinstance(data, list):
    df = pd.DataFrame(data)
    df.reset_index(inplace=True)
else:
    df = pd.DataFrame([data])

df.to_csv('backend\\llm_recommendation\\test.csv', index=False)
