from django.shortcuts import render, get_object_or_404, redirect
from datetime import timedelta, date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Timesheet, TimesheetSubmission

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

def client_management(request):
    return render(request, "sess_admin_portal/client_management.html")
