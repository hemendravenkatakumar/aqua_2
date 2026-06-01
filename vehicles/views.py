import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from config.db import db
from bson import ObjectId

class VehicleListView(APIView):
    def get(self, request):
        vehicles = list(db.vehicles.find({'user_id': ObjectId(request.user.id)}).sort('created', -1))
        
        for v in vehicles:
            v['id'] = str(v['_id'])
            del v['_id']
            v['user_id'] = str(v['user_id'])
            if 'created' in v:
                v['created'] = v['created'].isoformat()
                
        return Response(vehicles, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        name = data.get('name')
        fish = data.get('fish', 'rohu')
        
        if not name:
            return Response({'error': 'name is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        vehicle_data = {
            'user_id': ObjectId(request.user.id),
            'name': name,
            'fish': fish,
            'bags': 0,
            'kg': 0.0,
            'status': 'active',
            'created': datetime.datetime.utcnow()
        }
        
        res = db.vehicles.insert_one(vehicle_data)
        
        vehicle_data['id'] = str(res.inserted_id)
        del vehicle_data['_id']
        vehicle_data['user_id'] = str(vehicle_data['user_id'])
        vehicle_data['created'] = vehicle_data['created'].isoformat()
        
        return Response(vehicle_data, status=status.HTTP_201_CREATED)

class VehicleDetailView(APIView):
    def put(self, request, pk):
        try:
            vehicle_id = ObjectId(pk)
        except Exception:
            return Response({'error': 'Invalid ID format'}, status=status.HTTP_400_BAD_REQUEST)
            
        vehicle = db.vehicles.find_one({'_id': vehicle_id, 'user_id': ObjectId(request.user.id)})
        if not vehicle:
            return Response({'error': 'Vehicle not found'}, status=status.HTTP_404_NOT_FOUND)
            
        data = request.data
        update_fields = {}
        if 'name' in data:
            update_fields['name'] = data['name']
        if 'fish' in data:
            update_fields['fish'] = data['fish']
        if 'status' in data:
            update_fields['status'] = data['status']
        if 'bags' in data:
            update_fields['bags'] = int(data['bags'])
        if 'kg' in data:
            update_fields['kg'] = float(data['kg'])
            
        if update_fields:
            db.vehicles.update_one({'_id': vehicle_id}, {'$set': update_fields})
            
        updated_vehicle = db.vehicles.find_one({'_id': vehicle_id})
        updated_vehicle['id'] = str(updated_vehicle['_id'])
        del updated_vehicle['_id']
        updated_vehicle['user_id'] = str(updated_vehicle['user_id'])
        if 'created' in updated_vehicle:
            updated_vehicle['created'] = updated_vehicle['created'].isoformat()
            
        return Response(updated_vehicle, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            vehicle_id = ObjectId(pk)
        except Exception:
            return Response({'error': 'Invalid ID format'}, status=status.HTTP_400_BAD_REQUEST)
            
        vehicle = db.vehicles.find_one({'_id': vehicle_id, 'user_id': ObjectId(request.user.id)})
        if not vehicle:
            return Response({'error': 'Vehicle not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Delete vehicle and clear references from bags
        db.vehicles.delete_one({'_id': vehicle_id})
        db.bags.update_many({'veh_id': vehicle_id}, {'$set': {'veh_id': None}})
        
        return Response({'message': 'Vehicle deleted successfully'}, status=status.HTTP_200_OK)
