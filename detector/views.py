from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from .models import Prediction
from .ml.model import predict
import time

class PredictView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request):
        image = request.FILES.get('image')
        if not image:
            return Response({'error': 'No image provided.'}, status=400)

        allowed = ('image/jpeg', 'image/png', 'image/webp')
        if image.content_type not in allowed:
            return Response({'error': 'Invalid file type.'}, status=400)

        start = time.time()
        results = predict(image)
        elapsed = round((time.time() - start) * 1000, 1)

        # Save to history
        Prediction.objects.create(
            user=request.user,
            image=image,
            top_prediction=results[0]['class'],
            confidence=results[0]['confidence']
        )

        return Response({
            'predictions': results,
            'inference_ms': elapsed
        })

class HistoryView(APIView):
    def get(self, request):
        preds = Prediction.objects.filter(user=request.user).order_by('-created_at')[:20]
        return Response([{
            'id': p.id,
            'top_prediction': p.top_prediction,
            'confidence': p.confidence,
            'image_url': request.build_absolute_uri(p.image.url),
            'created_at': p.created_at,
        } for p in preds])