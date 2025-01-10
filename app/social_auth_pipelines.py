import cloudinary.uploader

def save_avatar(backend, user, response, *args, **kwargs):
    if backend.name == 'google-oauth2':
        if response.get('picture'):
            upload_result = cloudinary.uploader.upload(response.get('picture'))
            user.avatar = upload_result['secure_url']
            user.save()
