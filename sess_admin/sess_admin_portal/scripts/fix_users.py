from django.contrib.auth.models import User
from sess_admin_portal.models import Employee

for employee in Employee.objects.filter(user__isnull=True):
    username = employee.email
    if not User.objects.filter(username=username).exists():
        user = User.objects.create(
            username=username,
            email=employee.email,
            first_name=employee.first_name,
            last_name=employee.last_name,
        )
        user.set_password("pwd123456")
        user.save()

        # Link the Employee to the User
        employee.user = user
        employee.save()

        print(f"Created User for Employee {employee.first_name} {employee.last_name}")
    else:
        print(f"User with username '{username}' already exists. Skipping.")
