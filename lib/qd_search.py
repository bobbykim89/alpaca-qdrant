import json
from os import environ
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
import requests

load_dotenv()


class QdSearch:
    qd_client: QdrantClient
    collection_name: str
    model_name: str
    jina_api_key: str
    jina_url: str

    def __init__(self):
        qdrant_url = environ.get('QDRANT_URL')
        qdrant_api_key = environ.get('QDRANT_API_KEY')
        self.qd_client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
        self.collection_name = environ.get('COLLECTION_NAME')
        self.model_name = 'jina-embeddings-v2-small-en'
        self.jina_api_key = environ.get('JINA_API_KEY')
        self.jina_url = "https://api.jina.ai/v1/embeddings"

    def _get_jina_embedding(self, text: str):
        headers = {
            "Authorization": f"Bearer {self.jina_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model_name,
            "input": [text]
        }
        response = requests.post(
            self.jina_url,
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

    def _generate_user_profile(self, quiz_answers) -> str:
        user_profile = []
        for answer in quiz_answers:
            user_profile.append(
                answer['question'] + " " + ", ".join(answer['selections']))

        return "; ".join(user_profile)

    def _search(self, selected_career: str, user_profile: str, limit: int = 1):
        career_vector = self._get_jina_embedding(selected_career)
        profile_vector = self._get_jina_embedding(user_profile)

        results = self.qd_client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                models.Prefetch(query=career_vector,
                                using='career_vector', limit=20),
                models.Prefetch(query=profile_vector,
                                using='description_vector', limit=20)
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            with_payload=True
        )
        return results

    def _format_hits_response(self, hits):
        recommended_degrees_data = []
        for hit in hits.points:
            degree_data = {}
            degree_data["degree_title"] = hit.payload['degreeTitle']
            degree_data["careers"] = hit.payload['careers']
            degree_data["degree_description"] = hit.payload['shortDescription']
            recommended_degrees_data.append(degree_data)

        return json.dumps(recommended_degrees_data, indent=2)

    def qd_search(self, career: str, answers: str):
        user_profile = self._generate_user_profile(quiz_answers=answers)
        hits = self._search(selected_career=career,
                            user_profile=user_profile, limit=5)
        # format degrees
        recommended_degrees = self._format_hits_response(hits=hits)

        return recommended_degrees
