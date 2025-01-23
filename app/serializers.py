from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from app.models import User, Image, RentalPost, FindRoomPost, Comment, Follow, Role


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
    comments = serializers.SerializerMethodField()
    user_id = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = RentalPost
        fields = ['id', 'city', 'district', 'ward', 'detail_address', 'price', 'area', 'title', 'content', 'images', 'max_occupants', 'comments', 'user_id']

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

    def get_comments(self, instance):
        content_type = ContentType.objects.get_for_model(RentalPost)
        comments = Comment.objects.filter(content_type=content_type, object_id=instance.id)
        return CommentSerializer(comments, many=True).data

class FindRoomPostSerializer(ModelSerializer):
    comments = serializers.SerializerMethodField()
    class Meta:
        model = FindRoomPost
        exclude = ['user_id']

    def create(self, validated_data):
        user = self.context["request"].user
        find_room_post = FindRoomPost.objects.create(user_id=user, **validated_data)
        return find_room_post

    def get_comments(self, instance):
        content_type = ContentType.objects.get_for_model(FindRoomPost)
        comments = Comment.objects.filter(content_type=content_type, object_id=instance.id)
        return CommentSerializer(comments, many=True).data

class CommentSerializer(ModelSerializer):
    content_type = serializers.CharField()
    user_id = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Comment
        fields = ['id', 'content', 'created_at', 'content_type', 'object_id', 'image', 'user_id', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context["request"].user
        try:
            content_type = ContentType.objects.get(app_label='app',model=validated_data['content_type'])
            validated_data['content_type'] = content_type

            instance = content_type.model_class()
            if instance.objects.filter(id=validated_data['object_id']).first() is None:
                raise ValidationError({"object_id": "Object id must be defined."})

            return Comment.objects.create(user_id=user, **validated_data)
        except ContentType.DoesNotExist:
            raise ValidationError({"content_type": "Content type not found."})

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data['image']:
            data['image'] = instance.image.url
        return data

class FollowSerializer(ModelSerializer):
    follower = serializers.PrimaryKeyRelatedField(read_only=True)
    followed = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'followed', 'created_at']

    def create(self, validated_data):
        validated_data['follower'] = self.context["request"].user
        if Follow.objects.filter(followed=validated_data['followed'], follower=validated_data['follower']).exists():
            raise ValidationError({"followed": "Follow already exists."})

        if validated_data['follower'].role != Role.NGUOI_THUE_TRO:
            raise ValidationError({"detail": "Only (Nguoi_Thue_Tro) can follow (Chu_Nha_Tro)."})

        if validated_data['followed'].role != Role.CHU_NHA_TRO:
            raise ValidationError({"detail": "You can only follow (Chu_Nha_Tro)."})
        return super().create(validated_data)