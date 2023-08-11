from dotenv import load_dotenv
import os
load_dotenv()

regions = {
  "dev": "https://bdaas-api-southcentralus-canary.tachyus.com",
  "latam": "https://bdaas-api-southamerica-east1.tachyus.com",
  "us": "https://bdaas-api-us-central1.tachyus.com",
  "eu": "https://bdaas-api-europe-west6.tachyus.com",
  "asia": "https://bdaas-api-asia-southeast1.tachyus.com",
  "cop": "https://api.conoco.tachyus.com",
  "brazilsouth": "https://bdaas-api-southamerica-east1.tachyus.com",
  "southcentralus": "https://bdaas-api-us-central1.tachyus.com",
  "southeastasia": "https://bdaas-api-asia-southeast1.tachyus.com",
  "northeurope": "https://bdaas-api-europe-west6.tachyus.com"
}

api_region = os.environ.get("API_REGION")
api_url = regions[api_region]


def load_settings():
    return {
        "API_KEY": os.environ.get("API_KEY"),
        "API_CUSTOMER": os.environ.get("API_CUSTOMER"),
        "API_ORIGINATOR": os.environ.get("API_ORIGINATOR"),
        "API_REGION": os.environ.get("API_REGION"),
        'API_URL': api_url,
        "AUTH0_CLIENT_ID": os.environ.get("AUTH0_CLIENT_ID"),
        "AUTH0_CLIENT_SECRET": os.environ.get("AUTH0_CLIENT_SECRET"),
        "AUTH0_DOMAIN": os.environ.get("AUTH0_DOMAIN"),
        "APP_SECRET_KEY": os.environ.get("APP_SECRET_KEY"),
    }