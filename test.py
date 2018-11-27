import json

import requests

TULING_URL = 'http://openapi.tuling123.com/openapi/api/v2'
API_KEY = 'd498ae5d6bcf4adbb5e9ccf23d161f1e'
USERID = 'cd6c54cc75c834cb'
perception = {'text': '你好'}
request_params = {'req_type': 0, 'userInfo': {'apiKey': API_KEY, 'userId': USERID}, 'perception': perception}

post = requests.post(url=TULING_URL, data=json.dumps(request_params))
print(post.text)
