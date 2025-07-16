import json
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler
import urllib.parse
from lib.qd_search import QdSearch

load_dotenv()


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
        # init qdsearch class
        qd_search = QdSearch()
        # get content length
        content_length = int(self.headers.get('Content-Length', 0))

        # read and parse POST data
        post_data = self.rfile.read(content_length)

        try:
            # Parse JSON data
            data = json.loads(post_data.decode('utf-8'))

            selected_career = data.get('selected_career')
            quiz_answers = data.get('answers')

            recommended_degrees = qd_search.qd_search(
                career=selected_career, answers=quiz_answers)

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
