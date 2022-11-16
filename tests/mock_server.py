from threading import Thread
from uuid import uuid4

from flask import (
    Flask,
    jsonify,
)
from werkzeug.serving import make_server


HOST = '127.0.0.1'


class MockServer(Thread):

    def __init__(self, port=5000):
        super().__init__()
        self.port = port
        self.app = Flask(__name__)
        self.server = make_server(HOST, self.port, self.app)
        self.url = f'http://{HOST}:{self.port}'

    def shutdown_server(self):
        self.server.shutdown()
        self.join()

    def add_callback_response(self, url, callback, methods=('GET',)):
        callback.__name__ = str(uuid4())  # change name of method to mitigate flask exception
        self.app.add_url_rule(url, view_func=callback, methods=methods)

    def add_json_response(self, url, serializable, methods=('GET',)):
        def callback():
            return jsonify(serializable)

        self.add_callback_response(url, callback, methods=methods)

    def run(self):
        self.server.serve_forever()
