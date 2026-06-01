import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from config.db import db
from bson import ObjectId

def match_local_bot_reply(message):
    msg = message.lower()
    
    # 1. Greetings
    if any(x in msg for x in ["hello", "hi", "namaste", "hey", "greetings"]):
        return (
            "Namaste! I am your AquaSetu local AI helper. "
            "Ask me about current fish rates (Rohu/Catla), feed management, water quality (pH/DO), or pond disease treatments!"
        )
    
    # 2. Market Rates
    if any(x in msg for x in ["price", "rate", "cost", "market", "rupee", "money", "value", "sell", "buy"]):
        if "rohu" in msg:
            return "Current Rohu market rate is ₹125–₹145 per kg in local Andhra Pradesh/Bengal markets. Demand is steady."
        if "catla" in msg:
            return "Current Catla market rate is ₹135–₹155 per kg. Premium sizes (>2kg) fetch up to ₹165/kg."
        if "prawn" in msg or "shrimp" in msg:
            return "Vannamei Prawn rates: 100 count is ₹260/kg, 60 count is ₹340/kg, and large 30 count is ₹480/kg."
        if "tilapia" in msg:
            return "Tilapia rates are holding steady at ₹90–₹110 per kg depending on local sizes."
        return "Current Market Rates: Rohu (₹120-145/kg), Catla (₹135-165/kg), Tilapia (₹90-110/kg), and Vannamei Prawns (₹350-480/kg)."

    # 3. Feed Management
    if any(x in msg for x in ["feed", "food", "eat", "meal", "growel", "pellet"]):
        if "cloudy" in msg or "rain" in msg or "weather" in msg:
            return "⚠️ Weather Alert: Reduce feeding by 50% on cloudy/rainy days. Low sunlight decreases pond oxygen, and uneaten feed will rot."
        return "Feeding Rule: Feed Rohu/Catla at 2-3% of total body weight daily. Divide into 2 meals (morning and afternoon)."

    # 4. Water Quality
    if any(x in msg for x in ["water", "ph", "oxygen", "do", "salinity", "temp", "alkalinity"]):
        if "ph" in msg:
            return "Ideal pond pH is 7.5 to 8.5. If pH drops below 7.0, apply agricultural lime (50-100 kg per acre) to stabilize it."
        if "oxygen" in msg or "do" in msg:
            return "Dissolved Oxygen (DO) must be kept above 4.5 ppm. Run aerators during early morning (3 AM - 6 AM) when DO is lowest."
        return "Water Standards: Keep pH at 7.5-8.5, DO > 4.5 ppm, and Ammonia < 0.1 ppm. Run aerators daily and exchange 10% water if dirty."

    # 5. Diseases & Treatment
    if any(x in msg for x in ["disease", "spots", "fungus", "gill", "infection", "medicine", "dead", "rot"]):
        return (
            "Treatment Protocol: For fungal infections or red spots, apply Potassium Permanganate (2 kg/acre) or CIFAX sanitizer. "
            "Stop feeding for 1 day and run aerators continuously to help fish recover."
        )

    # 6. Default assistant response
    return (
        "I am AquaSetu AI. I can help with pond management! "
        "Try asking: 'What is the current Rohu rate?', 'How to manage pond pH?', or 'Feeding tips for cloudy weather'."
    )

class ChatView(APIView):
    def get(self, request):
        user_id = ObjectId(request.user.id)
        # Fetch last 30 messages
        history_cursor = db.chat_history.find({'user_id': user_id}).sort('created', 1).limit(30)
        formatted_messages = []
        for msg in history_cursor:
            formatted_messages.append({
                'id': str(msg['_id']),
                'role': 'user' if msg['role'] == 'user' else 'ai',
                'text': msg['text']
            })
        return Response(formatted_messages, status=status.HTTP_200_OK)

    def post(self, request):
        message = request.data.get('message', '')
        if not message:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = ObjectId(request.user.id)
        
        # Match using local rule-based database (No Google API key required!)
        reply = match_local_bot_reply(message)
        
        # Save both user message and local AI response to MongoDB
        db.chat_history.insert_many([
            {
                'user_id': user_id,
                'role': 'user',
                'text': message,
                'created': datetime.datetime.utcnow()
            },
            {
                'user_id': user_id,
                'role': 'model',
                'text': reply,
                'created': datetime.datetime.utcnow()
            }
        ])
        
        return Response({
            'reply': reply,
            'user': request.user.name or 'Farmer'
        }, status=status.HTTP_200_OK)

class ClearChatHistoryView(APIView):
    def delete(self, request):
        user_id = ObjectId(request.user.id)
        db.chat_history.delete_many({'user_id': user_id})
        return Response({'message': 'Conversation memory cleared successfully.'}, status=status.HTTP_200_OK)
