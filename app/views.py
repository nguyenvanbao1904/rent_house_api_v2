from cloudinary.uploader import upload
from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from oauthlib.common import generate_token
from oauth2_provider.models import Application
from django.db.models import Q, Prefetch

from app.models import User, RentalPost, FindRoomPost, Comment, Follow, RentalPostStatus, Role
from app.paginators import ItemPagination
from app.permissions import AdminPermission, ChuNhaTroPermission, NguoiThueTroPermission, IsOwner
from app.serializers import UserSerializer, RentalPostSerializer, FindRoomPostSerializer, \
    CommentSerializer, FollowSerializer
from django.http import JsonResponse

from app.ultis import send_mails


class UserViewSet(viewsets.ViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['get'], url_path='current_user', permission_classes=[permissions.IsAuthenticated])
    def current_user(self, request):
        user = self.request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='count_user', permission_classes=[AdminPermission])
    def count_user(self, request):
        month = request.GET.get('month')
        quarter = request.GET.get('quarter')
        year = request.GET.get('year')
        nguoi_thue_tro_query = User.objects.filter(role=Role.NGUOI_THUE_TRO)
        chu_nha_tro_query = User.objects.filter(role=Role.CHU_NHA_TRO)

        if month:
            nguoi_thue_tro_query = nguoi_thue_tro_query.filter(last_login__month=month)
            chu_nha_tro_query = chu_nha_tro_query.filter(last_login__month=month)

        if quarter:
            quarter = int(quarter)
            if quarter == 1:
                month_range = [1, 2, 3]
            elif quarter == 2:
                month_range = [4, 5, 6]
            elif quarter == 3:
                month_range = [7, 8, 9]
            elif quarter == 4:
                month_range = [10, 11, 12]
            else:
                return Response({"error": "Invalid quarter"}, status=400)

            nguoi_thue_tro_query = nguoi_thue_tro_query.filter(last_login__month__in=month_range)
            chu_nha_tro_query = chu_nha_tro_query.filter(last_login__month__in=month_range)

        if year:
            nguoi_thue_tro_query = nguoi_thue_tro_query.filter(last_login__year=year)
            chu_nha_tro_query = chu_nha_tro_query.filter(last_login__year=year)

        nguoi_thue_tro_count = nguoi_thue_tro_query.count()
        chu_nha_tro_count = chu_nha_tro_query.count()

        return Response({
            'nguoi_thue_tro': nguoi_thue_tro_count,
            'chu_nha_tro': chu_nha_tro_count,
            'total_user': nguoi_thue_tro_count + chu_nha_tro_count
        })

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

            user = User(
                email=request.data.get('email'),
                first_name=request.data.get('first_name'),
                last_name=request.data.get('last_name'),
                avatar_url=avatar_url,
            )

            if request.data.get('role'):
                if request.data.get('role') in Role.values:
                    if request.data.get('role') != Role.ADMIN:
                        user.role = request.data.get('role')
                    else:
                        if request.user and request.user.is_authenticated and request.user.role == Role.ADMIN:
                            user.role = request.data.get('role')
                        else:
                            return Response({'error': 'only admin can create admin account'}, status=401)
                else:
                    return Response({'error': 'Invalid role'}, status=400)

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

