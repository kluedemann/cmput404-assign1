#  coding: utf-8 
import socketserver
from utils import Request, ErrorResponse, Response

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# Copyright 2023 Kai Luedemann
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

# Sources: 
# https://opensource.stackexchange.com/questions/9199/how-to-label-and-license-derivative-works-made-under-apache-license-version-2-0


class MyWebServer(socketserver.BaseRequestHandler):
    
    def handle(self):
        # Read data
        self.data = self.request.recv(1024).strip()
        if self.data:
            # Handle request and send response
            req = Request(self.data)
            response = self.get_response(req)
            self.request.sendall(response.build())

    def get_response(self, request):
        """Handle the incoming HTTP request and return a response.
        
        Params:
            request - the incoming Request object

        Returns: the outgoing Response object
        """

        # Check method
        if not request.valid:
            return ErrorResponse(400, "Error 400: Bad Request")
        elif request.method.upper() != 'GET':
            return ErrorResponse(405, "Error 405: Invalid Method")
        
        # Check path
        path = self.get_path(request.path)
        if self.exits_dir(path):
            return ErrorResponse(404, "Error 404: File not found")
        
        # Try opening file
        try:
            in_file = open(path, 'rb')
        except IsADirectoryError:
            new_path = request.path + '/'
            return Response(301, b'', {'Location': new_path})
        except FileNotFoundError:
            return ErrorResponse(404, "Error 404: File not found")
        
        content = in_file.read()
        headers = self.get_headers(path, content)

        return Response(200, content, headers)
        
    def exits_dir(self, path):
        """Return True if the path exits the www directory; False otherwise.
        
        Params:
            path - the path string starting with www

        Returns: bool - whether the path exits www/
        """
        depth = 0
        for part in path.split('/'):
            if part == '..':
                depth  -= 1
            elif part != '.':
                depth += 1
            if depth <= 0:
                return True
        return False

    def get_headers(self, path, content):
        """Return the HTTP headers to include with the response based
        on the file path and content.
        
        Params:
            path - the path string
            content - the binary content to send with the response

        Returns: dict - the HTTP headers as key-value pairs
        """
        headers = {}
        headers["Content-Length"] = len(content)
        headers["Connection"] = "close"
        if path.split(".")[-1] == 'html':
            headers["Content-Type"] = "text/html"
        elif path.split(".")[-1] == 'css':
            headers["Content-Type"] = "text/css"
        return headers
        
    def get_path(self, path):
        """Return the file path to search for given the GET address.
        
        Params:
            path - the path string

        Returns: the normalized path of the file requested
        """
        path = 'www' + path 
        if path.endswith('/'):
            path += 'index.html'
        return path


if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
