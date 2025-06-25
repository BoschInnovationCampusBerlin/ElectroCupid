import os
from openai import AzureOpenAI
import json
from typing import List, Optional
from dataclasses import dataclass
from typing import Optional
import pandas as pd
from pydantic import BaseModel
from typing import List
#from backend.data_cleaner.bom_cleaner import start_cleaner


class ElectronicObject(BaseModel):
    index: int
    refdes: Optional[str]
    quantity: int
    description: str
    manufacturer_part_number: Optional[str]
    price: Optional[float] = None
    recommended_part_number: Optional[str] = None
    new_price: Optional[float] = None

def AIrecommender(
    client: AzureOpenAI,
    deployment_name: str,
    json1: str,
    json2: str,
) -> List[ElectronicObject]:
    """
    Loads multilingual fields from CSV, uses Azure OpenAI to translate
    and standardize them, and returns a list of HospitalObject instances.
    """
    #print(f"CSV content loaded from {lines[i]}")
    # 1. Prepare the prompt with CSV headers and content

    Task_prompt = (
        f"I am providing you a json with of a given part and a list of alternatives your task is to:\n"
        f"1. You have to find all the parts that exactly math the specs of the given part like size or even contain better specs for certain attributes like temperature torelance.\n"
        f"2. After that find the cheapest alternative part if exists or just give the given part if it is the cheapest in the given json format.  All fields will be same from given part specs just change recommended part number and new price if some alternative part is better else just put null.\n"
    )


    prompt = (
        f"{Task_prompt}\n\n"
        f"Given part specs:{json1}\n"
        f"List of Alternative parts:\n{json2}\n\n"
        "Please output only the optimized json without additional commentary."
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
    print(f"Response content: {content}")

    # Write the JSON content to a file
    output_path = "llm_recommendation/recommended_part.json"
    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.write(content)
    # os.makedirs(output_dir, exist_ok=True)
    # with open(file_path, "a", encoding="utf-8") as f:
    #     f.write(content + ",\n")
    # # 6. Close the JSON array in the file
    # with open(file_path, "a", encoding="utf-8") as f: 
    #     f.seek(f.tell() - 2, 0)  # Move back to overwrite the last comma and newline
    #     f.truncate()            # Remove the last comma and newline
    #     f.seek(f.tell() - 1, 0)  # Move back to overwrite the last comma and newline
    #     f.truncate()             # Remove the last comma and newline
        # f.write("]")  # Close the JSON array

    return True

def recommender_agent(json1, json2) -> None:
    """
    Main function to run the parser agent.
    """

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
    recommended_data = AIrecommender(
        client,
        deployment_name=deployment,
        json1=json1,  # Path to your CSV file containing the BOM data,
        json2=json2  # Path to your CSV file containing the BOM data,
    )

    client.close()

    # if parsed_data:
    #     # Load JSON into a DataFrame
    #     with open('backend\\api\\json_output\\BOM.json', 'r', encoding='utf-8') as jf:
    #         data = json.load(jf)

    #     df = pd.DataFrame(data)
    #     os.makedirs('backend\\api\\bom_output', exist_ok=True)
    #     df.to_csv('backend\\api\\bom_output\\output.csv', index=False#) 
    #             ,sep=';')
    #     return 'backend\\api\\bom_output\\output.csv'
#print("Current working directory:", os.getcwd())
with open('llm_recommendation\\part_info.json', 'r', encoding='utf-8') as f1:
    json1 = f1.read()

with open('llm_recommendation\\alternatives.json', 'r', encoding='utf-8') as f2:
    json2 = f2.read()
recommender_agent(json1, json2)
