from pypika import Query, Schema, CustomFunction
import httpx
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

API_KEY_HEADER = os.environ.get("API_KEY_HEADER")
API_HEADER_CUSTOMER = os.environ.get("API_HEADER_CUSTOMER")
API_HEADER_ORIGINATOR = os.environ.get("API_HEADER_ORIGINATOR")
API_URL = os.environ.get("API_URL")

print(API_KEY_HEADER)
def main():
    distinct = CustomFunction('DISTINCT', ['*'])
    aqueon = Schema('aqueon')
    q = Query.from_(
        getattr(aqueon, 'fit_info')
    ).select(distinct(aqueon.fit_info.casename)).limit(5)

    
    headers = {
        'x-api-key': os.environ.get("API_KEY"),
        'customer': os.environ.get("API_CUSTOMER"),
        'originator': os.environ.get("API_ORIGINATOR"),
        "Content-Type": "text/plain",
        "Accept": "application/json;q=1.0,application/json;q=0.9,*/*;q=0.8"
    }
    print(q.get_sql())
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f'{API_URL}/dataexplorer/query/tachyus',
            headers=headers,
            data=q.get_sql()
        )
    
    print(response.url)
    if response.status_code == 200:
        df = pd.DataFrame(response.json())
        print(df)
    else:
        print(response.status_code)
        print(response.text)
            
if __name__ == '__main__':
    main()

