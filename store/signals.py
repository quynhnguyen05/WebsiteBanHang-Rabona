from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Cart, UserProfile


@receiver(post_save, sender=User)
def create_user_cart_and_profile(sender, instance, created, **kwargs):
    """Tự động tạo Cart và UserProfile khi tạo User mới."""
    if created:
        Cart.objects.get_or_create(user=instance)
        UserProfile.objects.get_or_create(user=instance)
