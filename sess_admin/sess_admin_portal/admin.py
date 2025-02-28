# ========================
# Improved Admin Classes
# ========================
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.utils.html import format_html
from datetime import date
from .models import (
    Address, RegionalCenter, Client, Program, Category, Diagnosis, Medication, 
    ClientFamily, ExternalCareTeam, Appointment, Employee, DailyReport, 
    MedicalHistory, MedicationRegimen, ClientProgram, Timesheet, PTO, 
    TimesheetSubmission, ProfilePicture, Announcement, EmployeeRequest, ClientReport
)

# Custom Admin Site
class CustomAdminSite(admin.AdminSite):
    site_header = "SESS Admin Portal"
    site_title = "SESS Management System"
    index_title = "Welcome to Sierra Environmental and Social Services Administration"

admin_site = CustomAdminSite(name='sess_admin')

# Inlines
class AddressInline(GenericStackedInline):
    model = Address
    extra = 0
    
class ClientFamilyInline(admin.TabularInline):
    model = ClientFamily
    extra = 0
    
class MedicationRegimenInline(admin.TabularInline):
    model = MedicationRegimen
    extra = 0
    
class ClientProgramInline(admin.TabularInline):
    model = ClientProgram
    extra = 0
    
class DailyReportInline(admin.TabularInline):
    model = DailyReport
    extra = 0
    fields = ('date', 'time', 'report_preview')
    readonly_fields = ('report_preview',)
    
    def report_preview(self, obj):
        if obj.report:
            return obj.report[:50] + "..." if len(obj.report) > 50 else obj.report
        return ""
    report_preview.short_description = "Report Preview"

class TimesheetInline(admin.TabularInline):
    model = Timesheet
    extra = 0
    fields = ('date', 'time_in', 'time_out', 'get_hours')
    readonly_fields = ('get_hours',)
    
    def get_hours(self, obj):
        if obj.time_in and obj.time_out:
            return f"{obj.total_hours:.2f}"
        return "N/A"
    get_hours.short_description = "Hours"
    
class EmployeeRequestInline(admin.TabularInline):
    model = EmployeeRequest
    extra = 0
    fields = ('request_type', 'date_requested', 'subject', 'description', 'status')
    readonly_fields = ('request_type', 'date_requested', 'status')
    
class ClientReportInline(admin.TabularInline):
    model = ClientReport
    extra = 0
    fields = ('report_date', 'report_type', 'report_preview')
    readonly_fields = ('report_preview',)
    
    def report_preview(self, obj):
        if obj.report:
            return obj.report[:50] + "..." if len(obj.report) > 50 else obj.report
        return ""
    report_preview.short_description = "Report Preview"
    
    

# Improving Client Admin
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'sex', 'age', 'regional_center', 'onboarding_date', 'active')
    list_display_links = ('full_name',)
    list_filter = ('active', 'sex', 'regional_center', 'onboarding_date')
    search_fields = ('first_name', 'last_name', 'email', 'phone_number')
    date_hierarchy = 'onboarding_date'
    inlines = [AddressInline, ClientFamilyInline, MedicationRegimenInline, ClientProgramInline]
    
    fieldsets = (
        ('Personal Information', {
            'fields': (('first_name', 'middle_name', 'last_name'), 'sex', 'date_of_birth')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email')
        }),
        ('Program Details', {
            'fields': ('regional_center', 'onboarding_date', 'offboarding_date', 'active')
        }),
    )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = "Name"
    
    def age(self, obj):
        today = date.today()
        born = obj.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    age.short_description = "Age"
    
    
# Regional Center Admin
@admin.register(RegionalCenter)
class RegionalCenterAdmin(admin.ModelAdmin):
    list_display = ('regional_center', 'phone_number', 'email', 'client_count')
    search_fields = ('regional_center', 'phone_number', 'email')
    inlines = [AddressInline]
    
    def client_count(self, obj):
        return Client.objects.filter(regional_center=obj).count()
    client_count.short_description = "Number of Clients"

# Program Admin
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('program', 'phone_number', 'email', 'client_count')
    search_fields = ('program', 'phone_number', 'email')
    inlines = [AddressInline]
    
    def client_count(self, obj):
        return ClientProgram.objects.filter(program=obj).count()
    client_count.short_description = "Number of Clients"

# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category', 'diagnosis_count')
    
    def diagnosis_count(self, obj):
        return Diagnosis.objects.filter(category=obj).count()
    diagnosis_count.short_description = "Number of Diagnoses"

# Diagnosis Admin
@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('diagnosis', 'category', 'description_preview')
    list_filter = ('category',)
    search_fields = ('diagnosis', 'description')
    
    def description_preview(self, obj):
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return ""
    description_preview.short_description = "Description"
    
