from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import timedelta, date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Timesheet, TimesheetSubmission, Client, MedicalHistory, Appointment, DailyReport, Employee, ClientFamily, MedicationRegimen, ClientProgram, ExternalCareTeam 


def login_view(request):
    """View to handle user login"""
    # If user is already logged in, redirect to home
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Check if there's a next parameter in the URL
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            return render(request, 'sess_admin_portal/login.html', {
                'error_message': 'Invalid username or password.'
            })
    
    return render(request, 'sess_admin_portal/login.html')

def logout_view(request):
    """View to handle user logout"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

# Create your views here.
def home(request):
    return render(request, "sess_admin_portal/home.html")

from django.shortcuts import render

def timesheet_success(request):
    return render(request, "sess_admin_portal/timesheet_success.html")  # Create this template


@login_required
def timesheet_management(request, submission_id=None):
    today = date.today()
    if today.day <= 15:
        start_date = today.replace(day=1)
        end_date = today.replace(day=15)
    else:
        start_date = today.replace(day=16)
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)

    days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    employee = request.user.employee  # Ensure the user is linked to an Employee

    # If editing, retrieve existing submission and timesheets
    submission = None
    timesheets = {}

    if submission_id:
        submission = get_object_or_404(TimesheetSubmission, id=submission_id, employee=employee)
        # timesheets = {t.date: t for t in submission.timesheets.all()}  # Convert QuerySet to dictionary

    if request.method == "POST":
        # If there's an existing submission, delete it before resubmission
        if submission:
            submission.timesheets.all().delete()
            submission.delete()

        # Create a new submission
        submission = TimesheetSubmission.objects.create(
            employee=employee,
            start_date=start_date,
            end_date=end_date,
            status=TimesheetSubmission.STATUS_PENDING,
        )

        # Save timesheets for each day
        for day in days:
            time_in = request.POST.get(f"time_in_{day}")
            time_out = request.POST.get(f"time_out_{day}")
            if time_in and time_out:
                Timesheet.objects.create(
                    date=day,
                    time_in=time_in,
                    time_out=time_out,
                    employee=employee,
                    submission=submission,
                    status=TimesheetSubmission.STATUS_PENDING,
                )

        return redirect("timesheet_success")

    context = {
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "submission": submission,
        "timesheets": timesheets,  # Pass timesheets as a dictionary
    }

    return render(request, "sess_admin_portal/timesheet_management.html", context)

@login_required
def view_timesheet(request):
    # Determine the current pay period
    today = date.today()
    if today.day <= 15:
        start_date = today.replace(day=1)
        end_date = today.replace(day=15)
    else:
        start_date = today.replace(day=16)
        # Simple way to get the end of month
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
    
    employee = request.user.employee  # Adjust if your User model links to Employee differently

    # Look for a submission for the current pay period for this employee
    submission = TimesheetSubmission.objects.filter(
        employee__id=employee.id,
        start_date=start_date,
        end_date=end_date
    ).first()

    # Calculate total hours for all timesheets
    total_hours = sum(t.total_hours for t in submission.timesheets.all()) if submission else 0


    context = {
        "submission": submission,
        "total_hours": total_hours,
        "start_date": start_date,
        "end_date": end_date,
    }
    return render(request, "sess_admin_portal/timesheet.html", context)

def edit_timesheet(request, submission_id):
    submission = get_object_or_404(TimesheetSubmission, id=submission_id)

    if request.method == "POST":
        # Clear existing timesheets before resubmission
        submission.timesheets.all().delete()

        # Recreate timesheets from the new data
        for timesheet in request.POST.getlist('timesheets'):
            Timesheet.objects.create(
                date=timesheet['date'],
                time_in=timesheet['time_in'],
                time_out=timesheet['time_out'],
                employee=submission.employee,
                submission=submission,
                status=TimesheetSubmission.STATUS_PENDING  # Reset status to pending
            )

        # Redirect to timesheet submission page
        return redirect("sess_admin_portal/timesheet_management")  # Redirects to timesheet form for resubmission
    return render(request, "sess_admin_portal/edit_timesheet.html", {"submission": submission})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import (
    Client, ClientFamily, MedicalHistory, ExternalCareTeam, 
    ClientProgram, MedicationRegimen, Appointment, DailyReport, Employee
)

@login_required
def client_management(request):
    """Main client management view that handles all client data display."""
    employee = get_object_or_404(Employee, user=request.user)
    
    # Get the client assigned to the employee
    client = get_object_or_404(Client, id=employee.client.id)
    
    # Initialize context with client data
    context = {
        'client': client,
    }
    
    # Handle different views based on the GET parameter
    view = request.GET.get('view', 'client-details')
    
    if view == 'client-family':
        # Fetch family members
        client_family = ClientFamily.objects.filter(client=client)
        # Find emergency contact (assuming first family member is emergency contact)
        emergency_contact = client_family.first()
        context.update({
            'client_family': client_family,
            'emergency_contact': emergency_contact
        })
    
    elif view == 'medical-history':
        # Fetch medical history records
        medical_history = MedicalHistory.objects.filter(client=client).order_by('-date')
        context.update({
            'medical_history': medical_history
        })
    
    elif view == 'external-care-team':
        # Since ExternalCareTeam isn't directly linked to clients in your model,
        # this is a stub that would need to be customized based on your actual relationship
        external_care_team = ExternalCareTeam.objects.all()
        context.update({
            'external_care_team': external_care_team
        })
    
    elif view == 'programs':
        # Fetch client programs
        client_programs = ClientProgram.objects.filter(client=client)
        # Get a single client program for the client info card
        client_program = client_programs.first()
        context.update({
            'client_programs': client_programs,
            'client_program': client_program
        })
    
    elif view == 'medications':
        # Fetch medication regimens
        medication_regimens = MedicationRegimen.objects.filter(client=client)
        context.update({
            'medication_regimens': medication_regimens
        })
    
    elif view == 'appointments':
        # Fetch appointments and separate upcoming from past
        today = timezone.now().date()
        
        upcoming_appointments = Appointment.objects.filter(
            client=client, 
            appointment_date__gte=today
        ).order_by('appointment_date', 'appointment_time')
        
        past_appointments = Appointment.objects.filter(
            client=client, 
            appointment_date__lt=today
        ).order_by('-appointment_date', '-appointment_time')
        
        context.update({
            'upcoming_appointments': upcoming_appointments,
            'past_appointments': past_appointments
        })
    
    elif view == 'activity-report':
        # Fetch daily activity reports
        daily_reports = DailyReport.objects.filter(client=client).order_by('-date', '-time')
        context.update({
            'daily_reports': daily_reports
        })
    
    else:  # Default to client details
        # For the client details view, show the most recent activity reports
        recent_reports = DailyReport.objects.filter(client=client).order_by('-date', '-time')[:3]
        # Find emergency contact
        emergency_contact = ClientFamily.objects.filter(client=client).first()
        # Get client program for the client info card
        client_program = ClientProgram.objects.filter(client=client).first()
        
        context.update({
            'recent_reports': recent_reports,
            'emergency_contact': emergency_contact,
            'client_program': client_program
        })
    
    return render(request, 'sess_admin_portal/client_management.html', context)

@login_required
def add_daily_report(request, client_id):
    """View to add a new daily activity report"""
    client = get_object_or_404(Client, id=client_id)
    employee = get_object_or_404(Employee, user=request.user)
    
    # Ensure employee has access to this client
    if employee.client.id != client.id:
        return redirect('client_management')
    
    if request.method == 'POST':
        # Process form submission
        date = request.POST.get('date')
        time = request.POST.get('time')
        report = request.POST.get('report')
        
        if date and time and report:
            # Create new report
            DailyReport.objects.create(
                date=date,
                time=time,
                report=report,
                client=client,
                employee=employee
            )
            return redirect('client_management') + '?view=activity-report'
        
    # Default - show form
    context = {
        'client': client,
        'today': timezone.now().date().isoformat(),
        'now': timezone.now().time().strftime('%H:%M')
    }
    return render(request, 'sess_admin_portal/daily_report_form.html', context)

@login_required
def edit_daily_report(request, report_id):
    """View to edit an existing daily report"""
    report = get_object_or_404(DailyReport, id=report_id)
    employee = get_object_or_404(Employee, user=request.user)
    
    # Ensure this employee created the report
    if report.employee.id != employee.id:
        return redirect('client_management') + '?view=activity-report'
    
    if request.method == 'POST':
        # Process form submission
        date = request.POST.get('date')
        time = request.POST.get('time')
        report_text = request.POST.get('report')
        
        if date and time and report_text:
            # Update report
            report.date = date
            report.time = time
            report.report = report_text
            report.save()
            return redirect('client_management') + '?view=activity-report'
    
    # Default - show form with existing data
    context = {
        'report': report,
        'client': report.client
    }
    return render(request, 'sess_admin_portal/daily_report_form.html', context)

@login_required
def view_daily_report(request, report_id):
    """View to see details of a daily report"""
    report = get_object_or_404(DailyReport, id=report_id)
    employee = get_object_or_404(Employee, user=request.user)
    
    # Ensure employee has access to this client
    if employee.client.id != report.client.id:
        return redirect('client_management')
    
    context = {
        'report': report,
        'client': report.client,
        'can_edit': report.employee.id == employee.id
    }
    return render(request, 'sess_admin_portal/daily_report_detail.html', context)

@login_required
def delete_daily_report(request, report_id):
    """View to delete a daily report"""
    report = get_object_or_404(DailyReport, id=report_id)
    employee = get_object_or_404(Employee, user=request.user)
    
    # Ensure this employee created the report
    if report.employee.id == employee.id:
        report.delete()
    
    return redirect('client_management') + '?view=activity-report'

@login_required
def client_medical_history(request):
    """Fetch and display client's diagnosis details."""
    employee = request.user.employee
    client = get_object_or_404(MedicalHistory, id=employee.client.id)
    return render(request, "sess_admin_portal/client_medical_history.html", {"client": client})

