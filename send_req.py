from requests import post,get
from profile import generate_uuid

data = {
    'uid':generate_uuid(),
    'name':'mohamed123',
    'phone':'8877883788',
    'user_type':'shop'
}

req = post('http://127.0.0.1:2222/api/user/add/',data=data)
print(req.text)