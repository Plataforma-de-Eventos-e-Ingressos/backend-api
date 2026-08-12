import os
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_BASE_URL = "https://api.themoviedb.org/3"


TMDB_BEARER_TOKEN = os.getenv("TMDB_BEARER_TOKEN", "COLE_SEU_TOKEN_AQUI")

def search_movies(query: str):
    url = f"{TMDB_BASE_URL}/search/multi?query={query}&language=pt-BR&page=1"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_BEARER_TOKEN}"
    }
    
    print(TMDB_BEARER_TOKEN)
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print(f"✅ TMDb API Response: {response.json()}")  
        return response.json().get("results", [])
    else:
        print(f"❌ Erro TMDb: {response.status_code} - {response.text}")
        
    return []