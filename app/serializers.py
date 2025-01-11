from rest_framework.serializers import ModelSerializer

from app.models import User, Image


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class ImageSerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        print(data)
        if data['image_url'] is not None:
            data['image_url'] = instance.image_url.url
        return data