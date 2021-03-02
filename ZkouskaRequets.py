import requests
import json

URLDatabse = "http://192.168.1.102/skynet/www/api/product/add-product/"
Json = {"guide":"20.12.18.0","serial":"12351253","data":[{"key":"napeti","val":"9680"}]}
res = json.dumps(Json)
sumUrl = URLDatabse+res

print(sumUrl)
r = requests.get(sumUrl)

#odpoved
urlRet = json.loads(r.text)
status = (urlRet["status"])

print(status)
print(r.text)
print(r.url)