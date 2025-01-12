from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from app.models import User, Image, RentalPost


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {'password': {'write_only': True}}


class ImageSerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data['image_url']:
            data['image_url'] = instance.image_url.url
        return data

class RentalPostSerializer(ModelSerializer):
    images = PrimaryKeyRelatedField(many=True, queryset=Image.objects.all())
    class Meta:
        model = RentalPost
        fields = ['id', 'city', 'district', 'ward', 'detail_address', 'price', 'area', 'title', 'content', 'images']

    def create(self, validated_data):
        user = self.context["request"].user
        images = validated_data.pop('images', [])
        rental_post = RentalPost.objects.create(user_id=user, **validated_data)
        if len(images) < 3:
            raise ValidationError({"images": "Minimum 3 images required."})
        rental_post.images.set(images)
        print(rental_post)
        return rental_post

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Lấy danh sách hình ảnh
        if 'images' in data and data['images']:
            images = []
            for image_id in data['images']:
                try:
                    image = Image.objects.get(id=image_id)
                    images.append(image.image_url.url)
                except Image.DoesNotExist:
                    continue
            data['images'] = images
        return data