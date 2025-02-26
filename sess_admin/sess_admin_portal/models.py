from django.db import models
from smart_selects.db_fields import ChainedForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import User
import datetime
from django.utils import timezone


# Create your models here.
# employee model
# client model
# Client's family model
# daily report model
# external care team model
# programs model
# appointments model
# medications model
# medical history model
# timesheet model
# PTO model
# Regional Center Model
# Diagnosis Model

# RegionalCenter
# Client
# Programs
# Diagnosis
# Medications
# ClientFamily
# ExternalCareTeam
# Appointments
# Employee
# DailyReport
# MedicalHistory
# MedicationRegimen
# ClientProgram
# Timesheet
# PTO

class ProfilePicture(models.Model):
    """Model for storing profile pictures for employees and clients"""
    image = models.ImageField(upload_to='profile_pics/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Generic relation to work with both Employee and Client models
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    def __str__(self):
        return f"Profile picture for {self.content_object}"




class Address(models.Model):
    street = models.CharField(max_length=255)
    apt_or_unit = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=10)
    
    # Fields for generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        parts = [self.street]
        if self.apt_or_unit:
            parts.append(self.apt_or_unit)
        parts.append(self.city)
        parts.append(self.state)
        parts.append(self.zipcode)
        return ", ".join(parts)
    
class RegionalCenter(models.Model):
    regional_center = models.CharField(max_length=100)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return self.regional_center

class Client(models.Model):
    MALE = "Male"
    FEMALE = "Female"
    sex_choices = [
        (MALE, "M"),
        (FEMALE, "F"),
    ]
    
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100)
    sex = models.CharField(max_length=100, choices=sex_choices, default=MALE)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField()
    regional_center = models.ForeignKey(RegionalCenter, on_delete=models.CASCADE)
    onboarding_date = models.DateField()
    offboarding_date = models.DateField(null=True, blank=True)
    active = models.BooleanField()
    
    @property
    def profile_picture(self):
        """Get the client's profile picture if it exists"""
        from django.apps import apps
        ProfilePicture = apps.get_model('sess_admin_portal', 'ProfilePicture')
        
        content_type = ContentType.objects.get_for_model(self.__class__)
        return ProfilePicture.objects.filter(
            content_type=content_type,
            object_id=self.id
        ).first()
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

class Program(models.Model):
    program = models.CharField(max_length=100)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return self.program
    
    
class Category(models.Model):
    PHYSICAL = 'Physical'
    INTELLECTUAL = 'Intellectual'
    PHYSICAL_INTELLECTUAL = 'Physical/Intellectual'
    
    CATEGORY_CHOICES = [
        (PHYSICAL, 'Physical'),
        (INTELLECTUAL, 'Intellectual'),
        (PHYSICAL_INTELLECTUAL, 'Physical/Intellectual'),
    ]
    
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default=PHYSICAL)

    def __str__(self):
        return self.category
    
def get_default_category():
    return Category.objects.get(category=Category.PHYSICAL).id

class Diagnosis(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    diagnosis = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.diagnosis


    
class Medication(models.Model):
    medication = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.medication
    
    
class ClientFamily(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    relationship = models.CharField(max_length=100, null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class ExternalCareTeam(models.Model):
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class Appointment(models.Model):
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    appointment_location = models.CharField(max_length=100)
    appointment_reason = models.TextField()
    status = models.CharField(max_length=100)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Appointment: {self.appointment_date} - {self.client}"
    
class Employee(models.Model):
    MALE = "Male"
    FEMALE = "Female"
    sex_choices = [
        (MALE, "M"),
        (FEMALE, "F"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee', null=True, blank=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100)
    sex = models.CharField(max_length=100, choices=sex_choices, default=MALE)
    phone_number = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, null=True, blank=True)
    date_of_birth = models.DateField()
    hire_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)
    active = models.BooleanField()
    regionalCenter = models.ForeignKey(RegionalCenter, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    role = models.CharField(max_length=100)
    
    @property
    def profile_picture(self):
        """Get the employee's profile picture if it exists"""
        from django.apps import apps
        ProfilePicture = apps.get_model('sess_admin_portal', 'ProfilePicture')
        
        content_type = ContentType.objects.get_for_model(self.__class__)
        return ProfilePicture.objects.filter(
            content_type=content_type,
            object_id=self.id
        ).first()
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    @property
    def user_name(self):
        return f"{self.first_name} {self.last_name}"
    
class DailyReport(models.Model):
    date = models.DateField()
    time = models.TimeField()
    report = models.TextField()
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Daily Report: {self.date} - {self.client}"

class MedicalHistory(models.Model):
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    diagnosis = ChainedForeignKey(
        Diagnosis,
        chained_field="category",
        chained_model_field="category",
        show_all=False,
        auto_choose=True,
        sort=True,
        on_delete=models.CASCADE,
    )
    doctors_notes = models.TextField(null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Medical History: {self.date} - {self.diagnosis}"
    
class MedicationRegimen(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    def __str__(self):
        return f"Medication Regimen: {self.medication}"
    
class ClientProgram(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Client Program: {self.program}"

class TimesheetSubmission(models.Model):
    STATUS_PENDING = 'Pending'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.employee} - {self.start_date} to {self.end_date} ({self.status})"

   
class Timesheet(models.Model):
    date = models.DateField()
    time_in = models.TimeField()
    time_out = models.TimeField()
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    submission = models.ForeignKey(TimesheetSubmission, on_delete=models.CASCADE, null=True, blank=True, related_name='timesheets')
    status = models.CharField(max_length=20, choices=TimesheetSubmission.STATUS_CHOICES, default=TimesheetSubmission.STATUS_PENDING)
    
    @property
    def total_hours(self):
        """
        Returns the total hours worked, calculated as the difference between time_out and time_in in hours.
        """
        if self.time_in and self.time_out:
            # Convert string times to datetime objects for calculation
            time_in_dt = datetime.combine(self.date, self.time_in)
            time_out_dt = datetime.combine(self.date, self.time_out)
            
            # Calculate the difference
            delta = time_out_dt - time_in_dt
            
            # Check for negative time (if time_out is before time_in)
            if delta.total_seconds() < 0:
                return 0
                
            # Convert to hours and round to 1 decimal place
            hours = round(delta.total_seconds() / 3600.0, 1)
            return hours
        return 0

    def __str__(self):
        return f"Timesheet: {self.date} ({self.total_hours:.2f} hours) - {self.status}"
    
    @staticmethod
    def get_current_pay_period():
        """Determine current pay period dates"""
        today = datetime.date.today()
        if today.day <= 15:
            start_date = today.replace(day=1)
            end_date = today.replace(day=15)
        else:
            start_date = today.replace(day=16)
            next_month = start_date.replace(day=28) + datetime.timedelta(days=4)
            end_date = next_month - datetime.timedelta(days=next_month.day)
        return start_date, end_date
    
    @property
    def get_pay_period(self):
        """Determine pay period dates for a given date"""
        if self.date.day <= 15:
            start_date = self.date.replace(day=1)
            end_date = self.date.replace(day=15)
        else:
            start_date = self.date.replace(day=16)
            next_month = start_date.replace(day=28) + datetime.timedelta(days=4)
            end_date = next_month - datetime.timedelta(days=next_month.day)
        return start_date, end_date

    
class PTO(models.Model):
    date = models.DateField()
    start_date = models.TimeField()
    end_date = models.TimeField()
    reason = models.TextField(null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    status = models.CharField(max_length=100)
    
    def __str__(self):
        return f"PTO: {self.date} - {self.time_off}"
    
    