# Medication Admin
@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('medication', 'description_preview', 'client_count')
    search_fields = ('medication', 'description')
    
    def description_preview(self, obj):
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return ""
    description_preview.short_description = "Description"
    
    def client_count(self, obj):
        return MedicationRegimen.objects.filter(medication=obj).count()
    client_count.short_description = "Clients Using"

# ClientFamily Admin
@admin.register(ClientFamily)
class ClientFamilyAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'relationship', 'client_name', 'phone_number', 'email')
    list_filter = ('relationship',)
    search_fields = ('first_name', 'last_name', 'phone_number', 'email', 'client__first_name', 'client__last_name')
    raw_id_fields = ('client',)
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = "Name"
    
    def client_name(self, obj):
        return f"{obj.client.first_name} {obj.client.last_name}"
    client_name.short_description = "Client"

# ExternalCareTeam Admin
@admin.register(ExternalCareTeam)
class ExternalCareTeamAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'role', 'phone_number', 'email')
    list_filter = ('role',)
    search_fields = ('first_name', 'last_name', 'role', 'phone_number', 'email')
    inlines = [AddressInline]
    
    def full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return "N/A"
    full_name.short_description = "Name"
    
# Appointment Admin
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'appointment_date', 'appointment_time', 'appointment_location', 'status', 'days_away')
    list_filter = ('status', 'appointment_date')
    search_fields = ('client__first_name', 'client__last_name', 'appointment_location', 'appointment_reason')
    date_hierarchy = 'appointment_date'
    raw_id_fields = ('client',)
    
    fieldsets = (
        ('Client Information', {
            'fields': ('client',)
        }),
        ('Appointment Details', {
            'fields': ('appointment_date', 'appointment_time', 'appointment_location', 'appointment_reason', 'status')
        }),
    )
    
    def client_name(self, obj):
        return f"{obj.client.first_name} {obj.client.last_name}"
    client_name.short_description = "Client"
    
    def days_away(self, obj):
        today = date.today()
        delta = obj.appointment_date - today
        if delta.days == 0:
            return "Today"
        elif delta.days < 0:
            return f"{abs(delta.days)} days ago"
        return f"In {delta.days} days"
    days_away.short_description = "When"

# Employee Admin
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'role', 'client_name', 'hire_date', 'active')
    list_filter = ('active', 'role', 'hire_date', 'regionalCenter')
    search_fields = ('first_name', 'last_name', 'email', 'phone_number', 'role')
    date_hierarchy = 'hire_date'
    inlines = [AddressInline, TimesheetInline]
    raw_id_fields = ('client', 'regionalCenter')
    
    fieldsets = (
        ('Personal Information', {
            'fields': (('first_name', 'middle_name', 'last_name'), 'sex', 'date_of_birth')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email')
        }),
        ('Employment Details', {
            'fields': ('hire_date', 'termination_date', 'active', 'role', 'regionalCenter', 'client')
        }),
        ('User Account', {
            'fields': ('user',),
            'classes': ('collapse',)
        })
    )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = "Name"
    
    def client_name(self, obj):
        if obj.client:
            return f"{obj.client.first_name} {obj.client.last_name}"
        return "No Client"
    client_name.short_description = "Assigned Client"
    
# DailyReport Admin (already well-defined in original, just adding more features)
@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'employee_name', 'date', 'time', 'report_preview')
    list_filter = ('client', 'employee', 'date')
    search_fields = ('report', 'client__first_name', 'client__last_name', 
                    'employee__first_name', 'employee__last_name')
    date_hierarchy = 'date'
    raw_id_fields = ('client', 'employee')
    
    def report_preview(self, obj):
        """Return a preview of the report content"""
        return obj.report[:50] + "..." if len(obj.report) > 50 else obj.report
    report_preview.short_description = "Report Preview"
    
    def client_name(self, obj):
        return f"{obj.client.first_name} {obj.client.last_name}"
    client_name.short_description = "Client"
    
    def employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"
    employee_name.short_description = "Employee"

# MedicalHistory Admin
@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'diagnosis', 'category', 'date', 'notes_preview')
    list_filter = ('category', 'date', 'diagnosis')
    search_fields = ('client__first_name', 'client__last_name', 'diagnosis__diagnosis', 'doctors_notes')
    date_hierarchy = 'date'
    raw_id_fields = ('client', 'diagnosis')
    
    def client_name(self, obj):
        return f"{obj.client.first_name} {obj.client.last_name}"
    client_name.short_description = "Client"
    
    def notes_preview(self, obj):
        if obj.doctors_notes:
            return obj.doctors_notes[:50] + "..." if len(obj.doctors_notes) > 50 else obj.doctors_notes
        return ""
    notes_preview.short_description = "Doctor's Notes"
    
