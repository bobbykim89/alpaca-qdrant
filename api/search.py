import json
from os import environ
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
import requests
from http.server import BaseHTTPRequestHandler
import urllib.parse

load_dotenv()


class handler(BaseHTTPRequestHandler):
    qd_client: QdrantClient
    collection_name: str
    model_name: str
    jina_api_key: str
    jina_url: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qdrant_url = environ.get('QDRANT_URL')
        qdrant_api_key = environ.get('QDRANT_API_KEY')
        self.qd_client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
        self.collection_name = environ.get('COLLECTION_NAME')
        self.model_name = environ.get('MODEL_NAME')
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

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Extract search query parameter
        search_query = query_params.get('q', [''])[0]

        # Mock Response for GET request
        response_data = {
            "method": "GET",
            "query": search_query,
            "results": [
                {"id": 1, "title": f"Result for '{search_query}'",
                    "description": "This is a sample result"},
                {"id": 2, "title": f"Another result for '{search_query}'",
                    "description": "This is another sample result"}
            ] if search_query else [],
            "total": 2 if search_query else 0
        }

        # set response headers
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # send response
        self.wfile.write(json.dumps(response_data).encode())

    def do_POST(self):
        # get content length
        content_length = int(self.headers.get('Content-Length', 0))

        # read and parse POST data
        post_data = self.rfile.read(content_length)

        try:
            # Parse JSON data
            data = json.loads(post_data.decode('utf-8'))
            # search_query = data.get('query', '')
            # filters = data.get('filters', {})

            selected_career = data.get('selected_career')
            quiz_answers = data.get('answers')

            user_profile = self._generate_user_profile(
                quiz_answers=quiz_answers)

            hits = self._search(selected_career=selected_career,
                                user_profile=user_profile, limit=5)

            # format data
            recommended_degrees = self._format_hits_response(hits=hits)

            # Set response headers
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # Send response
            self.wfile.write(json.dumps(recommended_degrees).encode())

        except json.JSONDecodeError:
            # Handle invalid JSON
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            error_response = {"error": "Invalid JSON in request body"}
            self.wfile.write(json.dumps(error_response).encode())

        except Exception as e:
            # Handle other processing errors
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            error_response = {"error": f"Processing error: {str(e)}"}
            self.wfile.write(json.dumps(error_response).encode())

    def do_OPTIONS(self):
        # Handle preflight requests for CORS
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
