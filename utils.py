"""Module containing utility classes for implementing the server."""


import os


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
# Sources:
# https://docs.python.org/3/library/os.path.html
# https://docs.python.org/3/library/socketserver.html
# https://www.rfc-editor.org/rfc/rfc2616#section-14.10
# https://stackoverflow.com/questions/5258977/are-http-headers-case-sensitive


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
            301: 'Moved Permanently',
            400: 'Bad Request'
        }

    def build(self):
        """Return the binary response to send.
        
        Returns: bytes - the HTTP response to send
        """
        resp = f"HTTP/1.1 {self.code} {self.codes[self.code]}\r\n"
        for k, v in self.headers.items():
            resp += f"{k}: {v}\r\n"
        resp += '\r\n'
        return resp.encode() + self.content
    

class ErrorResponse(Response):
    """Represent an HTTP error response to send to the client.
    
    Params:
        code - the HTTP status code to send
        message - the error message to display
    """

    def __init__(self, code=404, message='') -> None:
        content = self.build_html(code, message)
        headers = self.get_headers(content)
        super().__init__(code, content, headers)

    def get_headers(self, content):
        """Create the headers to send.
        
        Params:
            content - the binary HTML content to send

        Returns: dict - the HTTP headers as key-value pairs
        """
        headers = {}
        headers["Content-Type"] = "text/html"
        headers["Content-Length"] = len(content)
        headers["Connection"] = "close"
        return headers
    
    def build_html(self, code, message):
        """Build the binary HTML content to send.
        Loads an HTML template from a file and adds the error message to display.
        
        Params:
            code - the HTTP status code
            message - the error message to display on the page
        
        Returns: bytes - the encoded HTML to send
        """
        with open("error_template.html", "r") as html_file:
            html = html_file.read()
        return html.format(message, message).encode()


class RequestHandler:

    def handle(self, request):
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
        if not os.path.isfile(path):
            if os.path.isdir(path):
                new_path = request.path + '/'
                return Response(301, b'', {'Location': new_path})
            else:
                return ErrorResponse(404, 'Error 404: File not found')
        elif not path.startswith('www'):
            return ErrorResponse(404, "Error 404: File not found")
        
        # Get content
        with open(path, 'rb') as in_file:
            content = in_file.read()
        headers = self.get_headers(path, content)

        return Response(200, content, headers)

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
        self.valid = True
        self.parse(data)

    def parse(self, data):
        """Parse the incoming HTTP request
        
        Params:
            data - the binary incoming HTTP request
        """
        lines = data.decode().splitlines()

        if lines and len(lines[0].split(' ')) == 3:
            self.method, self.path, self.standard = lines[0].split(' ')
        else:
            self.valid = False
        
        # Read HTTP headers
        self.headers = {}
        i = 1
        while i < len(lines) and lines[i]:
            key, val = lines[i].split(': ')
            self.headers[key] = val
            i += 1
