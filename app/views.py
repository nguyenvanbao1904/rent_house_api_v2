from multiprocessing.connection import address_type

from cloudinary.uploader import upload
from django.utils import timezone
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from oauthlib.common import generate_token
from oauth2_provider.models import Application, AccessToken
from django.db.models import Q

from app.models import User, Image, RentalPost, FindRoomPost, Comment
from app.serializers import UserSerializer, ImageSerializer, RentalPostSerializer, FindRoomPostSerializer, \
    CommentSerializer
from django.http import JsonResponse


class UserViewSet(viewsets.ViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['get'], url_path='current_user', permission_classes=[permissions.IsAuthenticated])
    def current_user(self, request):
        user = self.request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)


class AccountViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'], url_path='login/callback', permission_classes=[permissions.IsAuthenticated])
    def callback(self, request):
        user = request.user

        try:
            existing_token = AccessToken.objects.get(user=user, application__name="rent house")
            existing_token.delete()
        except AccessToken.DoesNotExist:
            pass

        if not user.is_authenticated:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        # Tạo access_token cho người dùng
        app = Application.objects.get(name="rent house")
        expires = timezone.now() + timezone.timedelta(days=1)
        access_token = AccessToken.objects.create(
            user=user,
            application=app,
            token=generate_token(),
            expires=expires,
            scope="read write"
        )
        # Trả về access_token cho frontend
        return JsonResponse({'access_token': access_token.token,
                             'expires_in': (expires - timezone.now()).total_seconds(),
                             'token_type': 'Bearer',
                             'user': {
                                 'id': user.id,
                                 'username': user.username,
                                 'first_name': user.first_name,
                                 'last_name': user.last_name,
                                 'email': user.email}
                             }
                            )
    @action(detail=False, methods=['post'], url_path='register', permission_classes=[permissions.AllowAny])
    def register(self, request):
        try:
            if request.data.get('password') != request.data.get('confirm_password'):
                return JsonResponse({'error': 'Passwords not match'}, status=400)

            avatar = request.FILES.get('avatar')
            avatar_url = None
            if avatar:
                try:
                    upload_result = upload(avatar)
                    avatar_url = upload_result.get('secure_url')
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=400)

            user = User.objects.create(
                email=request.data.get('email'),
                first_name=request.data.get('first_name'),
                last_name=request.data.get('last_name'),
                avatar_url=avatar_url,
            )

            user.set_password(request.data.get('password'))
            user.save()
            return JsonResponse({'message': 'User created'}, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='logout', permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        try :
            token = request.auth
            if not token:
                return JsonResponse({'error': 'No token'}, status=status.HTTP_400_BAD_REQUEST)

            AccessToken.objects.get(token=token).delete()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({'error': e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ImageViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = Image.objects.filter(is_active=True).all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]

class RentalViewSet(viewsets.ViewSet, viewsets.ModelViewSet):
    queryset = RentalPost.objects.filter(is_active = True).all()
    serializer_class = RentalPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.queryset
        city = self.request.query_params.get('city', None)
        district = self.request.query_params.get('district', None)
        ward = self.request.query_params.get('ward', None)
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        occupants = self.request.query_params.get('occupants', None)
        address = self.request.query_params.get('address', None)
        if city:
            query = query.filter(city=city)
        if district:
            query = query.filter(district=district)
        if ward:
            query = query.filter(ward=ward)
        if min_price:
            query = query.filter(price__gte=min_price)
        if max_price:
            query = query.filter(price__lte=max_price)
        if occupants:
            query = query.filter(Q(max_occupants=occupants) | Q(max_occupants__isnull=True))
        if address:
            query = query.filter(detail_address__icontains=address)
        return query

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class FindRoomPostViewSet(viewsets.ViewSet, viewsets.ModelViewSet):
    queryset = FindRoomPost.objects.filter(is_active = True).all()
    serializer_class = FindRoomPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class CommentViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.DestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context