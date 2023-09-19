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


class MyWebServer(socketserver.BaseRequestHandler):
    
    def handle(self):
        self.data = self.request.recv(1024).strip()
        self.parse_request(self.data)
        #print ("Got a request of: %s\n" % self.data)
        #self.request.sendall(bytearray("OK",'utf-8'))

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