# MedicationRegimen Admin
@admin.register(MedicationRegimen)
class MedicationRegimenAdmin(admin.ModelAdmin):
    list_display = ('medication_name', 'client_name', 'dosage', 'frequency')
    list_filter = ('medication',)
    search_fields = ('client__first_name', 'client__last_name', 'medication__medication', 'dosage', 'frequency')
    raw_id_fields = ('client', 'medication')
    
    def medication_name(self, obj):
        return obj.medication.medication
    medication_name.short_description = "Medication"
    
    def client_name(self, obj):
        return f"{obj.client.first_name} {obj.client.last_name}"
    client_name.short_description = "Client"

# ClientProgram Admin
@admin.register(ClientProgram)
class ClientProgramAdmin(admin.ModelAdmin):
    list_display = ('program_name', 'client_name')
    list_filter = ('program',)
    search_fields = ('client__first_name', 'client__last_name', 'program__program')
    raw_id_fields = ('client', 'program')
    
    def program_name(self, obj):
        return obj.program.program
    program_name.short_description = "Program"
    
    def client_name(self, obj):
        return f"{obj.client.first_name} {obj.client.last_name}"
    client_name.short_description = "Client"

# Timesheet Admin (Enhancing existing)
@admin.register(Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    list_display = ("date", "employee_name", "time_in", "time_out", "hours", "submission_status")
    list_filter = ("employee", "date", "status")
    search_fields = ("employee__first_name", "employee__last_name", "date")
    date_hierarchy = "date"
    raw_id_fields = ('employee', 'submission')
    
    def employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"
    employee_name.short_description = "Employee"
    
    def hours(self, obj):
        return f"{obj.total_hours:.2f}" if hasattr(obj, 'total_hours') else "N/A"
    hours.short_description = "Hours"
    
    def submission_status(self, obj):
        if obj.submission:
            return obj.submission.status
        return "No Submission"
    submission_status.short_description = "Status"
    
# PTO Admin
@admin.register(PTO)
class PTOAdmin(admin.ModelAdmin):
    list_display = ('employee_name', 'start_date', 'end_date', 'start_time', 'end_time', 'pto_type', 'status', 'reason_preview')
    list_filter = ('status', 'start_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')
    date_hierarchy = 'start_date'
    raw_id_fields = ('employee',)
    
    def employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"
    employee_name.short_description = "Employee"
    
    def start_date(self, obj):
        return obj.start_date
    start_date.short_description = "Start Date"
    
    def end_date(self, obj):
        return obj.end_date
    end_date.short_description = "End Date"
    
    def start_time(self, obj):
        return obj.start_time
    start_time.short_description = "Start Time"
    
    def end_time(self, obj):
        return obj.end_time
    end_time.short_description = "End Time"
    
    def reason_preview(self, obj):
        if obj.reason:
            return obj.reason[:50] + "..." if len(obj.reason) > 50 else obj.reason
        return ""
    reason_preview.short_description = "Reason"
    
    def pto_type(self, obj):
        return obj.pto_type
    pto_type.short_description = "PTO Type"
  
    

# TimesheetSubmission Admin (enhancing existing)
@admin.register(TimesheetSubmission)
class TimesheetSubmissionAdmin(admin.ModelAdmin):
    list_display = ("employee_name", "period", "status", "submitted_at", "total_hours")
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("employee__first_name", "employee__last_name")
    date_hierarchy = "submitted_at"
    raw_id_fields = ('employee',)
    inlines = [TimesheetInline]
    actions = ['approve_submissions', 'reject_submissions']
    
    def employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"
    employee_name.short_description = "Employee"
    
    def period(self, obj):
        return f"{obj.start_date.strftime('%b %d')} - {obj.end_date.strftime('%b %d, %Y')}"
    period.short_description = "Pay Period"
    
    def total_hours(self, obj):
        hours = sum(t.total_hours for t in obj.timesheets.all() if hasattr(t, 'total_hours'))
        return f"{hours:.2f}"
    total_hours.short_description = "Total Hours"
    
    def approve_submissions(self, request, queryset):
        updated = queryset.update(status='Approved')
        for submission in queryset:
            submission.timesheets.all().update(status='Approved')
        self.message_user(request, f'{updated} timesheet submissions approved.')
    approve_submissions.short_description = "Approve selected submissions"
    
    def reject_submissions(self, request, queryset):
        updated = queryset.update(status='Rejected')
        for submission in queryset:
            submission.timesheets.all().update(status='Rejected')
        self.message_user(request, f'{updated} timesheet submissions rejected.')
    reject_submissions.short_description = "Reject selected submissions"
    
# ProfilePicture Admin
@admin.register(ProfilePicture)
class ProfilePictureAdmin(admin.ModelAdmin):
    list_display = ('preview_image', 'content_type', 'content_object_name', 'uploaded_at')
    list_filter = ('content_type', 'uploaded_at')
    readonly_fields = ('preview_large',)
    
    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 50%;" />', obj.image.url)
        return "No Image"
    preview_image.short_description = "Image"
    
    def preview_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" height="200" style="object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "No Image"
    preview_large.short_description = "Image Preview"
    
    def content_object_name(self, obj):
        if obj.content_object:
            if hasattr(obj.content_object, 'first_name') and hasattr(obj.content_object, 'last_name'):
                return f"{obj.content_object.first_name} {obj.content_object.last_name}"
            return str(obj.content_object)
        return "Unknown"
    content_object_name.short_description = "For"

from .forms import AnnouncementForm
# Announcement Admin
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'announcement_type', 'important', 'expiry_date', 'date_posted', 'posted_by')
    list_filter = ('announcement_type', 'important', 'expiry_date', 'date_posted', 'posted_by')
    search_fields = ('title', 'content')
    date_hierarchy = 'date_posted'
    form = AnnouncementForm
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" height="200" style="object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = "Image Preview"
    
