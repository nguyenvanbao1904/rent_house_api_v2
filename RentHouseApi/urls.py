from django.contrib import admin
from django.urls import path, include, re_path

# Swagger config
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from app.views import CustomTokenView

schema_view = get_schema_view(
    openapi.Info(
        title="Find_Room API",
        default_version='v1',
        description="APIs for Find_Room_App",
        contact=openapi.Contact(email="2251012012bao@ou.edu.vn"),
        license=openapi.License(name="Nguyễn Văn Bảo"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    path('', include('app.urls')),
    path('admin/', admin.site.urls),
    path('account/', include('social_django.urls', namespace='social')),

    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    re_path(r'^swagger/$',
            schema_view.with_ui('swagger', cache_timeout=0),
            name='schema-swagger-ui'),
    re_path(r'^redoc/$',
            schema_view.with_ui('redoc', cache_timeout=0),
            name='schema-redoc'),
    path('o/token/', CustomTokenView.as_view(), name='token'),
    path('o/', include('oauth2_provider.urls',
                       namespace='oauth2_provider')),

]
