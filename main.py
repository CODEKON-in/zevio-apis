from flask import Flask,jsonify,request
from profile import *
from auth import *
from secrets import token_hex

zevio = Flask('myapp')

def response(status):
    return jsonify({
        'status':status,
        'csrf':token_hex(16)
    })

@zevio.route('/api/user/<string:uid>',methods=['GET'])
def get_user(uid:str):
    if request.method == 'GET':
        return response(get_user_info(uid))
    else: return response('method not allowed')

@zevio.route('/api/user/add/',methods=['POST'])
def _add_user():
    if request.method == 'POST':
        userdatas = request.form
        uid = userdatas.get('uid')
        name = userdatas.get('name')
        phone = userdatas.get('phone')
        user_type = userdatas.get('user_type')

        allowed_utypes = ['customer','shop','delivery_person']
        valid_phone_no = phone_number_validator(phone)

        if valid_phone_no != None and user_type in allowed_utypes:
            _add = add_user(uid,name,phone,user_type)
            if _add:
                return response(200)
            else: return response('failed to add user')
        else:
            return response('invalid phone number or user type')
    else: return response('Method not allowed')

zevio.run(host='',port=2222)