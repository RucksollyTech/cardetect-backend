from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, UserSerializer
from django.contrib.auth.decorators import login_required
from decouple import config
from django.shortcuts import redirect
from django.contrib.auth import logout as django_logout

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

class LogoutView(APIView):
    def post(self, request):
        try:
            token = RefreshToken(request.data['refresh'])
            token.blacklist()
            return Response({'detail': 'Logged out.'})
        except Exception:
            return Response({'detail': 'Invalid token.'}, status=400)

def google_callback(request):
    user = request.user
    if not user.is_authenticated:
        frontend_url = config('FRONTEND_URL', default='http://localhost:3000')
        return redirect(f"{frontend_url}/login?error=google_failed")

    refresh = RefreshToken.for_user(user)

    django_logout(request)

    frontend_url = config('FRONTEND_URL', default='http://localhost:3000')
    return redirect(
        f"{frontend_url}/auth/google"
        f"?access={str(refresh.access_token)}"
        f"&refresh={str(refresh)}"
    )









