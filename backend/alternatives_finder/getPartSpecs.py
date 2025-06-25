import os, sys
import csv
import json
from nexarClient import NexarClient


clientId = "724b870d-80a3-403c-a1fe-7d4dfe926ee7"
clientSecret = "7yMg2aANL81GCJsvTTrh_g8uTOhpULDrBpCR"
QUERY_MPN = '''
query Search($mpn: String!) {
    supSearchMpn(q: $mpn, limit: 1) {
      results {
        part {
          mpn
          shortDescription
          manufacturer { name }
          specs { attribute { name shortname } displayValue }
          sellers { company { name } offers { prices { quantity price } } }
          similarParts {
            name
            octopartUrl
            mpn
            shortDescription
            manufacturer { name }
            specs { attribute { name shortname } displayValue }
            sellers { company { name } offers { prices { quantity price } } }
          }
        }
      }
    }
  }
'''


def get_part_info_and_alternatives(mpn=None, search_term=None, nexar=None):
    """
    Returns a dict with part info and alternatives using a single API call for the main part and its alternatives.
    Only supports MPN-based lookup now.
    Returns a tuple of (part_info_json, alternatives_json) as JSON strings, or (None, None) if not found.
    """
    if mpn:
        variables = {"mpn": mpn}
        results = nexar.get_query(QUERY_MPN, variables)
        parts = results.get('supSearchMpn', {}).get('results', [])
        if not parts:
            return None, None
        part = parts[0].get('part', {})
        # Main part info
        attributes = []
        for spec in part.get('specs', []):
            attr = spec.get('attribute', {})
            attributes.append({
                'name': attr.get('name'),
                'shortname': attr.get('shortname'),
                'displayValue': spec.get('displayValue')
            })
        prices = []
        for seller in part.get('sellers', []):
            company = seller.get('company', {}).get('name')
            for offer in seller.get('offers', []):
                for price_info in offer.get('prices', []):
                    price_entry = {
                        'company': company,
                        'quantity': price_info.get('quantity'),
                        'price': price_info.get('price')
                    }
                    prices.append(price_entry)
        part_info = {
            'mpn': part.get('mpn'),
            'shortDescription': part.get('shortDescription'),
            'manufacturer': part.get('manufacturer', {}).get('name'),
            'attributes': attributes,
            'prices': prices
        }
        # Alternatives
        alternatives = []
        for alt in part.get('similarParts', []):
            alt_attributes = []
            for spec in alt.get('specs', []):
                attr = spec.get('attribute', {})
                alt_attributes.append({
                    'name': attr.get('name'),
                    'shortname': attr.get('shortname'),
                    'displayValue': spec.get('displayValue')
                })
            alt_prices = []
            for seller in alt.get('sellers', []):
                company = seller.get('company', {}).get('name')
                for offer in seller.get('offers', []):
                    for price_info in offer.get('prices', []):
                        price_entry = {
                            'company': company,
                            'quantity': price_info.get('quantity'),
                            'price': price_info.get('price')
                        }
                        alt_prices.append(price_entry)
            alternatives.append({
                'name': alt.get('name'),
                'octopartUrl': alt.get('octopartUrl'),
                'mpn': alt.get('mpn'),
                'shortDescription': alt.get('shortDescription'),
                'manufacturer': alt.get('manufacturer', {}).get('name'),
                'attributes': alt_attributes,
                'prices': alt_prices
            })
        part_info_json = json.dumps(part_info, ensure_ascii=False, indent=2)
        alternatives_json = json.dumps(alternatives, ensure_ascii=False, indent=2)
        return part_info_json, alternatives_json
    # Only MPN-based lookup is supported in this version
    return None, None



nexar = NexarClient(clientId, clientSecret)

lookup_result = get_part_info_and_alternatives(mpn="LM358", search_term=None, nexar=nexar)
part_info_json, alternatives_json = lookup_result

def get_mpn_from_csv(csv_path, mpn_column_name="mpn"):
    """
    Reads a CSV file, finds the MPN (Manufacturer Part Number) column, and returns a list of MPNs.
    By default, looks for a column named 'mpn'.
    """
    mpns = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            mpn = row.get(mpn_column_name)
            if mpn:
                mpns.append(mpn)
    return mpns
#mpns = get_mpn_from_csv('/Users/mbengamina/Downloads/output_comma.csv', mpn_column_name="manufacturer_part_number")
""" for mpn in mpns:
    result = get_part_info_and_alternatives(mpn=mpn, nexar=nexar)
    print(result) """

#print(get_part_info_and_alternatives(mpn="LM358", search_term=None, nexar=nexar))

# --- Save part_info and alternatives as separate JSON files ---

""" if part_info_json and alternatives_json:
    print('part_info_json:', part_info_json)
    print('alternatives_json:', alternatives_json)
else:
    print('No part_info found to save.') """