@admin.register(EmployeeRequest)
class EmployeeRequestAdmin(admin.ModelAdmin):
    list_display = ('employee_name', 'request_type', 'subject', 'description', 'status')
    list_filter = ('request_type', 'status', 'submitted_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'subject', 'description')
    date_hierarchy = 'submitted_at'
    
    def employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"
    employee_name.short_description = "Employee"
    
    def request_type(self, obj):
        return obj.get_request_type_display()
    request_type.short_description = "Request Type"
    
    def submitted_at(self, obj):
        return obj.submitted_at
    submitted_at.short_description = "Submitted At"

    
    def status(self, obj):
        return obj.get_status_display()
    status.short_description = "Status"
    
    def subject(self, obj):
        return obj.subject
    subject.short_description = "Subject"
    
    def description(self, obj):
        return obj.description
    description.short_description = "Description"
    
@admin.register(ClientReport)
class ClientReportAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'report_date', 'report_type', 'report_preview', 'submitted_by')
    list_filter = ('report_type', 'report_date')
    search_fields = ('client__first_name', 'client__last_name', 'report')
    date_hierarchy = 'report_date'
    raw_id_fields = ('client',)
    
    def client_name(self, obj):
        return f"{obj.client.first_name} {obj.client.last_name}"
    client_name.short_description = "Client"
    
    def report_preview(self, obj):
        if obj.report:
            return obj.report[:50] + "..." if len(obj.report) > 50 else obj.report
        return ""
    report_preview.short_description = "Report Preview"
    
    def report_type(self, obj):
        return obj.get_report_type_display()
    report_type.short_description = "Report Type"
    
    def report_date(self, obj):
        return obj.report_date
    report_date.short_description = "Report Date"
    
    def report(self, obj):
        return obj.report
    report.short_description = "Report"
    
    def submitted_by(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"
    submitted_by.short_description = "Submitted By"
    
# ========================

# Register all models with the custom admin site
admin_site.register(Address)
admin_site.register(RegionalCenter, RegionalCenterAdmin)
admin_site.register(Client, ClientAdmin)
admin_site.register(Program, ProgramAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Diagnosis, DiagnosisAdmin)
admin_site.register(Medication, MedicationAdmin)
admin_site.register(ClientFamily, ClientFamilyAdmin)
admin_site.register(ExternalCareTeam, ExternalCareTeamAdmin)
admin_site.register(Appointment, AppointmentAdmin)
admin_site.register(Employee, EmployeeAdmin)
admin_site.register(DailyReport, DailyReportAdmin)
admin_site.register(MedicalHistory, MedicalHistoryAdmin)
admin_site.register(MedicationRegimen, MedicationRegimenAdmin)
admin_site.register(ClientProgram, ClientProgramAdmin)
admin_site.register(Timesheet, TimesheetAdmin)
admin_site.register(PTO, PTOAdmin)
admin_site.register(TimesheetSubmission, TimesheetSubmissionAdmin)
admin_site.register(ProfilePicture, ProfilePictureAdmin)
admin_site.register(Announcement, AnnouncementAdmin)
admin_site.register(EmployeeRequest, EmployeeRequestAdmin)
admin_site.register(ClientReport, ClientReportAdmin)


