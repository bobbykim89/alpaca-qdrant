import json
from os import environ
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv

load_dotenv()

qd_client = QdrantClient(
    url=environ.get('QDRANT_URL'),
    api_key=environ.get('QDRANT_API_KEY')
)

collection_name = environ.get('COLLECTION_NAME')
model_name = environ.get('MODEL_NAME')


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
        results = qd_client.query_points(
            collection_name=collection_name,
            prefetch=[
                models.Prefetch(
                    query=models.Document(
                        text=selected_career, model=model_name
                    ),
                    using='career_vector',
                    limit=20
                ),
                models.Prefetch(
                    query=models.Document(
                        text=user_profile, model=model_name
                    ),
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
