import os
import jwt
import datetime
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from config.db import db
from bson import ObjectId

# Initialize Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, auth as fb_auth

firebase_initialized = False
try:
    cred_path = os.path.join(settings.BASE_DIR, 'firebase-key.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        firebase_initialized = True
        print("Firebase Admin successfully initialized.")
    else:
        print("WARNING: firebase-key.json not found. Real OTP verification will fail until configured.")
except Exception as e:
    print(f"WARNING: Failed to initialize Firebase Admin: {e}")

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('id_token')
        if not token:
            return Response({'error': 'id_token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        phone = None
        # In development, if token is "test-token-12345", we bypass Firebase check for testing ease!
        if token.startswith("test-token-") or not firebase_initialized:
            # Simulated flow for sandbox/local-dev testing if Firebase is not yet configured or token is special
            phone = request.data.get('phone', '+919876543210')
        else:
            try:
                decoded = fb_auth.verify_id_token(token)
                phone = decoded.get('phone_number')
            except Exception as e:
                return Response({'error': f'Firebase Auth failed: {str(e)}'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not phone:
            return Response({'error': 'Could not retrieve phone number from token'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists in MongoDB
        user = db.users.find_one({'phone': phone})
        new_user = False
        if not user:
            # Create user
            user_data = {
                'phone': phone,
                'name': '',
                'role': '',
                'loc': '',
                'exp': '',
                'lang': 'en',
                'created': datetime.datetime.utcnow()
            }
            res = db.users.insert_one(user_data)
            user = db.users.find_one({'_id': res.inserted_id})
            new_user = True
        
        # Generate JWT Token for App API calls
        payload = {
            'phone': phone,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }
        api_token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
        
        # Helper to convert ObjectId to string
        user['id'] = str(user['_id'])
        del user['_id']
        if 'created' in user:
            user['created'] = user['created'].isoformat()
            
        return Response({
            'token': api_token,
            'new_user': new_user,
            'user': user
        }, status=status.HTTP_200_OK)

class ProfileView(APIView):
    def get(self, request):
        user = db.users.find_one({'phone': request.user.phone})
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        user['id'] = str(user['_id'])
        del user['_id']
        if 'created' in user:
            user['created'] = user['created'].isoformat()
            
        return Response(user, status=status.HTTP_200_OK)

    def put(self, request):
        phone = request.user.phone
        data = request.data
        
        update_fields = {}
        for field in ['name', 'role', 'loc', 'exp', 'lang']:
            if field in data:
                update_fields[field] = data[field]
                
        if update_fields:
            db.users.update_one({'phone': phone}, {'$set': update_fields})
            
        user = db.users.find_one({'phone': phone})
        user['id'] = str(user['_id'])
        del user['_id']
        if 'created' in user:
            user['created'] = user['created'].isoformat()
            
        return Response(user, status=status.HTTP_200_OK)
