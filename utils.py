"""Module containing utility classes for implementing the server."""


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
