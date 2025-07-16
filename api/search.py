import json
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler
from lib.qd_search import QdSearch

load_dotenv()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Mock Response for GET request
        response_data = {
            "message": "This route only support POST method.",
            "data": {
                "selected_career": "selected career from quiz",
                "answers": ["answers from quiz"]
            }
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

            recommended_degrees, user_profile = qd_search.qd_search(
                career=selected_career, answers=quiz_answers)

            response_data = {
                "message": "Submission received",
                "request": {
                    "selected_career": selected_career,
                    "user_profile": user_profile
                },
                "data": recommended_degrees
            }

            # Set response headers
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # Send response
            self.wfile.write(json.dumps(response_data).encode())

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
