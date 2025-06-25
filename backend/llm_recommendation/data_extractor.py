import pandas as pd
from backend.alternatives_finder.getPartSpecs import get_part_info_and_alternatives
from backend.llm_recommendation.recommendation import recommender_agent

def data_extractor(csv_path='backend\\api\\bom_output\\output.csv'):
    # Load only the manufacturer_part_number column, handle bad lines
    try:
        # Read the CSV without specifying usecols to inspect columns
        df = pd.read_csv(csv_path, on_bad_lines='skip')
        print("Available columns:", df.columns.tolist())
        if 'manufacturer_part_number' not in df.columns:
            print("Error: 'manufacturer_part_number' column not found in CSV.")
            return
        df = df[['manufacturer_part_number']]
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Get unique values of manufacturer_part_number
    manufacturer_part_numbers = df['manufacturer_part_number'].unique()

    # Print each manufacturer_part_number
    for part_number in manufacturer_part_numbers:
        part_info, alternatives = get_part_info_and_alternatives(
            mpn=part_number,
            search_term=None,
        )
        recommender_agent(
            json1=part_info,
            json2=alternatives
        )
        print(f"Part Number: {part_info}")