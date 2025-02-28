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
            time_in_dt = datetime.datetime.combine(self.date, self.time_in)
            time_out_dt = datetime.datetime.combine(self.date, self.time_out)
            
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
"""
#  Old PTo model
 class PTO(models.Model):
    date = models.DateField()
    start_date = models.TimeField()
    end_date = models.TimeField()
    reason = models.TextField(null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    status = models.CharField(max_length=100)
    
    def __str__(self):
        return f"PTO: {self.date} - {self.time_off}"
"""

    
# Add to your models.py

class Announcement(models.Model):
    """Model to store company announcements"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True, help_text="Leave blank if announcement doesn't expire")
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='announcements')
    important = models.BooleanField(default=False, help_text="Important announcements are highlighted")
    
    # Define choices for announcement types
    TYPE_GENERAL = 'general'
    TYPE_POLICY = 'policy'
    TYPE_EVENT = 'event'
    TYPE_HOLIDAY = 'holiday'
    
    TYPE_CHOICES = [
        (TYPE_GENERAL, 'General'),
        (TYPE_POLICY, 'Policy Update'),
        (TYPE_EVENT, 'Event'),
        (TYPE_HOLIDAY, 'Holiday'),
    ]
    
    announcement_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_GENERAL
    )
    
    # Optional image for the announcement
    image = models.ImageField(upload_to='announcements/', null=True, blank=True)
    
    class Meta:
        ordering = ['-date_posted']
    
    def __str__(self):
        return self.title
    
    @property
    def is_expired(self):
        """Check if announcement has expired"""
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False
    
    @property
    def days_ago(self):
        """Return how many days ago the announcement was posted"""
        delta = timezone.now().date() - self.date_posted.date()
        return delta.days
    
    
# Update to models.py for PTO management
class PTO(models.Model):
    STATUS_PENDING = 'Pending'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    
    TYPE_FULL_DAY = 'Full Day'
    TYPE_PARTIAL_DAY = 'Partial Day'
    TYPE_MULTIPLE_DAYS = 'Multiple Days'
    TYPE_CHOICES = [
        (TYPE_FULL_DAY, 'Full Day'),
        (TYPE_PARTIAL_DAY, 'Partial Day'),
        (TYPE_MULTIPLE_DAYS, 'Multiple Days'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='pto_requests')
    pto_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_FULL_DAY)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # For multiple days
    start_time = models.TimeField(null=True, blank=True)  # For partial days
    end_time = models.TimeField(null=True, blank=True)  # For partial days
    reason = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)  # For admin notes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_pto_requests'
    )
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = "PTO Request"
        verbose_name_plural = "PTO Requests"
    
    def __str__(self):
        return f"{self.employee} - {self.start_date} ({self.status})"
    
    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING
    
    @property
    def is_approved(self):
        return self.status == self.STATUS_APPROVED
    
    @property
    def is_rejected(self):
        return self.status == self.STATUS_REJECTED
    
    @property
    def days_requested(self):
        """Calculate the number of days requested"""
        if self.pto_type == self.TYPE_FULL_DAY:
            return 1
        elif self.pto_type == self.TYPE_PARTIAL_DAY:
            return 0.5
        elif self.pto_type == self.TYPE_MULTIPLE_DAYS and self.end_date:
            delta = self.end_date - self.start_date
            return delta.days + 1
        return 0
    
    @property
    def date_display(self):
        """Format the date(s) for display"""
        if self.pto_type == self.TYPE_MULTIPLE_DAYS and self.end_date:
            return f"{self.start_date.strftime('%b %d, %Y')} - {self.end_date.strftime('%b %d, %Y')}"
        else:
            return self.start_date.strftime("%b %d, %Y")
    
    @property
    def time_display(self):
        """Format the time for display"""
        if self.pto_type == self.TYPE_PARTIAL_DAY and self.start_time and self.end_time:
            return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"
        return "All Day"
    

# Model for Employee Requests
class EmployeeRequest(models.Model):
    STATUS_PENDING = 'Pending'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_RESOLVED = 'Resolved'
    STATUS_REJECTED = 'Rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_REJECTED, 'Rejected')
    ]
    
    TYPE_PERSONAL_INFO = 'Personal Info Change'
    TYPE_CLIENT_INFO = 'Client Info Update'
    TYPE_TECHNICAL_ISSUE = 'Technical Issue'
    TYPE_OTHER = 'Other'
    TYPE_CHOICES = [
        (TYPE_PERSONAL_INFO, 'Personal Info Change'),
        (TYPE_CLIENT_INFO, 'Client Info Update'),
        (TYPE_TECHNICAL_ISSUE, 'Technical Issue'),
        (TYPE_OTHER, 'Other')
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='requests')
    request_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='resolved_requests'
    )
    resolution_notes = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = "Employee Request"
        verbose_name_plural = "Employee Requests"
    
    def __str__(self):
        return f"{self.employee} - {self.subject} ({self.status})"
    
    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING
    
    @property
    def is_in_progress(self):
        return self.status == self.STATUS_IN_PROGRESS
    
    @property
    def is_resolved(self):
        return self.status == self.STATUS_RESOLVED
    
    @property
    def is_rejected(self):
        return self.status == self.STATUS_REJECTED
    
    @property
    def days_since_submission(self):
        """Calculate days since the request was submitted"""
        delta = timezone.now() - self.submitted_at
        return delta.days
    
    
# Model for Client Reports
class ClientReport(models.Model):
    TYPE_INCIDENT = 'Incident Report'
    TYPE_SLEEP_LOG = 'Sleep Log'
    TYPE_IPP = 'Individual Support Plan'
    TYPE_QUARTERLY = 'Quarterly Progress Report'
    TYPE_MEDICAL = 'Medical Visit Summary'
    TYPE_INITIAL_ASSESSMENT = 'Initial Assessment'
    TYPE_ANNUAL_SUPPORT = 'Annual Support Plan'
    
    TYPE_CHOICES = [
        (TYPE_INCIDENT, 'Client Incident Report'),
        (TYPE_SLEEP_LOG, 'Sleep Log Report'),
        (TYPE_IPP, 'Individual Support Plan (IPP)'),
        (TYPE_QUARTERLY, 'Quarterly Progress Report'),
        (TYPE_MEDICAL, 'Medical Visit/Hospital Summary'),
        (TYPE_INITIAL_ASSESSMENT, 'Initial Assessment Report'),
        (TYPE_ANNUAL_SUPPORT, 'Annual Support Plan Report')
    ]
    
    STATUS_DRAFT = 'Draft'
    STATUS_SUBMITTED = 'Submitted'
    STATUS_APPROVED = 'Approved'
    STATUS_NEEDS_REVISION = 'Needs Revision'
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_NEEDS_REVISION, 'Needs Revision')
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reports')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='submitted_reports')
    report_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    report_date = models.DateField()
    content = models.JSONField()  # Store form data as JSON
    notes = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_reports'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Client Report"
        verbose_name_plural = "Client Reports"
    
    def __str__(self):
        return f"{self.report_type} - {self.client} ({self.report_date})"
    
    @property
    def is_draft(self):
        return self.status == self.STATUS_DRAFT
    
    @property
    def is_submitted(self):
        return self.status == self.STATUS_SUBMITTED
    
    @property
    def is_approved(self):
        return self.status == self.STATUS_APPROVED
    
    @property
    def needs_revision(self):
        return self.status == self.STATUS_NEEDS_REVISION
    
    @property
    def is_editable(self):
        return self.status in [self.STATUS_DRAFT, self.STATUS_NEEDS_REVISION]
    
    def submit(self):
        """Submit the report for approval"""
        self.status = self.STATUS_SUBMITTED
        self.submitted_at = timezone.now()
        self.save()
    
    def approve(self, approved_by):
        """Approve the report"""
        self.status = self.STATUS_APPROVED
        self.approved_at = timezone.now()
        self.approved_by = approved_by
        self.save()
    
    def request_revision(self):
        """Request revision for the report"""
        self.status = self.STATUS_NEEDS_REVISION
        self.save()