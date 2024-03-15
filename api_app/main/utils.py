from users.models import CustomUser


def get_user(request):
    user = CustomUser.objects.get(id=request.user.id)
    return user