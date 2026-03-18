from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import Profile

User = get_user_model()

GROUP_ADMIN = "Admin"
GROUP_USER = "User"


@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def assign_default_group(sender, instance, created, **kwargs):
    if not created:
        return
    group, _ = Group.objects.get_or_create(name=GROUP_USER)
    instance.groups.add(group)


@receiver(post_migrate)
def ensure_default_groups_and_permissions(sender, **kwargs):
    """
    Create default groups and assign permissions:
    - Admin: full permissions on shop models
    - User: view-only on shop models
    """
    # Ensure groups exist
    admin_group, _ = Group.objects.get_or_create(name=GROUP_ADMIN)
    user_group, _ = Group.objects.get_or_create(name=GROUP_USER)

    # Shop models to protect
    shop_app_label = "shop"
    model_names = ["book", "category"]

    admin_perms: list[Permission] = []
    user_perms: list[Permission] = []

    for model in model_names:
        try:
            ct = ContentType.objects.get(app_label=shop_app_label, model=model)
        except ContentType.DoesNotExist:
            continue

        perms = Permission.objects.filter(content_type=ct)
        admin_perms.extend(list(perms))
        user_perms.extend(list(perms.filter(codename__startswith="view_")))

    if admin_perms:
        admin_group.permissions.set(admin_perms)
    if user_perms:
        user_group.permissions.set(user_perms)

