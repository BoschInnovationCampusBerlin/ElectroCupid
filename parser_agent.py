import os
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import json
import base64
from typing import List, Optional, Dict
from dataclasses import dataclass
from typing import Optional
import pandas as pd
from pydantic import BaseModel
from typing import List
import csv

class ElectronicObject(BaseModel):
    index: int
    refdes: Optional[str]
    quantity: int
    description: str
    manufacturer_part_number: Optional[str]

def optimizeBOM(
    client: AzureOpenAI,
    deployment_name: str,
    csv_path: str,
    output_dir: str = "bom_output",
) -> List[ElectronicObject]:
    """
    Loads multilingual fields from CSV, uses Azure OpenAI to translate
    and standardize them, and returns a list of HospitalObject instances.
    """
    os.makedirs(output_dir, exist_ok=True)
    # 2. Open the file and read all lines as raw strings
    with open(csv_path, "r", encoding="utf-8") as file:
        lines = file.readlines()  # Reads each line into a list of strings[1]
    file_path = os.path.join(output_dir, "BOM.json")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("[")
    for i in range(1,len(lines)):
        print(f"CSV content loaded from {lines[i]}")
        # 1. Define JSON schema
        # json_schema ={
        #     "type": "ElectronicObject",
        #     "properties": {
        #         "index": {"type": "integer"},
        #         "refdes": {"type": ["string", "null"]},
        #         "quantity": {"type": "integer"},
        #         "description": {"type": "string"},
        #         "manufacturer_part_number": {"type": ["string", "null"]}
        #     },
        #     "required": ["index", "quantity", "description"],
        #     "additionalProperties": False
        # }

        # results = []
        
        
        
        # {
        #     "type": "ElectronicObject",
        #     "properties": {
        #         "index": {"type": "string", "enum": ["Ceiling", "Floor", "Wall"]},
        #         "name": {"type": "string"},
        #         "object_category": {
        #             "type": "string",
        #             "enum": ["Lighting", "Fixed Furniture", "Movable Furniture", "Medical Equipment", "Storage"]
        #         },
        #         "approximate_weight": {"type": "string", "enum": ["Low", "Medium", "High"]},
        #         "is_light": {"type": "boolean"},
        #         "light_type": {
        #             "type": "string",
        #             "enum": ["Area Light", "Spot Light", "Surgical Light", None]
        #         },
        #         "is_door": {"type": "boolean"},
        #         "door_type": {"type": "string", "enum": ["Sliding Door", "Panel Door", None]}
        #     },
        #     "required": ["mounting_location", "name", "object_category", "approximate_weight", "is_light", "is_door"],
        #     "additionalProperties": False
        # }

        Task_prompt = (
            f"Below is a CSV file containing a Bill of Materials (BOM) for a PCBA.  I want you to do the below tasks:\n"
            f"1. Translate all headers to english\n"
            f"2. Fill the data in a provided schema format for each index properly and keep that structure for any type BOM\n"
        )


        prompt = (
            f"{Task_prompt}\n\n"
            f"CSV Headers:{lines[0]}\n"
            f"Input CSV:\n{lines[i]}\n\n"
            "Please output only the optimized CSV without additional commentary."
        )

        # # 2. Convert dimensions to centimeters and build prompt
        # prompt = (
        #     f"Generate a JSON object with EXACTLY these fields about the highlighted hospital object:\n"
        #     f"mounting_location (one of Ceiling, Floor, Wall),\n"
        #     f"name (string),\n"
        #     f"object_category (one of Lighting, Fixed Furniture, Movable Furniture, Medical Equipment, Storage),\n"
        #     f"approximate_weight (one of Low, Medium, High),\n"
        #     f"is_light (boolean),\n"
        #     f"light_type (one of Area Light, Spot Light, Surgical Light or null),\n"
        #     f"is_door (boolean),\n"
        #     f"door_type (one of Sliding Door, Panel Door or null)\n"
        # )

        # # 3. Encode images as base64 for API transmission
        # message_parts = [{"type": "text", "text": prompt}]
        # for idx, png_bytes in enumerate(png_bytes_list, start=1):
        #     if png_bytes:
        #         b64 = base64.b64encode(png_bytes).decode("utf-8")
        #         message_parts.append({
        #             "type": "image_url",
        #             "image_url": {"url": f"data:image/png;base64,{b64}"}
        #         })

        response = client.beta.chat.completions.parse(
            #stream=True,
            messages=[
                {
                    "role": "system",
                    "content": "You are a billing assistant, your task is to optimize the BOM for a PCBA and keep everything in english.",
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            response_format=ElectronicObject,
            # response_format={
            #     "type": "json_schema",
            #     "json_schema": {"name": "hospital_object", "schema": json_schema, "strict": True}
            # },
            #max_completion_tokens=800,
            temperature=1.0,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            model=deployment_name,
        )
        # # 4. Call Azure OpenAI with structured output
        # response = client.chat.completions.create(
        #     model=deployment_name,
        #     messages=[{"role": "user", "content": prompt}],
        #     response_format={
        #         "type": "json_schema",
        #         "json_schema": {"name": "hospital_object", "schema": json_schema, "strict": True}
        #     }
        # )

        # 5. Extract and save response
        # for update in response:
        #     if update.choices:
        #         print(update.choices[0].delta.content or "", end="")
        print(response.choices[0].message.content)
        # print(response.choices[1].message.content)


        content = response.choices[0].message.content
        os.makedirs(output_dir, exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content + ",\n")
        # 6. Deserialize into data class
        # data = json.loads(content)
        # return HospitalObject(
        #     mounting_location=data["mounting_location"],
        #     name=data["name"],
        #     object_category=data["object_category"],
        #     approximate_weight=data["approximate_weight"],
        #     is_light=data["is_light"],
        #     light_type=data.get("light_type"),
        #     is_door=data["is_door"],
        #     door_type=data.get("door_type")
        # )
    with open(file_path, "a", encoding="utf-8") as f: 
        f.seek(f.tell() - 2, 0)  # Move back to overwrite the last comma and newline
        f.truncate()            # Remove the last comma and newline
        f.seek(f.tell() - 1, 0)  # Move back to overwrite the last comma and newline
        f.truncate()             # Remove the last comma and newline
        f.write("]")  # Close the JSON array

# Token provider for Azure AD authentication
endpoint = "https://boschdemov4.openai.azure.com/"
model_name = "gpt-4.1"
deployment = "hackathon-gpt-4.1"

subscription_key = "b7ac5b08650e44f88baf0821f6b40d6e"
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

# Call function
hospital_obj = optimizeBOM(
    client,
    deployment_name=deployment,
    csv_path="cleaned_bom3.csv"  # Path to your CSV file containing the BOM data,
)

client.close()


import json
import pandas as pd

# Load JSON into a DataFrame
with open('bom_output/BOM.json', 'r', encoding='utf-8') as jf:
    data = json.load(jf)

df = pd.DataFrame(data)
df.to_csv('bom_output/output.csv', index=False) 
          #sep=';')



# # Send a test completion request
# print("Sending a test completion job")
# response = client.chat.completions.create(
#     stream=True,
#     messages=[
#         {
#             "role": "system",
#             "content": "You are a helpful assistant.",
#         },
#         {
#             "role": "user",
#             "content": "I am going to Paris, what should I see?",
#         }
#     ],
#     max_completion_tokens=800,
#     temperature=1.0,
#     top_p=1.0,
#     frequency_penalty=0.0,
#     presence_penalty=0.0,
#     model=deployment,
# )

# for update in response:
#     if update.choices:
#         print(update.choices[0].delta.content or "", end="")

# client.close()
