import httpx
from dotenv import load_dotenv
import os
import pandas as pd
load_dotenv()

def main():

    headers = {
        'x-api-key': os.environ.get("API_KEY"),
        'customer': os.environ.get("API_CUSTOMER"),
        'originator': os.environ.get("API_ORIGINATOR"),
        "Accept": "application/json;q=1.0,application/json;q=0.9,*/*;q=0.8"
    }
    with httpx.Client(timeout=30) as client:
        response = client.get(
            f'{os.environ.get("API_URL")}/fit/TEST20221130chichimenegbWLv8B0FF202358320',
            headers=headers,
        )
    
    data = response.json()
    
    file_path = data['files']['intermediateOutput']['fit_output.json']
    with httpx.Client(timeout=30) as client:
        response_file = client.get(
            f'{os.environ.get("API_URL")}/{file_path}',
            headers=headers,
        )

    data_file = response_file.json()
    print(data_file)
    
if __name__ == '__main__':
    main()