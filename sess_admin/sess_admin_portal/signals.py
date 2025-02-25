from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Employee

@receiver(post_save, sender=Employee)
def create_user_for_employee(sender, instance, created, **kwargs):
    """
    Automatically creates a User when an Employee is created.
    Ensures username is unique.
    """
    if created and not instance.user:
        username = instance.email  # Using email as username

        # Check if a User with this username already exists
        if not User.objects.filter(username=username).exists():
            user = User.objects.create(
                username=username,
                email=instance.email,
                first_name=instance.first_name,
                last_name=instance.last_name,
            )
            user.set_password("defaultpassword123")  # Set temporary password
            user.save()

            # Link the Employee to the new User
            instance.user = user
            instance.save()
        else:
            print(f"User with username '{username}' already exists. Skipping creation.")

