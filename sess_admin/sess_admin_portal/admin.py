from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from .models import Address, RegionalCenter, Client, Program, Category, Diagnosis, Medication, ClientFamily, ExternalCareTeam, \
Appointment, Employee, DailyReport, MedicalHistory, MedicationRegimen, ClientProgram, Timesheet, PTO, TimesheetSubmission, \
    ProfilePicture, Announcement

# Register your models here.
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

class AddressInline(GenericStackedInline):
    model = Address
    extra = 0

class ClientAdmin(admin.ModelAdmin):
    inlines = [AddressInline]

class EmployeeAdmin(admin.ModelAdmin):
    inlines = [AddressInline]
    
class ClientFamilyAdmin(admin.ModelAdmin):
    inlines = [AddressInline]
    
class ExternalCareTeamAdmin(admin.ModelAdmin):
    inlines = [AddressInline]
    
class AppointmentsAdmin(admin.ModelAdmin):
    inlines = [AddressInline]
    
class RegionalCenterAdmin(admin.ModelAdmin):
    inlines = [AddressInline]
    
class ProgramsAdmin(admin.ModelAdmin):
    inlines = [AddressInline]   

class TimesheetAdmin(admin.ModelAdmin):
    list_display = ("date", "time_in", "time_out", "employee", "submission")
    list_filter = ("employee", "date")
    search_fields = ("employee__first_name", "employee__last_name", "date")

class TimesheetSubmissionAdmin(admin.ModelAdmin):
    list_display = ("employee", "start_date", "end_date", "status")
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("employee__first_name", "employee__last_name")
    
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'announcement_type', 'date_posted', 'expiry_date', 'posted_by', 'important', 'is_expired')
    list_filter = ('announcement_type', 'important', 'date_posted')
    search_fields = ('title', 'content')
    date_hierarchy = 'date_posted'
    readonly_fields = ('date_posted',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'announcement_type', 'important')
        }),
        ('Timing', {
            'fields': ('date_posted', 'expiry_date'),
        }),
        ('Author', {
            'fields': ('posted_by',),
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-set the posted_by field to current user if not set"""
        if not obj.posted_by:
            obj.posted_by = request.user
        super().save_model(request, obj, form, change)
        
    def is_expired(self, obj):
        """Display if an announcement is expired"""
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = "Expired"

admin.site.register(Timesheet, TimesheetAdmin)
admin.site.register(TimesheetSubmission, TimesheetSubmissionAdmin)
    
admin.site.register(Address)
admin.site.register(RegionalCenter, RegionalCenterAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Program, ProgramsAdmin)
admin.site.register(Category)
admin.site.register(Diagnosis)
admin.site.register(Medication)
admin.site.register(ClientFamily, ClientFamilyAdmin)
admin.site.register(ExternalCareTeam, ExternalCareTeamAdmin)
admin.site.register(Appointment, AppointmentsAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(DailyReport)
admin.site.register(MedicalHistory)
admin.site.register(MedicationRegimen)
admin.site.register(ClientProgram)
# admin.site.register(Timesheet)
admin.site.register(PTO)
# admin.site.register(TimesheetSubmission)
admin.site.register(ProfilePicture)

