#  coding: utf-8 
import socketserver
import os

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
# https://docs.python.org/3/library/os.path.html
# https://docs.python.org/3/library/socketserver.html


class Response:
    """Represent an HTTP response to send to the client.
    
    Params:
        code - the HTTP status code to send
        content - the binary content to send
        headers - the HTTP headers to include
    """

    def __init__(self, code=200, content=b'', headers={}) -> None:
        self.code = code
        self.content = content
        self.headers = headers
        self.codes = {
            404: 'Not Found',
            200: 'OK',
            405: 'Method Not Allowed',
            301: 'Moved Permanently'
        }

    def build(self):
        """Return the binary response to send."""
        resp = f"HTTP/1.1 {self.code} {self.codes[self.code]}\n"
        for k, v in self.headers.items():
            resp += f"{k}: {v}\n"
        resp += '\n'
        return resp.encode() + self.content


class RequestHandler:

    def handle(self, request):
        if request.method.upper() != 'GET':
            return Response(405)
        path = self.get_path(request.path)
        if not os.path.isfile(path):
            if os.path.isdir(path):
                new_path = request.path + '/'
                return Response(301, b'', {'Location': new_path})
            else:
                return Response(404)
        elif not path.startswith('www'):
            return Response(404)
        with open(path, 'rb') as in_file:
            content = in_file.read()
        headers = self.get_headers(path, content)
        return Response(200, content, headers)

    def get_headers(self, path, content):
        headers = {}
        headers["content-length"] = len(content)
        if path.split(".")[-1] == 'html':
            headers["content-type"] = "text/html"
        elif path.split(".")[-1] == 'css':
            headers["content-type"] = "text/css"
        return headers
            
        
    def get_path(self, path):
        path = 'www' + path 
        if path.endswith('/'):
            path = os.path.join(path, 'index.html')
        return os.path.normpath(path)
        

class Request:
    """Represent an HTTP request.
    
    Params:
        data - the binary input request

    Attributes:
        method - the HTTP method
        path - the path specified
        standard - the HTTP standard used
        headers - the HTTP headers included
    """

    def __init__(self, data) -> None:
        self.parse(data)

    def parse(self, data):
        lines = data.decode().splitlines()
        self.method, self.path, self.standard = lines[0].split(' ')
        self.headers = {}
        i = 1
        while i < len(lines) and lines[i]:
            key, val = lines[i].split(': ')
            self.headers[key] = val
            i += 1


class MyWebServer(socketserver.BaseRequestHandler):
    
    def handle(self):
        self.data = self.request.recv(1024).strip()
        if self.data:
            req = Request(self.data)
            response = RequestHandler().handle(req)
            #print ("Got a request of: %s\n" % self.data)
            #self.request.sendall(bytearray("OK",'utf-8'))
            self.request.sendall(response.build())

    def parse_request(self, data):
        lines = data.splitlines()
        request, path, standard = lines[0].split(b' ')
        #print(request, path, standard)
        assert standard == b'HTTP/1.1', "Only HTTP/1.1 is supported"
        if request.upper() != b'GET':
            response = b'HTTP/1.1 405 Method Not Allowed'
        else:
            response = b'HTTP/1.1 200 OK\n\n'
            if path.endswith(b'/'):
                path += b'index.html'
            path = os.path.join("www", path.decode())
            print(path)
            try:
                send_file = open(path, 'rb')
            except FileNotFoundError:
                response = b'HTTP/1.1 404 Not Found'
            else:
                response += send_file.read()
        self.request.sendall(response)

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
