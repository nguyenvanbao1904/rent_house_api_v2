from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from cloudinary.models import CloudinaryField
from django.db.models.fields import CharField


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.avatar = "https://t4.ftcdn.net/jpg/05/49/98/39/360_F_549983970_bRCkYfk0P6PP5fKbMhZMIb07mCJ6esXL.jpg"
        user.save()
        return user

    def create_superuser(self, email, **extra_fields):
        extra_fields.setdefault('role', Role.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, **extra_fields)


class Role(models.TextChoices):
    ADMIN = 'Admin'
    CHU_NHA_TRO = 'Chu_Nha_Tro'
    NGUOI_THUE_TRO = 'Nguoi_Thue_Tro'

class User(AbstractUser):
    password = models.CharField(max_length=128, null=True)
    username = None
    email = models.EmailField(blank=False, unique=True, null=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    phone_number = CharField(max_length=11, null=True, blank=True)
    avatar_url = CloudinaryField('image', null=False, blank=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.NGUOI_THUE_TRO)
    following = models.ManyToManyField('self', through='Follow', related_name='followers', symmetrical=False )
    objects = UserManager()


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_set') #nguoi theo doi nguoi khac
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower_set') #nguoi duoc nguoi khac theo doi
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')

class Post(models.Model):
    class Meta:
        abstract = True
    content = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    price = models.FloatField(null=False, blank=False)
    is_active = models.BooleanField(default=True)

class Address(models.Model):
    class Meta:
        abstract = True
    city = models.CharField(max_length=100, null=False, blank=False)
    district = models.CharField(max_length=100, null=False, blank=False)
    detail_address = models.TextField(null=False, blank=False)

class RoomImage(models.Model):
    image_url = CloudinaryField('image', null=False, blank=False)
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='images')

class Room(Address):
    name = models.CharField(max_length=100, null=False, blank=False)
    area = models.FloatField(null=False, blank=False)
    num_of_bedrooms = models.IntegerField(null=True, blank=True)
    num_of_bathrooms = models.IntegerField(null=True, blank=True)

    def clean(self):
        if self.images.count() < 3:
            raise ValidationError('A room must have at least 3 images.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class FindRoomPost(Post, Address):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='find_room_post')

class RentalPost(Post, Address):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rental_post')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='rental_post')

class Comment(models.Model):
    content = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    image_url = CloudinaryField('image', null=False, blank=False)
    updated_at = models.DateTimeField(auto_now=True)
    find_room_post = models.ForeignKey(FindRoomPost, on_delete=models.CASCADE)
    rental_post = models.ForeignKey(RentalPost, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
