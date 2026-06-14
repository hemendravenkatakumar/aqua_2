import datetime
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from config.db import db
from bson import ObjectId

class BagListView(APIView):
    def get(self, request):
        # Retrieve only active bags for this user
        bags = list(db.bags.find({
            'user_id': ObjectId(request.user.id),
            'active': {'$ne': False}
        }).sort('created', -1))
        
        # Convert BSON to JSON serializable
        for b in bags:
            b['id'] = str(b['_id'])
            del b['_id']
            b['user_id'] = str(b['user_id'])
            if b.get('veh_id'):
                b['veh_id'] = str(b['veh_id'])
            if 'created' in b:
                b['created'] = b['created'].isoformat()
                
        return Response(bags, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        fish = data.get('fish', 'rohu')
        weight = float(data.get('weight', 0.0))
        price = float(data.get('price', 0.0))
        veh_id = data.get('veh_id')
        
        bag_data = {
            'user_id': ObjectId(request.user.id),
            'fish': fish,
            'weight': weight,
            'price': price,
            'veh_id': ObjectId(veh_id) if veh_id else None,
            'active': True,
            'created': datetime.datetime.utcnow()
        }
        
        res = db.bags.insert_one(bag_data)
        
        # If this is linked to a vehicle, update the vehicle stats
        if veh_id:
            vehicle = db.vehicles.find_one({'_id': ObjectId(veh_id)})
            if vehicle:
                new_bags = vehicle.get('bags', 0) + 1
                new_kg = vehicle.get('kg', 0.0) + weight
                db.vehicles.update_one(
                    {'_id': ObjectId(veh_id)},
                    {'$set': {'bags': new_bags, 'kg': new_kg}}
                )

        bag_data['id'] = str(res.inserted_id)
        del bag_data['_id']
        bag_data['user_id'] = str(bag_data['user_id'])
        if bag_data['veh_id']:
            bag_data['veh_id'] = str(bag_data['veh_id'])
        bag_data['created'] = bag_data['created'].isoformat()
        
        return Response(bag_data, status=status.HTTP_201_CREATED)

class BagDetailView(APIView):
    def delete(self, request, pk):
        try:
            bag_id = ObjectId(pk)
        except Exception:
            return Response({'error': 'Invalid ID format'}, status=status.HTTP_400_BAD_REQUEST)
            
        bag = db.bags.find_one({'_id': bag_id, 'user_id': ObjectId(request.user.id)})
        if not bag:
            return Response({'error': 'Bag not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # If this bag was linked to a vehicle, update the vehicle stats
        veh_id = bag.get('veh_id')
        if veh_id:
            vehicle = db.vehicles.find_one({'_id': ObjectId(veh_id)})
            if vehicle:
                new_bags = max(0, vehicle.get('bags', 0) - 1)
                new_kg = max(0.0, vehicle.get('kg', 0.0) - bag.get('weight', 0.0))
                db.vehicles.update_one(
                    {'_id': ObjectId(veh_id)},
                    {'$set': {'bags': new_bags, 'kg': new_kg}}
                )

        db.bags.delete_one({'_id': bag_id})
        return Response({'message': 'Bag deleted successfully'}, status=status.HTTP_200_OK)

class BagStatsView(APIView):
    def get(self, request):
        user_id = ObjectId(request.user.id)
        bags = list(db.bags.find({
            'user_id': user_id,
            'active': {'$ne': False}
        }))
        
        total_bags = len(bags)
        total_weight = sum(b.get('weight', 0.0) for b in bags)
        avg_weight = total_weight / total_bags if total_bags > 0 else 0.0
        total_amount = sum(b.get('weight', 0.0) * b.get('price', 0.0) for b in bags)
        
        return Response({
            'total_bags': total_bags,
            'total_weight': round(total_weight, 2),
            'avg_weight': round(avg_weight, 2),
            'total_amount': round(total_amount, 2)
        }, status=status.HTTP_200_OK)
