import json
from os import environ
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
import requests

load_dotenv()

qd_client = QdrantClient(
    url=environ.get('QDRANT_URL'),
    api_key=environ.get('QDRANT_API_KEY')
)

collection_name = environ.get('COLLECTION_NAME')
model_name = environ.get('MODEL_NAME')
jina_api_key = environ.get('JINA_API_KEY')
jina_url = "https://api.jina.ai/v1/embeddings"


def get_jina_embedding(text):
    headers = {
        "Authorization": f"Bearer {jina_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_name,
        "input": [text]
    }
    response = requests.post(
        jina_url,
        headers=headers,
        json=data,
        timeout=30
    )
    if response.status_code == 200:
        result = response.json()
        return result["data"][0]["embedding"]
    else:
        raise Exception(
            f"Jina API error: {response.status_code} - {response.text}")


def handler(request):
    if request.method != 'POST':
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method not allowed"})
        }

    try:
        body = request.json()
        selected_career = body.get('selected_career')
        user_profile = body.get('user_profile')
        career_vector = get_jina_embedding(selected_career)
        profile_vector = get_jina_embedding(user_profile)
        results = qd_client.query_points(
            collection_name=collection_name,
            prefetch=[
                models.Prefetch(
                    query=career_vector,
                    using='career_vector',
                    limit=20
                ),
                models.Prefetch(
                    query=profile_vector,
                    using="description_vector",
                    limit=20,
                )
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=1,
            with_payload=True
        )
        return {
            "statusCode": 200,
            "body": json.dumps({"data": results}),
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
