import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from config.db import db
from bson import ObjectId

class BatchListView(APIView):
    def get(self, request):
        batches = list(db.batches.find({'user_id': ObjectId(request.user.id)}).sort('created', -1))
        
        for b in batches:
            b['id'] = str(b['_id'])
            del b['_id']
            b['user_id'] = str(b['user_id'])
            if 'created' in b:
                b['created'] = b['created'].isoformat()
                
        return Response(batches, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        name = data.get('name')
        fish = data.get('fish', 'rohu')
        bags = int(data.get('bags', 0))
        kg = float(data.get('kg', 0.0))
        amt = float(data.get('amt', 0.0))
        
        if not name:
            name = f"Batch - {datetime.date.today().strftime('%d %b %Y')}"
            
        batch_data = {
            'user_id': ObjectId(request.user.id),
            'name': name,
            'fish': fish,
            'bags': bags,
            'kg': kg,
            'amt': amt,
            'created': datetime.datetime.utcnow()
        }
        
        res = db.batches.insert_one(batch_data)
        
        # Proactively clear/reset the active bags after saving a batch if requested (or let client decide)
        # We can keep them or let client handle clearing them.
        
        batch_data['id'] = str(res.inserted_id)
        del batch_data['_id']
        batch_data['user_id'] = str(batch_data['user_id'])
        batch_data['created'] = batch_data['created'].isoformat()
        
        return Response(batch_data, status=status.HTTP_201_CREATED)

class WeeklySummaryView(APIView):
    def get(self, request):
        user_id = ObjectId(request.user.id)
        # Get past 7 days batches
        seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        batches = list(db.batches.find({
            'user_id': user_id,
            'created': {'$gte': seven_days_ago}
        }))
        
        total_kg = sum(b.get('kg', 0.0) for b in batches)
        total_amt = sum(b.get('amt', 0.0) for b in batches)
        total_bags = sum(b.get('bags', 0) for b in batches)
        
        # Calculate daily aggregates
        daily_stats = {}
        for b in batches:
            # Format date e.g. "Mon", "Tue"
            day = b['created'].strftime('%a')
            if day not in daily_stats:
                daily_stats[day] = {'kg': 0.0, 'amt': 0.0}
            daily_stats[day]['kg'] += b.get('kg', 0.0)
            daily_stats[day]['amt'] += b.get('amt', 0.0)
            
        # Format for charts
        chart_data = []
        for day, stats in daily_stats.items():
            chart_data.append({
                'day': day,
                'kg': round(stats['kg'], 2),
                'amt': round(stats['amt'], 2)
            })
            
        return Response({
            'total_kg': round(total_kg, 2),
            'total_amt': round(total_amt, 2),
            'total_bags': total_bags,
            'chart_data': chart_data
        }, status=status.HTTP_200_OK)
