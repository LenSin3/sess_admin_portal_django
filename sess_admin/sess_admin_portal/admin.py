from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from .models import Address, RegionalCenter, Client, Program, Category, Diagnosis, Medication, ClientFamily, ExternalCareTeam, Appointment, Employee, DailyReport, MedicalHistory, MedicationRegimen, ClientProgram, Timesheet, PTO, TimesheetSubmission

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

