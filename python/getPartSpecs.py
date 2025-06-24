import os, sys
from nexarClient import NexarClient


QUERY_MPN = '''
query Search($mpn: String!) {
    supSearchMpn(q: $mpn, limit: 2) {
      results {
        part {
          mpn
          shortDescription
          manufacturer {
            name
          }
          specs {
            attribute {
              name
              shortname
            }
            displayValue
          }
        }
      }
    }
  }
'''

QUERY_FREE_SEARCH = '''
query FreeSearch($q: String!) {
  supSearch(q: $q, limit: 1) {
    results {
      part {
        id
        name
        mpn
        medianPrice1000 {
          quantity
          currency
        }
        category {
          id
          name
        }
        manufacturer {
          name
          homepageUrl
        }
      }
    }
  }
}
'''

QUERY_ALTERNATIVES = '''
query Alternatives($mpn: String!) {
  supSearchMpn(q: $mpn, limit: 1) {
    results {
      part {
        similarParts {
          name
          octopartUrl
          mpn
        }
      }
    }
  }
}
'''

def get_part_info(mpn, nexar):
    """
    Given an MPN, return all attributes of the part using the working NexarClient method and response handling.
    """
    if not mpn:
        return None
    variables = {"mpn": mpn}
    results = nexar.get_query(QUERY_MPN, variables)
    # results is expected to be a dict with 'supSearchMpn' at the top level
    parts = results.get('supSearchMpn', {}).get('results', [])
    if not parts:
        return None
    part = parts[0].get('part', {})
    attributes = []
    for spec in part.get('specs', []):
        attr = spec.get('attribute', {})
        attributes.append({
            'name': attr.get('name'),
            'shortname': attr.get('shortname'),
            'displayValue': spec.get('displayValue')
        })
    return {
        'mpn': part.get('mpn'),
        'shortDescription': part.get('shortDescription'),
        'manufacturer': part.get('manufacturer', {}).get('name'),
        'attributes': attributes
    }


def get_part_alternatives(mpn, nexar):
    """
    Given an MPN, return a list of alternative parts (similarParts).
    """
    if not mpn:
        return None
    variables = {"mpn": mpn}
    response = nexar.get_query(QUERY_ALTERNATIVES, variables)
    results = response.get('supSearchMpn', {}).get('results', [])
    if not results:
        return None
    part = results[0].get('part', {})
    alternatives = part.get('similarParts', [])
    for alt in alternatives:
        get_part_info(alt.get('mpn'), nexar)  # Ensure each alternative part is fetched
    return alternatives


def get_part_by_free_search(search_term, nexar):
    """
    Given a free text search term, return the first matching part's attributes.
    """
    if not search_term:
        return None
    variables = {"q": search_term}
    response = nexar.get_query(QUERY_FREE_SEARCH, variables)
    results = response.get('supSearch', {}).get('results', [])
    if not results:
        return None
    part = results[0].get('part', {})
    return {
        'id': part.get('id'),
        'name': part.get('name'),
        'mpn': part.get('mpn'),
        'medianPrice1000': part.get('medianPrice1000'),
        'category': part.get('category'),
        'manufacturer': part.get('manufacturer')
    }

def get_part_info_and_alternatives(mpn=None, search_term=None, nexar=None):
    """
    Returns a dict with part info and alternatives if mpn is given and found.
    If not found and search_term is given, returns part info from free search.
    No printing, just returns the data.
    """
    if mpn:
        part_info = get_part_info(mpn, nexar)
        if part_info:
            alternatives = get_part_alternatives(mpn, nexar)
            #if alternatives:
              #  alternatives_part_info = [get_part_info(alternative['mpn'], nexar) for alternative in alternatives]
           # if alternatives_part_info:
                
            return {
                'part_info': part_info,
                'alternatives': alternatives
            }
    if search_term:
        part_info_free_search = get_part_by_free_search(search_term, nexar)
        if part_info_free_search:
            return {'part_info_free_search': part_info_free_search}
    return None

""" if __name__ == '__main__':
    clientId = os.environ['NEXAR_CLIENT_ID']
    clientSecret = os.environ['NEXAR_CLIENT_SECRET']
    nexar = NexarClient(clientId, clientSecret)
    if len(sys.argv) < 2:
        print("Usage: python getPartSpecs.py <MPN>")
        sys.exit(1)
    mpn = sys.argv[1]
    part_info = get_part_info(mpn, nexar)
    alternatives = get_part_alternatives(mpn, nexar)
    search_term = input("Enter a search term for free search: ")
    part_info_free_search = get_part_by_free_search(search_term, nexar)
    if part_info:
        print(f"MPN: {part_info['mpn']}")
        print(f"Description: {part_info['shortDescription']}")
        print(f"Manufacturer: {part_info['manufacturer']}")
        print("Attributes:")
        for attr in part_info['attributes']:
            print(f"  {attr['name']} ({attr['shortname']}): {attr['displayValue']}")
        if alternatives:
            print("Alternative Parts:")
            for alt in alternatives:
                #print(f"  Name: {alt['name']}, MPN: {alt['mpn']}, URL: {alt['octopartUrl']}")
                # print the attributes of each alternative part
                print(f"  MPN: {alt['mpn']}")
                print(f"  Description: {alt['name']}")
                print(f"  Octopart URL: {alt['octopartUrl']}")
                # Assuming alt has 'name', 'shortname', and 'displayValue' attributes
                if 'displayValue' in alt:
                    print(f"  Display Value: {alt['displayValue']}")
                else:
                    print("  No display value available.")
                # Print the alternative part's attributes
                if get_part_info(alt['mpn'], nexar):
                    for attr in get_part_info(alt['mpn'], nexar)['attributes']:
                        print(f"    {attr['name']} ({attr['shortname']}): {attr['displayValue']}")
                else:
                    print("  No attributes available for this alternative part.")
                #print(f"  {alt['name']} ({alt['shortname']}): {alt['displayValue']}")
    

    # Example usage of free search
    elif part_info_free_search:
        print(f"Part ID: {part_info_free_search['id']}")
        print(f"Name: {part_info_free_search['name']}")
        print(f"MPN: {part_info_free_search['mpn']}")
        print(f"Median Price (1000): {part_info_free_search['medianPrice1000']}")
        print(f"Category: {part_info_free_search['category']}")
        print(f"Manufacturer: {part_info_free_search['manufacturer']}")
    else:
        print("No part found for the given search term.")
        sys.exit(1) """