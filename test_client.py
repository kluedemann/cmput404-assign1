from urllib import request

BASEURL = "http://127.0.0.1:8080"

url = BASEURL + "/doesnotexist"

req = request.urlopen(url, None, 3)
print(req, type(req))
print(req.data)
