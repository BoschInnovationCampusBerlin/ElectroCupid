import os
from openai import AzureOpenAI
import json
from typing import List, Optional
from dataclasses import dataclass
from typing import Optional
import pandas as pd
from pydantic import BaseModel
from typing import List
from backend.data_cleaner.bom_cleaner import start_cleaner


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
    output_dir: str = "backend\\api\\json_output",
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
        #print(f"CSV content loaded from {lines[i]}")
        # 1. Prepare the prompt with CSV headers and content

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
            temperature=1.0,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            model=deployment_name,
        )
        # 5. Print the response content
       # print(response.choices[0].message.content)


        content = response.choices[0].message.content
        os.makedirs(output_dir, exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content + ",\n")
    # 6. Close the JSON array in the file
    with open(file_path, "a", encoding="utf-8") as f: 
        f.seek(f.tell() - 2, 0)  # Move back to overwrite the last comma and newline
        f.truncate()            # Remove the last comma and newline
        f.seek(f.tell() - 1, 0)  # Move back to overwrite the last comma and newline
        f.truncate()             # Remove the last comma and newline
        f.write("]")  # Close the JSON array

    return True

def parser_agent(csv: str = "cleaned_bom3.csv") -> None:
    """
    Main function to run the parser agent.
    """

    cleaned_bom_path, cleaned_missing_bom_path = start_cleaner(
        input_file=csv,
        #output_file='backend\\api\\clean_output\\cleaned_bom.csv',
        #missing_file='backend\\api\\clean_output\\cleaned_missing_bom.csv'
    )



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
    parsed_data = optimizeBOM(
        client,
        deployment_name=deployment,
        csv_path= cleaned_bom_path  # Path to your CSV file containing the BOM data,
    )

    client.close()

    if parsed_data:
        # Load JSON into a DataFrame
        with open('backend\\api\\json_output\\BOM.json', 'r', encoding='utf-8') as jf:
            data = json.load(jf)

        df = pd.DataFrame(data)
        os.makedirs('backend\\api\\bom_output', exist_ok=True)
        df.to_csv('backend\\api\\bom_output\\output.csv', index=False#) 
                ,sep=';')
        return 'backend\\api\\bom_output\\output.csv'