@login_required
def client_external_care_team(request):
    """Fetch and display client's external care team."""
    employee = request.user.employee
    client = get_object_or_404(ExternalCareTeam, id=employee.client.id)
    return render(request, "sess_admin_portal/client_external_care_team.html", {"client": client})

@login_required
def client_programs(request):
    """Fetch and display client's assigned programs."""
    employee = request.user.employee
    client = get_object_or_404(ClientProgram, id=employee.client.id)
    return render(request, "sess_admin_portal/client_programs.html", {"client": client})

@login_required
def client_medications(request):
    """Fetch and display client's medications."""
    employee = request.user.employee
    client = get_object_or_404(MedicationRegimen, id=employee.client.id)
    return render(request, "sess_admin_portal/client_medication_regimen.html", {"client": client})

@login_required
def client_appointments(request):
    """Fetch and display client's appointments."""
    employee = request.user.employee
    client = get_object_or_404(Appointment, id=employee.client.id)
    return render(request, "sess_admin_portal/client_appointments.html", {"client": client})

@login_required
def client_activity_report(request):
    """Fetch and display client's daily activity reports."""
    employee = request.user.employee
    client = get_object_or_404(DailyReport, id=employee.client.id)
    return render(request, "sess_admin_portal/client_daily_report.html", {"client": client})

@login_required
def client_family(request):
    """Fetch and display client's family details."""
    employee = request.user.employee
    client = get_object_or_404(ClientFamily, id=employee.client.id)
    return render(request, "sess_admin_portal/client_family.html", {"client": client})