class RentalViewSet(viewsets.ViewSet, viewsets.ModelViewSet):
    queryset = RentalPost.objects.filter(is_active = True).prefetch_related('images').select_related('user_id')
    serializer_class = RentalPostSerializer
    pagination_class = ItemPagination

    def get_queryset(self):
        query = self.queryset
        city = self.request.GET.get('city')
        district = self.request.GET.get('district')
        ward = self.request.GET.get('ward')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        occupants = self.request.GET.get('occupants')
        address = self.request.GET.get('address')
        status = self.request.GET.get('status')
        area = self.request.GET.get('area')

        if self.request.user.is_authenticated and self.request.user.role == Role.CHU_NHA_TRO:
            query = query.filter(user_id = self.request.user.id)
        if status:
            if self.request.user.is_authenticated and (self.request.user.role == Role.CHU_NHA_TRO or self.request.user.role == Role.ADMIN) :
                query = query.filter(status = status)
            else:
                query = query.filter(status=RentalPostStatus.ALLOW)
        if status is None and self.action != 'retrieve':
            query = query.filter(status = RentalPostStatus.ALLOW)
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
        if area:
            try:
                query = query.filter(area__gte=int(area) - 5, area__lte=int(area) + 5)
            except ValueError:
                raise ValidationError({"area": "Invalid area, must be a number."})
        # **Prefetch comments với GFK**
        rental_post_type = ContentType.objects.get_for_model(RentalPost)
        comments_query = Comment.objects.filter(content_type=rental_post_type).select_related('user_id')

        query = query.prefetch_related(
            Prefetch('comments_gfk', queryset=comments_query, to_attr='prefetched_comments')
        )
        return query.order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_permissions(self):
        action_permissions = {
            'create': [ChuNhaTroPermission],
            'update': [ChuNhaTroPermission],
            'partial_update': [ChuNhaTroPermission],
            'destroy': [ChuNhaTroPermission],
            'saved_post': [NguoiThueTroPermission],
            'delete_saved_post': [NguoiThueTroPermission],
            'saved_posts': [NguoiThueTroPermission],
            'change_post_status': [AdminPermission],
        }

        permission_classes = action_permissions.get(self.action, [permissions.IsAuthenticated])
        return [permission() for permission in permission_classes]

    @action(methods=['post'], detail=False, url_path='save_post')
    def saved_post(self, request):
        try:
            post_id = request.data.get('post_id')
            rental_post = RentalPost.objects.get(id=post_id)
            request.user.saved_posts.add(rental_post)
            return Response({"message": "Rental post saved successfully!"}, status=status.HTTP_200_OK)
        except RentalPost.DoesNotExist:
            return Response({"error": "Rental post not found!"}, status=status.HTTP_404_NOT_FOUND)

    @action(methods=['delete'], detail=True, url_path='delete_saved_post')
    def delete_saved_post(self, request, pk=None):
        try:
            rental_post = RentalPost.objects.get(id=pk)
            request.user.saved_posts.remove(rental_post)
            return Response({"message": "Rental post removed successfully!"}, status=status.HTTP_200_OK)
        except RentalPost.DoesNotExist:
            return Response({"error": "Rental post not found!"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='saved_posts')
    def saved_posts(self, request):
        saved_posts = request.user.saved_posts.all()
        serializer = RentalPostSerializer(saved_posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch'], url_path='change_post_status')
    def change_post_status(self, request):
        try:
            post_id = request.data.get('post_id')
            rental_post = RentalPost.objects.get(id=post_id)
            rental_post_status = request.data.get('status')
            if rental_post_status not in RentalPostStatus.values:
                raise ValueError("Invalid status. Must be one of: Pending, Allow, Deny.")
            rental_post.status = rental_post_status
            rental_post.save()
            if rental_post.status == RentalPostStatus.ALLOW:
                follower = rental_post.user_id.follower_set.all()
                follower_users = [follow.follower for follow in follower]

                subject = f"{rental_post.user_id.first_name} {rental_post.user_id.last_name} vừa có 1 bài đăng mới."
                message = f"Người dùng {rental_post.user_id.first_name} {rental_post.user_id.last_name} mà bạn theo dõi vừa đăng bài mới trên hệ thống RentHouse."
                recipient_list = follower_users

                send_mails(subject, message, recipient_list)
            return Response({"message": "Rental post approved successfully!"}, status=status.HTTP_200_OK)
        except RentalPost.DoesNotExist:
            return Response({"error": "Rental post not found!"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FindRoomPostViewSet(viewsets.ViewSet, viewsets.ModelViewSet):
    queryset = FindRoomPost.objects.filter(is_active = True).all().order_by('-created_at').select_related('user_id')
    serializer_class = FindRoomPostSerializer
    pagination_class = ItemPagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_permissions(self):
        action_permissions = {
            'create': [NguoiThueTroPermission],
            'update': [NguoiThueTroPermission],
            'partial_update': [NguoiThueTroPermission],
            'destroy': [NguoiThueTroPermission],
            'my_find_room_posts': [NguoiThueTroPermission]
        }

        permission_classes = action_permissions.get(self.action, [permissions.IsAuthenticated])
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        query = self.queryset
        find_room_post = ContentType.objects.get_for_model(FindRoomPost)
        comments_query = Comment.objects.filter(content_type=find_room_post).select_related('user_id')
        query = query.prefetch_related(
            Prefetch('comments_gfk', queryset=comments_query, to_attr='prefetched_comments')
        )
        return query

    @action(detail=False, methods=['get'], url_path='my_find_room_posts')
    def my_find_room_posts(self, request):
        query = self.get_queryset().filter(user_id = request.user)
        return Response(FindRoomPostSerializer(query, many=True).data, status=status.HTTP_200_OK)
class CommentViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.DestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ItemPagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsOwner()]
        return super().get_permissions()

class FollowViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [NguoiThueTroPermission]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        follow = serializer.save()

        followed_user = follow.followed
        follower_user = follow.follower

        subject = "Bạn có một người theo dõi mới!"
        message = f"Người dùng {follower_user.email} đã bắt đầu theo dõi bạn trên hệ thống RentHouse."
        recipient_list = [followed_user.email]

        send_mails(subject, message, recipient_list)

    @action(detail=False, methods=['post'], url_path='unfollow', permission_classes=[NguoiThueTroPermission])
    def unfollow(self, request):
        followed = request.data.get('followed')
        if followed is None:
            return JsonResponse({'error': 'followed is required'}, status=400)
        try:
            followed_user = User.objects.get(id=followed)
            follow_instance = Follow.objects.get(follower = request.user, followed = followed_user)
            follow_instance.delete()
            return JsonResponse({'message': 'User unfollowed'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Follow.DoesNotExist:
            return Response({"detail": "You are not following this user."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], url_path='following')
    def following(self, request):
        following_users = request.user.following.all()
        serializer = UserSerializer(following_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'], url_path='count_follower', permission_classes=[ChuNhaTroPermission])
    def count_follower(self, request):
        my_followers = request.user.follower_set.count()
        return Response({'total_follower': my_followers}, status=status.HTTP_200_OK)


import json
from oauth2_provider.views import TokenView
from django.contrib.auth.models import update_last_login
from oauth2_provider.models import AccessToken

class CustomTokenView(TokenView):
    def post(self, request, *args, **kwargs):
        # Gọi phương thức `post` gốc của TokenView
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Parse nội dung JSON từ `response.content`
            token_data = json.loads(response.content)
            access_token = token_data.get('access_token')

            if access_token:
                try:
                    # Lấy AccessToken và cập nhật `last_login`
                    token = AccessToken.objects.get(token=access_token)
                    user = token.user
                    if user:
                        update_last_login(None, user)
                except AccessToken.DoesNotExist:
                    pass
        return response
