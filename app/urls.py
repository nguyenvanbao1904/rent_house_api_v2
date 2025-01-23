from django.urls import path, include
from rest_framework import routers

from app import views

router = routers.DefaultRouter()
router.register('users', views.UserViewSet)
router.register('account', views.AccountViewSet, basename='account')
router.register('image', views.ImageViewSet, basename='image')
router.register('rental_post', views.RentalViewSet, basename='rental_post')
router.register('find_room_post', views.FindRoomPostViewSet, basename='find_room_post')
router.register('comment', views.CommentViewSet, basename='comment')
router.register('follow', views.FollowViewSet, basename='follow')
urlpatterns = [
    path('', include(router.urls)),
]
