import google.genai as genai
from google.genai import types
from pydantic import BaseModel
import json

'''model setup'''

# set up the model (explicit api key for file portability)

GOOGLE_API_KEY = "redacted"
client = genai.Client(api_key = GOOGLE_API_KEY)

# set up an auxiliary augmented sastric name class

class AugmentedSastricName(BaseModel):
    """
    A data class for sastric names that Gemini finds.
    """
    name: str
    definition: str
    context: str
    references: list[str]
    category: str
    gender: str

# set up a function to load names already found, from a JSON file

def load_existing_names(json_file_path: str) -> list[str]:
    """
    Load existing names from a JSON file to exclude them from new searches.
    
    Args:
        json_file_path (str): Path to the JSON file containing existing names.
        
    Returns:
        list[str]: List of existing name strings to exclude.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            existing_names = [item['name'] for item in data]
            print(f"Loaded {len(existing_names)} existing names from {json_file_path}")
            return existing_names
    except FileNotFoundError:
        print(f"Warning: {json_file_path} not found. No existing names to exclude.")
        return []
    except Exception as e:
        print(f"Error loading existing names: {e}")
        return []

'''implement the name extracting function'''

def extract_names(source_str, source_ref, exclude_names_file: str = None):
    """
    A function that processes a sastric text input with its reference and retrieves
    beautiful names from said input, excluding names that are already in a specified file.

    Args:
        source_str (str):         A string with all the source text including verse, 
                                  synonyms, translation, and purport.
        source_ref (str):         A string reference to the source text to guide the model
                                  (ex. Srimad-Bhagavatam Canto 10, Chapter 1, Texts 1-10).
        exclude_names_file (str): Optional path to a JSON file containing names to exclude.

    Returns:
        list[AugmentedSastricName]: 
        A list of AugmentedSastricName objects, where each one represents 
        a beautiful Sanskrit name found in the text and contains the
        following keys:
            - 'name' (str):              The actual beautiful Sanskrit name found, presented
                                         in the nominative case.
            - 'definition' (str):        The definition of the name.
            - 'context' (str):           Relevant information illuminating where this name
                                         comes from and how it's used, etc. This should be
                                         especially comprehensive.
            - 'references' (list[str]):  The specific verse number(s) or sections
                                         (e.g., "SB 1.1.1, 1.1.12 Purport") pointing to
                                         this name.
            - 'category' (str):          The name criteria category this name falls under
                                         (e.g., "Names of Krishna", "Qualities of Krishna's 
                                         devotees").
            - 'gender' (str):            The gender associated with this name ("Male", 
                                         "Female", or "Neutral").
    """

    # load existing names to exclude, if any

    existing_names = []
    if exclude_names_file:
        existing_names = load_existing_names(exclude_names_file)
    
    # create exclusion list for the prompt

    exclusion_text = ""
    if existing_names:
        exclusion_text = f"""IMPORTANT: DO NOT include any of the following names that have already been found:
        
        {', '.join(existing_names)}
        
        Please find ONLY NEW names that are not in the above list."""

        print(exclusion_text)

    # set up the prompt

    command = f"""

    You are a Sanskrit expert interested in identifying beautiful names that are 
    in Sanskrit. The above input comes from the following reference: {source_ref},
    with all the Sanskrit verses transliterated, word-to-word Sanskrit-to-English 
    translations, verse translations, and purports. Your task is to find all relevant 
    Sanskrit names from the above text. These names will be used by someone who gives 
    new names to people of all ages looking to be initiated into the disciplic 
    succession of ISKCON, so feel free to include names of any and all lengths. 
    HOWEVER, you MUST make sure to follow the given criteria for names.

    {exclusion_text}

    The following is the criteria for the names:

    Names of Krishna
    Names of Krishna's incarnations (ex. names of Caitanya, Balaram, Rama, etc.)
    Names of Krishna's male devotees (ex. acaryas, etc.)
    Names of Krishna's female devotees (ex. gopis, radha, etc.)
    Names of Krishna's animals and pets (ex. hamsi, etc.)
    Qualities of Krishna (ex. face, feet, kindness, mercy, etc.)
    Qualities of Krishna's devotees (ex. desire-fulfilling trees, etc.)
    Qualities of bhakti and devotional practice (ex. prema, etc.)
    Names of books (ex. gopala-campu)
    Names of holy places (ex. vrindavan, etc.)

    Your output must include the name, definition, context around the name, 
    the verse number as reference, the criteria category, AND the gender 
    (male/female/neutral). Format your output EXACTLY as follows:

    "Vāsudeva
    Definition: Son of Vasudeva; the divine son of Vasudeva and Devakī
    Context: This is the primary name invoked in the opening verse of 
    Śrīmad-Bhāgavatam. The name indicates both Krishna's earthly parentage and 
    His divine nature. It's used in the invocation "oṁ namo bhagavate vāsudevāya" 
    (I offer my obeisances unto the Personality of Godhead, Vāsudeva).
    Reference: SB 1.1.1, 1.1.12 Purport, 1.1.19
    Category: Names of Krishna
    Gender: Male"

    Note how the name is first, and the definition, context, references, and so 
    on and so forth are all thoroughly provided below. Make sure to be especially 
    comprehensive in any context that you find for the name. Also, make sure to 
    extract ALL names, and DO NOT SKIP ANY, since you are very, very interested in 
    learning all of the names according to the criteria. Lastly, make sure to 
    present the name as the name itself in the correct Sanskrit declension, the 
    nominative case."""

    first_prompt = f"{source_str} \n\n {command}"

    # initiate the response

    print(f"\nBeautiful names from source: {source_ref}\n")

    # print the exclusion information if there are existing names

    if existing_names:
        print(f"Excluding {len(existing_names)} existing names from previous searches\n")

    # calculate the model's first response

    first_response = client.models.generate_content(
        model="gemini-2.5-pro", 
        contents=first_prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=list[AugmentedSastricName]
        )
    )

    # initialize the second prompt with the first response as a Content object

    model_content_for_history = first_response.candidates[0].content

    second_prompt = f"""
    The above is the first response. Now, please continue to find more names
    from the same source text, {source_ref}, that you have not already found.
    Make sure to follow the same criteria as before, and DO NOT repeat any names
    that you have already found in the first response. Format your output exactly
    as before, with the name first, followed by the definition, context, references,
    category. Then, add these to the previous response, so that you have a
    comprehensive list of all the names you have found so far."""

    # create chat contents for the second response as a list of Contents made of Parts

    chat_contents = [
        types.Content(role="user", parts=[types.Part(text=first_prompt)]),
        model_content_for_history,
        types.Content(role="user", parts=[types.Part(text=second_prompt)])
    ]

    # calculate the model's second response

    print("\nContinuing to find more names...\n")

    second_response = client.models.generate_content(
        model="gemini-2.5-pro", 
        contents=chat_contents,
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=list[AugmentedSastricName]
        )
    )

    # print the second response to the console

    print(second_response.text)

    # return the names (type explicitly specified as a reminder)

    found_names: list[AugmentedSastricName] = second_response.parsed
    return found_names

# store the output in a JSON file

def extract_names_to_json(canto, chapter, found_names):
    # convert the pydantic models to dictionaries for JSON serialization
    
    names_data = [name.model_dump() for name in found_names]

    # save the output to a JSON file

    try:
        # read existing content
        with open(f'sb_canto{canto}_chapter{chapter}_names.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        # if file doesn't exist, start with an empty list
        existing_data = []
    except json.JSONDecodeError:
        # if file is empty or malformed, start with an empty list
        existing_data = []

    # append new data

    existing_data.extend(names_data)

    # write updated content back to the file

    with open(f'sb_canto{canto}_chapter{chapter}_names.json', 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

    # print the number of new names appended to the file

    print(f"Appended {len(found_names)} new entries to " \
          "sb_canto{canto}_chapter{chapter}_names.json.")
