from django.urls import path, include
from rest_framework import routers

from app import views

router = routers.DefaultRouter()
router.register('users', views.UserViewSet)
router.register('account', views.AccountViewSet, basename='account')
urlpatterns = [
    path('', include(router.urls)),

]
