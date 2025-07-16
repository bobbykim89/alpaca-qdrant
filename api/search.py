import json
from os import environ
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
import requests
from http.server import BaseHTTPRequestHandler
import urllib.parse

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


class handler(BaseHTTPRequestHandler):
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

            # # Mock response for POST request
            # response_data = {
            #     "method": "POST",
            #     "query": search_query,
            #     "filters": filters,
            #     "results": [
            #         {"id": 1, "title": f"Advanced result for '{search_query}'",
            #             "description": "This is a filtered result"},
            #         {"id": 2, "title": f"Filtered result for '{search_query}'",
            #             "description": "This matches your filters"}
            #     ] if search_query else [],
            #     "total": 2 if search_query else 0
            # }

            # Set response headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # Send response
            self.wfile.write(json.dumps(data).encode())

        except json.JSONDecodeError:
            # Handle invalid JSON
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            error_response = {"error": "Invalid JSON in request body"}
            self.wfile.write(json.dumps(error_response).encode())

    def do_OPTIONS(self):
        # Handle preflight requests for CORS
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

# def handler(request):
#     if request['method'] != 'POST':
#         return {
#             "statusCode": 405,
#             "headers": {"Content-Type": "application/json"},
#             "body": json.dumps({"error": "Method not allowed"})
#         }

#     try:
#         body = json.loads(request['body'])
#         selected_career = body.get('selected_career')
#         user_profile = body.get('user_profile')
#         career_vector = get_jina_embedding(selected_career)
#         profile_vector = get_jina_embedding(user_profile)
#         results = qd_client.query_points(
#             collection_name=collection_name,
#             prefetch=[
#                 models.Prefetch(
#                     query=career_vector,
#                     using='career_vector',
#                     limit=20
#                 ),
#                 models.Prefetch(
#                     query=profile_vector,
#                     using="description_vector",
#                     limit=20,
#                 )
#             ],
#             query=models.FusionQuery(fusion=models.Fusion.RRF),
#             limit=1,
#             with_payload=True
#         )
#         return {
#             "statusCode": 200,
#             "body": json.dumps({"data": results.model_dump()}),
#             "headers": {"Content-Type": "application/json"}
#         }
#     except Exception as e:
#         return {
#             "statusCode": 500,
#             "body": json.dumps({"error": str(e)}),
#             "headers": {"Content-Type": "application/json"}
#         }
