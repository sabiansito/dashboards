import httpx
from dotenv import load_dotenv
import os
import pandas as pd
import io
load_dotenv()

def main():

    headers = {
        'x-api-key': os.environ.get("API_KEY"),
        'customer': os.environ.get("API_CUSTOMER"),
        'originator': os.environ.get("API_ORIGINATOR"),
        "Accept": "application/json;q=1.0,application/json;q=0.9,*/*;q=0.8"
    }
    
    params = {
        'fit':'ChichimeneDec2022BFF20233131545'
    }
    
    with httpx.Client(timeout=30) as client:
        response = client.get(
            f'{os.environ.get("API_URL")}/predict',
            headers=headers,
            params=params
        )
    
    data = response.json()
    last_data = data[-1]
    case_name = last_data['name']
    
    with httpx.Client(timeout=30) as client:
        response_files = client.get(
            f'{os.environ.get("API_URL")}/predict/{case_name}/files',
            headers=headers,
        )
    
    files = response_files.json()
    print(files['files']['final']['SensitivityMatrixCumWWell.csv'])
    file_path = files['files']['final']['SensitivityMatrixCumWWell.csv']
    
    with httpx.Client(timeout=30) as client:
        response_file_csv = client.get(
            f'{os.environ.get("API_URL")}/{file_path}',
            headers=headers,
        )
    
    csv_data = response_file_csv.content.decode('utf-8')
    dataa = io.StringIO(csv_data)
    df = pd.read_csv(dataa)
    print(type(csv_data))
    print(df.head())
    
    
if __name__ == '__main__':
    main()