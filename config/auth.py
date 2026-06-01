import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from config.db import db
from bson import ObjectId

class MockUser:
    def __init__(self, data):
        self.id = str(data['_id'])
        self.phone = data['phone']
        self.name = data.get('name', '')
        self.role = data.get('role', '')
        self.loc = data.get('loc', '')
        self.exp = data.get('exp', '')
        self.lang = data.get('lang', 'en')
        self.is_authenticated = True

    def __str__(self):
        return self.phone

class MongoJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
            phone = payload.get('phone')
            if not phone:
                raise AuthenticationFailed('Invalid token payload')
            
            user = db.users.find_one({'phone': phone})
            if not user:
                raise AuthenticationFailed('User does not exist')
            
            return (MockUser(user), token)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
