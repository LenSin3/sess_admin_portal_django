from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Avg, Q, Case, When
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from datetime import timedelta, date, datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .forms import AnnouncementForm
from .models import Timesheet, TimesheetSubmission, Client, MedicalHistory, Appointment, DailyReport, Employee, ClientFamily, \
    MedicationRegimen, ClientProgram, ExternalCareTeam, ProfilePicture, RegionalCenter, Announcement, PTO, EmployeeRequest, ClientReport
        


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

@login_required
def profile(request):
    """View for employee profile management"""
    employee = get_object_or_404(Employee, user=request.user)
    
    if request.method == 'POST':
        # Handle form submission for profile updates
        if 'update_profile' in request.POST:
            # Only allow updating certain fields
            employee.phone_number = request.POST.get('phone_number', employee.phone_number)
            employee.email = request.POST.get('email', employee.email)
            employee.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
            
        # Handle profile picture upload
        if 'upload_picture' in request.POST and request.FILES.get('profile_picture'):
            # Get ContentType for Employee model
            content_type = ContentType.objects.get_for_model(Employee)
            
            # Delete existing profile picture if any
            ProfilePicture.objects.filter(
                content_type=content_type,
                object_id=employee.id
            ).delete()
            
            # Create new profile picture
            profile_pic = ProfilePicture(
                content_type=content_type,
                object_id=employee.id,
                image=request.FILES['profile_picture']
            )
            profile_pic.save()
            
            messages.success(request, 'Profile picture updated successfully!')
            return redirect('profile')
    
    # Get current profile picture
    content_type = ContentType.objects.get_for_model(Employee)
    profile_picture = ProfilePicture.objects.filter(
        content_type=content_type,
        object_id=employee.id
    ).first()
    
    context = {
        'employee': employee,
        'profile_picture': profile_picture
    }
    
    return render(request, 'sess_admin_portal/profile.html', context)

@login_required
def settings(request):
    """View for user account settings"""
    if request.method == 'POST':
        # Handle password change
        if 'change_password' in request.POST:
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Check if current password is correct
            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
                return redirect('settings')
            
            # Check if new passwords match
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
                return redirect('settings')
            
            # Check password strength
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return redirect('settings')
            
            # Update password
            request.user.set_password(new_password)
            request.user.save()
            
            # Update session so user stays logged in
            update_session_auth_hash(request, request.user)
            
            messages.success(request, 'Password updated successfully!')
        
        # Handle notification preferences
        elif 'notification_settings' in request.POST:
            # This would typically update user preferences in a real app
            messages.success(request, 'Notification preferences saved!')
        
        # Handle app settings
        elif 'app_settings' in request.POST:
            # This would typically update app settings in a real app
            messages.success(request, 'App settings saved!')
    
    return render(request, 'sess_admin_portal/settings.html')


def is_admin_or_superuser(user):
    """Check if user is an admin or superuser"""
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin_or_superuser)
def analytics_dashboard(request):
    """Admin analytics dashboard view"""
    # Get counts of clients
    total_clients = Client.objects.count()
    active_clients = Client.objects.filter(active=True).count()
    inactive_clients = total_clients - active_clients
    
    # Get counts of employees
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(active=True).count()
    
    # Employee roles distribution
    employee_roles = Employee.objects.values('role').annotate(count=Count('id'))
    
    # Reports statistics
    today = timezone.now().date()
    month_start = today.replace(day=1)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    last_month_end = month_start - timedelta(days=1)
    
    reports_this_month = DailyReport.objects.filter(date__gte=month_start).count()
    reports_last_month = DailyReport.objects.filter(
        date__gte=last_month_start,
        date__lte=last_month_end
    ).count()
    
    # Calculate trends
    days_in_month = (today - month_start).days + 1
    reports_per_day = round(reports_this_month / days_in_month, 1) if days_in_month > 0 else 0
    
    # Calculate percentage change
    if reports_last_month > 0:
        report_trend = round(((reports_this_month / reports_last_month) - 1) * 100)
    else:
        report_trend = 100  # If no reports last month, show 100% increase
    
    # Hours logged statistics - manually calculate since total_hours is a property
    timesheets = Timesheet.objects.filter(date__gte=month_start)
    total_timesheets = timesheets.count()
    
    # Calculate hours manually
    hours_logged = 0
    for timesheet in timesheets:
        if timesheet.time_in and timesheet.time_out:
            time_in_dt = datetime.combine(timesheet.date, timesheet.time_in)
            time_out_dt = datetime.combine(timesheet.date, timesheet.time_out)
            delta = time_out_dt - time_in_dt
            hours = delta.total_seconds() / 3600.0  # Convert seconds to hours
            hours_logged += hours
    
    # Average hours per employee
    if active_employees > 0:
        avg_hours_per_employee = round(hours_logged / active_employees, 1)
    else:
        avg_hours_per_employee = 0
    
    # Regional centers with client counts
    regional_centers = []
    for center in RegionalCenter.objects.all():
        regional_centers.append({
            'name': center.regional_center,
            'location': str(center.address) if center.address else 'N/A',
            'client_count': Client.objects.filter(regional_center=center).count()
        })
    
    # Current pay period information
    if today.day <= 15:
        pay_period_start = today.replace(day=1)
        pay_period_end = today.replace(day=15)
    else:
        pay_period_start = today.replace(day=16)
        next_month = pay_period_start.replace(day=28) + timedelta(days=4)
        pay_period_end = next_month - timedelta(days=next_month.day)
    
    pay_period = f"{pay_period_start.strftime('%b %d')} - {pay_period_end.strftime('%b %d, %Y')}"
    timesheet_due_date = pay_period_end.strftime("%b %d, %Y")
    
    # Timesheet submission stats
    total_active_employees = active_employees
    
    # Count submissions by status
    submissions = TimesheetSubmission.objects.filter(
        start_date=pay_period_start,
        end_date=pay_period_end
    )
    
    submitted_count = submissions.filter(
        status=TimesheetSubmission.STATUS_APPROVED
    ).count()
    
    pending_approvals = submissions.filter(
        status=TimesheetSubmission.STATUS_PENDING
    ).count()
    
    in_progress_count = 0  # Would need logic to determine employees who have started but not submitted
    
    # Calculate not started (employees who haven't submitted)
    submitted_employee_ids = submissions.values_list('employee_id', flat=True)
    not_started_count = Employee.objects.filter(
        active=True
    ).exclude(
        id__in=submitted_employee_ids
    ).count()
    
    # Calculate submission rate
    if total_active_employees > 0:
        submission_rate = round((submitted_count / total_active_employees) * 100)
    else:
        submission_rate = 0
    
    # Calculate pending percentage
    if total_active_employees > 0:
        pending_percentage = round((pending_approvals / total_active_employees) * 100)
    else:
        pending_percentage = 0
    
    # Sample system activities
    # In a real app, this would come from an activity log model
    system_activities = [
        {
            'title': 'New Employee Added',
            'description': 'Emily Johnson was added as a Caregiver',
            'user': 'Admin',
            'time': '2 hours ago',
            'icon': 'bi-person-plus',
            'icon_class': 'bg-success-light'
        },
        {
            'title': 'Client Information Updated',
            'description': 'Contact information updated for John Smith',
            'user': 'Sarah Davis',
            'time': '4 hours ago',
            'icon': 'bi-pencil',
            'icon_class': 'bg-primary-light'
        },
        {
            'title': 'Timesheet Approved',
            'description': 'Timesheet for May 1-15 approved',
            'user': 'Admin',
            'time': '1 day ago',
            'icon': 'bi-check-circle',
            'icon_class': 'bg-success-light'
        },
        {
            'title': 'New Regional Center Added',
            'description': 'East Valley Regional Center was added',
            'user': 'Admin',
            'time': '2 days ago',
            'icon': 'bi-building',
            'icon_class': 'bg-info-light'
        },
        {
            'title': 'System Maintenance',
            'description': 'Database backup completed',
            'user': 'System',
            'time': '3 days ago',
            'icon': 'bi-gear',
            'icon_class': 'bg-warning-light'
        }
    ]
    
    context = {
        'total_clients': total_clients,
        'active_clients': active_clients,
        'inactive_clients': inactive_clients,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'employee_roles': employee_roles,
        'reports_this_month': reports_this_month,
        'reports_per_day': reports_per_day,
        'report_trend': report_trend,
        'hours_logged': int(hours_logged),
        'total_timesheets': total_timesheets,
        'avg_hours_per_employee': avg_hours_per_employee,
        'regional_centers': regional_centers,
        'pay_period': pay_period,
        'timesheet_due_date': timesheet_due_date,
        'submission_rate': submission_rate,
        'pending_approvals': pending_approvals,
        'pending_percentage': pending_percentage,
        'submitted_count': submitted_count,
        'in_progress_count': in_progress_count,
        'not_started_count': not_started_count,
        'system_activities': system_activities
    }
    
    return render(request, 'sess_admin_portal/analytics_dashboard.html', context)

@login_required
def home(request):
    """Enhanced home view with dynamic announcements"""
    # Get the employee and associated client
    employee = get_object_or_404(Employee, user=request.user)
    client = employee.client
    
    # Get active announcements (not expired)
    today = timezone.now().date()
    announcements = Announcement.objects.filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=today)
    ).order_by('-important', '-date_posted')[:5]  # Show 5 most recent announcements, prioritizing important ones
    
    # Format announcements for template
    company_announcements = []
    for announcement in announcements:
        # Format days ago text
        if announcement.days_ago == 0:
            time_text = "Today"
        elif announcement.days_ago == 1:
            time_text = "Yesterday"
        else:
            time_text = f"{announcement.days_ago} days ago"
            
        company_announcements.append({
            'id': announcement.id,
            'title': announcement.title,
            'content': announcement.content,
            'date': announcement.date_posted,
            'time_text': time_text,
            'posted_by': announcement.posted_by.get_full_name() if announcement.posted_by else "Admin",
            'read_more': len(announcement.content) > 150,  # Show read more if content is long
            'type': announcement.announcement_type,
            'important': announcement.important,
            'image': announcement.image.url if announcement.image else None
        })
    
    context = {
        'client': client,
        'company_announcements': company_announcements,
        # ... rest of your existing context ...
    }
    
    return render(request, "sess_admin_portal/home.html", context)

@login_required
@user_passes_test(is_admin_or_superuser)
def manage_announcements(request):
    """View to manage all announcements"""
    announcements = Announcement.objects.all().order_by('-date_posted')
    
    # Filter options
    announcement_type = request.GET.get('type')
    if announcement_type:
        announcements = announcements.filter(announcement_type=announcement_type)
        
    show_expired = request.GET.get('show_expired') == 'true'
    if not show_expired:
        today = timezone.now().date()
        announcements = announcements.filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=today)
        )
    
    context = {
        'announcements': announcements,
        'announcement_types': Announcement.TYPE_CHOICES,
        'selected_type': announcement_type,
        'show_expired': show_expired
    }
    
    return render(request, 'sess_admin_portal/manage_announcements.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def create_announcement(request):
    """View to create a new announcement"""
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.posted_by = request.user
            announcement.save()
            messages.success(request, 'Announcement created successfully!')
            return redirect('manage_announcements')
    else:
        form = AnnouncementForm()
    
    context = {
        'form': form,
        'title': 'Create Announcement'
    }
    
    return render(request, 'sess_admin_portal/announcement_form.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def edit_announcement(request, announcement_id):
    """View to edit an existing announcement"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Announcement updated successfully!')
            return redirect('manage_announcements')
    else:
        form = AnnouncementForm(instance=announcement)
    
    context = {
        'form': form,
        'announcement': announcement,
        'title': 'Edit Announcement'
    }
    
    return render(request, 'sess_admin_portal/announcement_form.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def delete_announcement(request, announcement_id):
    """View to delete an announcement"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'Announcement deleted successfully!')
        return redirect('manage_announcements')
    
    context = {
        'announcement': announcement
    }
    
    return render(request, 'sess_admin_portal/confirm_delete_announcement.html', context)

@login_required
def view_announcement(request, announcement_id):
    """View to see a single announcement in detail"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    context = {
        'announcement': announcement
    }
    
    return render(request, 'sess_admin_portal/view_announcement.html', context)


@login_required
def timesheet_management(request, submission_id=None):
    """View for submitting a timesheet for the current pay period"""
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
        # Get timesheets as a dictionary keyed by date for easy access in template
        for timesheet in submission.timesheets.all():
            timesheets[timesheet.date] = timesheet

    if request.method == "POST":
        # If there's an existing submission for this period, delete it before resubmission
        existing_submission = TimesheetSubmission.objects.filter(
            employee=employee,
            start_date=start_date,
            end_date=end_date
        ).first()
        
        if existing_submission:
            existing_submission.timesheets.all().delete()
            existing_submission.delete()

        # Create a new submission
        submission = TimesheetSubmission.objects.create(
            employee=employee,
            start_date=start_date,
            end_date=end_date,
            status=TimesheetSubmission.STATUS_PENDING,
            submitted_at=timezone.now()
        )

       # Save timesheets for each day
        total_hours = 0
        for day in days:
            day_str = day.strftime('%Y-%m-%d')
            time_in = request.POST.get(f"time_in_{day_str}")
            time_out = request.POST.get(f"time_out_{day_str}")
            if time_in and time_out:
                # Create the timesheet entry
                timesheet = Timesheet.objects.create(
                    date=day,
                    time_in=time_in,
                    time_out=time_out,
                    employee=employee,
                    submission=submission,
                    status=TimesheetSubmission.STATUS_PENDING
                )
                
                # Calculate hours manually to ensure accuracy
                time_in_dt = datetime.combine(day, datetime.strptime(time_in, '%H:%M').time())
                time_out_dt = datetime.combine(day, datetime.strptime(time_out, '%H:%M').time())
                delta = time_out_dt - time_in_dt
                
                if delta.total_seconds() > 0:
                    hours = delta.total_seconds() / 3600.0
                    total_hours += hours

        # Store submission date in session for success page
        request.session['timesheet_submitted'] = {
            'submission_id': submission.id,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'total_hours': total_hours,
            'submitted_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return redirect("timesheet_success")

    context = {
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "submission": submission,
        "timesheets": timesheets,
        "today": today
    }

    return render(request, "sess_admin_portal/timesheet_management.html", context)

@login_required
def timesheet_success(request):
    """Success page after timesheet submission"""
    # Get submission info from session
    submission_info = request.session.get('timesheet_submitted', {})
    
    if not submission_info:
        # If no submission info in session, redirect to timesheet page
        return redirect('timesheet')
    
    context = {
        'start_date': date.fromisoformat(submission_info.get('start_date')),
        'end_date': date.fromisoformat(submission_info.get('end_date')),
        'total_hours': submission_info.get('total_hours', 0),
        'submitted_at': timezone.datetime.strptime(
            submission_info.get('submitted_at'), 
            '%Y-%m-%d %H:%M:%S'
        )
    }
    
    # Clear the session data
    if 'timesheet_submitted' in request.session:
        del request.session['timesheet_submitted']
    
    return render(request, "sess_admin_portal/timesheet_success.html", context)

@login_required
def view_timesheet(request):
    """View for seeing timesheet summary and history"""
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
    
    employee = request.user.employee

    # Look for a submission for the current pay period
    submission = TimesheetSubmission.objects.filter(
        employee=employee,
        start_date=start_date,
        end_date=end_date
    ).first()

        # Calculate total hours for current submission
    total_hours = 0
    if submission:
        # Get all associated timesheets
        timesheet_entries = submission.timesheets.all()
        
        # Calculate total hours by summing the individual timesheet hours
        for timesheet in timesheet_entries:
            # Calculate hours manually for reliability
            if timesheet.time_in and timesheet.time_out:
                time_in_dt = datetime.combine(timesheet.date, timesheet.time_in)
                time_out_dt = datetime.combine(timesheet.date, timesheet.time_out)
                delta = time_out_dt - time_in_dt
                
                # Add to total hours (converting seconds to hours)
                if delta.total_seconds() > 0:  # Only add positive time differences
                    hours = delta.total_seconds() / 3600.0  # Convert to hours
                    total_hours += hours

    # Get previous submissions (excluding current)
    previous_submissions = []
    prev_submissions_qs = TimesheetSubmission.objects.filter(
        employee=employee
    ).exclude(
        id=submission.id if submission else None
    ).order_by('-end_date')[:10]  # Get the 10 most recent
    
    # Calculate total hours for each previous submission
    for prev_sub in prev_submissions_qs:
        prev_hours = sum(t.total_hours for t in prev_sub.timesheets.all())
        previous_submissions.append({
            'id': prev_sub.id,
            'start_date': prev_sub.start_date,
            'end_date': prev_sub.end_date,
            'status': prev_sub.status,
            'submitted_at': prev_sub.submitted_at,
            'total_hours': prev_hours
        })

    context = {
        "submission": submission,
        "total_hours": total_hours,
        "start_date": start_date,
        "end_date": end_date,
        "previous_submissions": previous_submissions
    }
    
    return render(request, "sess_admin_portal/timesheet.html", context)

@login_required
def edit_timesheet(request, submission_id):
    """View for editing an existing timesheet submission"""
    employee = request.user.employee
    submission = get_object_or_404(TimesheetSubmission, id=submission_id, employee=employee)
    
    # Check if the timesheet can be edited (only if status is Pending or Rejected)
    if submission.status not in [TimesheetSubmission.STATUS_PENDING, TimesheetSubmission.STATUS_REJECTED]:
        messages.error(request, "This timesheet cannot be edited because it has already been approved.")
        return redirect('timesheet')
    
    # Redirect to the timesheet management view with the submission ID
    return redirect('timesheet_management', submission_id=submission_id)

def is_admin_or_superuser(user):
    """Check if user is admin or superuser"""
    return user.is_staff or user.is_superuser

"""
OLD Admin Timesheet Management Views
===================================


"""

# Update to the admin_timesheets view in views.py
@login_required
@user_passes_test(is_admin_or_superuser)
def admin_timesheets(request):
    """Admin view for managing all timesheet submissions"""
    # Determine the current pay period
    today = date.today()
    if today.day <= 15:
        start_date = today.replace(day=1)
        end_date = today.replace(day=15)
        current_period = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
    else:
        start_date = today.replace(day=16)
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
        current_period = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
    
    # Apply filters if provided
    status_filter = request.GET.get('status')
    employee_filter = request.GET.get('employee')
    sort_by = request.GET.get('sort_by', 'latest')
    
    # Get requested pay period if specified
    period = request.GET.get('period')
    if period:
        try:
            year, month, half = period.split('-')
            year, month = int(year), int(month)
            if half == '1':  # First half of month
                start_date = date(year, month, 1)
                end_date = date(year, month, 15)
            else:  # Second half of month
                start_date = date(year, month, 16)
                # Get last day of month
                if month == 12:
                    next_month = date(year + 1, 1, 1)
                else:
                    next_month = date(year, month + 1, 1)
                end_date = next_month - timedelta(days=1)
            
            current_period = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
        except:
            pass  # If period format is invalid, use current period
    
    # Get all active employees
    employees = Employee.objects.filter(active=True)
    
    # Get submissions for current period
    submissions = TimesheetSubmission.objects.filter(
        start_date=start_date,
        end_date=end_date
    )
    
    # Apply filters
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    
    if employee_filter:
        submissions = submissions.filter(employee_id=employee_filter)
    
    # Apply sorting
    if sort_by == 'latest':
        submissions = submissions.order_by('-submitted_at')
    elif sort_by == 'status':
        submissions = submissions.order_by('status', '-submitted_at')
    elif sort_by == 'employee':
        submissions = submissions.order_by('employee__last_name', 'employee__first_name')
    elif sort_by == 'hours':
        # We can't directly sort by computed total_hours, so we'll have to sort after retrieving
        pass
    
    # Calculate statistics
    total_submissions = submissions.count()
    pending_submissions = submissions.filter(status=TimesheetSubmission.STATUS_PENDING).count()
    
    # Calculate total hours for all submissions
    total_hours = 0
    for sub in submissions:
        sub_hours = sum(t.total_hours for t in sub.timesheets.all())
        sub.total_hours = sub_hours  # Add total_hours to each submission object
        total_hours += sub_hours
    
    # If sorting by hours, we need to do it after calculating hours
    if sort_by == 'hours':
        submissions = sorted(submissions, key=lambda x: x.total_hours, reverse=True)
    
    # Get previous periods for dropdown
    previous_periods = []
    
    # First half of current month
    current_month = today.replace(day=1)
    if today.day > 15:
        prev_start = today.replace(day=1)
        prev_end = today.replace(day=15)
        previous_periods.append({
            'id': f"{prev_start.year}-{prev_start.month}-1",
            'label': f"{prev_start.strftime('%b')} 1-15, {prev_start.year}"
        })
    
    # Add past periods (up to 6 months back)
    for i in range(6):
        # Subtract one month
        if current_month.month == 1:
            current_month = date(current_month.year - 1, 12, 1)
        else:
            current_month = date(current_month.year, current_month.month - 1, 1)
        
        # Add second half of month
        previous_periods.append({
            'id': f"{current_month.year}-{current_month.month}-2",
            'label': f"{current_month.strftime('%b')} 16-{(current_month.replace(day=28) + timedelta(days=4) - timedelta(days=1)).day}, {current_month.year}"
        })
        
        # Add first half of month
        previous_periods.append({
            'id': f"{current_month.year}-{current_month.month}-1",
            'label': f"{current_month.strftime('%b')} 1-15, {current_month.year}"
        })
    
    context = {
        'submissions': submissions,
        'employees': employees,
        'total_submissions': total_submissions,
        'pending_submissions': pending_submissions,
        'total_hours': round(total_hours, 1),
        'current_period': current_period,
        'previous_periods': previous_periods,
        # Add selected filters to context for template
        'selected_status': status_filter,
        'selected_employee': employee_filter,
        'selected_sort': sort_by
    }
    
    return render(request, 'sess_admin_portal/admin_timesheets.html', context)

# Update the approve_timesheet and reject_timesheet views
@login_required
@user_passes_test(is_admin_or_superuser)
def approve_timesheet(request, submission_id):
    """Approve a timesheet submission"""
    submission = get_object_or_404(TimesheetSubmission, id=submission_id)
    
    # Update status to approved
    submission.status = TimesheetSubmission.STATUS_APPROVED
    submission.save()
    
    # Also update all associated timesheets
    for timesheet in submission.timesheets.all():
        timesheet.status = TimesheetSubmission.STATUS_APPROVED
        timesheet.save()
    
    messages.success(request, f"Timesheet for {submission.employee.first_name} {submission.employee.last_name} has been approved.")
    
    # Return to previous page if available
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    return redirect('admin_timesheets')

@login_required
@user_passes_test(is_admin_or_superuser)
def reject_timesheet(request, submission_id):
    """Reject a timesheet submission"""
    submission = get_object_or_404(TimesheetSubmission, id=submission_id)
    
    # Update status to rejected
    submission.status = TimesheetSubmission.STATUS_REJECTED
    submission.save()
    
    # Also update all associated timesheets
    for timesheet in submission.timesheets.all():
        timesheet.status = TimesheetSubmission.STATUS_REJECTED
        timesheet.save()
    
    messages.warning(request, f"Timesheet for {submission.employee.first_name} {submission.employee.last_name} has been rejected.")
    
    # Return to previous page if available
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    return redirect('admin_timesheets')

# Add an API endpoint to get timesheet details
@login_required
@user_passes_test(is_admin_or_superuser)
def get_timesheet_details(request, submission_id):
    """API to get timesheet details for the modal"""
    submission = get_object_or_404(TimesheetSubmission, id=submission_id)
    timesheets = submission.timesheets.all().order_by('date')
    
    # Calculate total hours
    total_hours = sum(t.total_hours for t in timesheets)
    
    context = {
        'submission': submission,
        'timesheets': timesheets,
        'total_hours': total_hours
    }
    
    return render(request, 'sess_admin_portal/timesheet_details_modal.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def batch_process_timesheets(request):
    """Process multiple timesheet submissions at once"""
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids_json = request.POST.get('selected_ids')
        
        if action and selected_ids_json:
            try:
                import json
                selected_ids = json.loads(selected_ids_json)
                
                # Process each submission
                count = 0
                for submission_id in selected_ids:
                    submission = TimesheetSubmission.objects.get(id=submission_id)
                    
                    if action == 'approve':
                        # Update status to approved
                        submission.status = TimesheetSubmission.STATUS_APPROVED
                        submission.save()
                        
                        # Also update all associated timesheets
                        for timesheet in submission.timesheets.all():
                            timesheet.status = TimesheetSubmission.STATUS_APPROVED
                            timesheet.save()
                        
                        count += 1
                    
                    elif action == 'reject':
                        # Update status to rejected
                        submission.status = TimesheetSubmission.STATUS_REJECTED
                        submission.save()
                        
                        # Also update all associated timesheets
                        for timesheet in submission.timesheets.all():
                            timesheet.status = TimesheetSubmission.STATUS_REJECTED
                            timesheet.save()
                        
                        count += 1
                
                if action == 'approve':
                    messages.success(request, f"{count} timesheet submissions approved successfully.")
                else:
                    messages.warning(request, f"{count} timesheet submissions rejected.")
            
            except Exception as e:
                messages.error(request, f"Error processing timesheets: {str(e)}")
    
    # Return to previous page if available
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    return redirect('admin_timesheets')


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
            # Fix: Use reverse to get URL, then add query string
            return redirect(reverse('client_management') + '?view=activity-report')
        
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
        # Fix: Use reverse with query string
        return redirect(reverse('client_management') + '?view=activity-report')
    
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
            # Fix: Use reverse with query string
            return redirect(reverse('client_management') + '?view=activity-report')
    
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
    
    # Fix: Use reverse with query string
    return redirect(reverse('client_management') + '?view=activity-report')

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


@login_required
def pto_management(request):
    """View for employees to see and manage their PTO requests"""
    employee = get_object_or_404(Employee, user=request.user)
    
    # Get all PTO requests for this employee
    pto_requests = PTO.objects.filter(employee=employee).order_by('-submitted_at')
    
    # Calculate PTO statistics
    total_requests = pto_requests.count()
    pending_requests = pto_requests.filter(status=PTO.STATUS_PENDING).count()
    approved_requests = pto_requests.filter(status=PTO.STATUS_APPROVED).count()
    rejected_requests = pto_requests.filter(status=PTO.STATUS_REJECTED).count()
    
    # Calculate total days for the year
    today = timezone.now().date()
    year_start = date(today.year, 1, 1)
    year_end = date(today.year, 12, 31)
    
    days_taken = 0
    days_pending = 0
    
    for pto in pto_requests.filter(start_date__year=today.year):
        if pto.status == PTO.STATUS_APPROVED:
            days_taken += pto.days_requested
        elif pto.status == PTO.STATUS_PENDING:
            days_pending += pto.days_requested
    
    # For demonstration purposes, we'll assume each employee gets 20 PTO days per year
    # In a real application, this would come from a policy or employee record
    total_pto_days = 20
    remaining_days = total_pto_days - days_taken - days_pending
    
    context = {
        'pto_requests': pto_requests,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'days_taken': days_taken,
        'days_pending': days_pending,
        'total_pto_days': total_pto_days,
        'remaining_days': remaining_days
    }
    
    return render(request, 'sess_admin_portal/pto_management.html', context)

@login_required
def create_pto(request):
    """View for creating a new PTO request"""
    employee = get_object_or_404(Employee, user=request.user)
    
    if request.method == 'POST':
        pto_type = request.POST.get('pto_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date', None)
        start_time = request.POST.get('start_time', None)
        end_time = request.POST.get('end_time', None)
        reason = request.POST.get('reason')
        
        # Basic validation
        if not (pto_type and start_date and reason):
            messages.error(request, "Please fill in all required fields.")
            return redirect('create_pto')
        
        # Create the PTO request
        try:
            pto = PTO(
                employee=employee,
                pto_type=pto_type,
                start_date=start_date,
                reason=reason,
                status=PTO.STATUS_PENDING
            )
            
            # Set optional fields based on type
            if pto_type == PTO.TYPE_MULTIPLE_DAYS and end_date:
                pto.end_date = end_date
            
            if pto_type == PTO.TYPE_PARTIAL_DAY and start_time and end_time:
                pto.start_time = start_time
                pto.end_time = end_time
            
            pto.save()
            
            messages.success(request, "PTO request submitted successfully. It is now pending approval.")
            return redirect('pto_management')
        
        except Exception as e:
            messages.error(request, f"Error creating PTO request: {str(e)}")
            return redirect('create_pto')
    
    context = {
        'employee': employee,
        'today': timezone.now().date().isoformat(),
    }
    
    return render(request, 'sess_admin_portal/create_pto.html', context)

@login_required
def edit_pto(request, pto_id):
    """View for editing an existing PTO request"""
    employee = get_object_or_404(Employee, user=request.user)
    pto = get_object_or_404(PTO, id=pto_id, employee=employee)
    
    # Only allow editing of pending requests
    if pto.status != PTO.STATUS_PENDING:
        messages.error(request, "You can only edit pending PTO requests.")
        return redirect('pto_management')
    
    if request.method == 'POST':
        pto_type = request.POST.get('pto_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date', None)
        start_time = request.POST.get('start_time', None)
        end_time = request.POST.get('end_time', None)
        reason = request.POST.get('reason')
        
        # Basic validation
        if not (pto_type and start_date and reason):
            messages.error(request, "Please fill in all required fields.")
            return redirect('edit_pto', pto_id=pto_id)
        
        # Update the PTO request
        try:
            pto.pto_type = pto_type
            pto.start_date = start_date
            pto.reason = reason
            
            # Reset optional fields
            pto.end_date = None
            pto.start_time = None
            pto.end_time = None
            
            # Set optional fields based on type
            if pto_type == PTO.TYPE_MULTIPLE_DAYS and end_date:
                pto.end_date = end_date
            
            if pto_type == PTO.TYPE_PARTIAL_DAY and start_time and end_time:
                pto.start_time = start_time
                pto.end_time = end_time
            
            pto.save()
            
            messages.success(request, "PTO request updated successfully.")
            return redirect('pto_management')
        
        except Exception as e:
            messages.error(request, f"Error updating PTO request: {str(e)}")
            return redirect('edit_pto', pto_id=pto_id)
    
    context = {
        'pto': pto,
        'employee': employee
    }
    
    return render(request, 'sess_admin_portal/edit_pto.html', context)

@login_required
def delete_pto(request, pto_id):
    """View for deleting a PTO request"""
    employee = get_object_or_404(Employee, user=request.user)
    pto = get_object_or_404(PTO, id=pto_id, employee=employee)
    
    # Only allow deletion of pending requests
    if pto.status != PTO.STATUS_PENDING:
        messages.error(request, "You can only delete pending PTO requests.")
        return redirect('pto_management')
    
    if request.method == 'POST':
        # Delete the PTO request
        pto.delete()
        messages.success(request, "PTO request deleted successfully.")
        return redirect('pto_management')
    
    context = {
        'pto': pto
    }
    
    return render(request, 'sess_admin_portal/delete_pto.html', context)

@login_required
def view_pto(request, pto_id):
    """View for seeing details of a specific PTO request"""
    employee = get_object_or_404(Employee, user=request.user)
    
    # For employees, only show their own PTO
    if not (request.user.is_staff or request.user.is_superuser):
        pto = get_object_or_404(PTO, id=pto_id, employee=employee)
    else:
        # Admins can view any PTO
        pto = get_object_or_404(PTO, id=pto_id)
    
    context = {
        'pto': pto,
        'is_admin': request.user.is_staff or request.user.is_superuser
    }
    
    return render(request, 'sess_admin_portal/view_pto.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def admin_pto(request):
    """Admin view for managing all PTO requests"""
    # Get filter parameters
    status_filter = request.GET.get('status')
    employee_filter = request.GET.get('employee')
    date_filter = request.GET.get('date_range', 'upcoming')
    
    # Base query - all PTO requests
    pto_requests = PTO.objects.all()
    
    # Apply filters
    if status_filter:
        pto_requests = pto_requests.filter(status=status_filter)
    
    if employee_filter:
        pto_requests = pto_requests.filter(employee_id=employee_filter)
    
    # Apply date filtering
    today = timezone.now().date()
    if date_filter == 'upcoming':
        pto_requests = pto_requests.filter(start_date__gte=today)
    elif date_filter == 'past':
        pto_requests = pto_requests.filter(start_date__lt=today)
    elif date_filter == 'this_month':
        month_start = today.replace(day=1)
        if today.month == 12:
            next_month = date(today.year + 1, 1, 1)
        else:
            next_month = date(today.year, today.month + 1, 1)
        month_end = next_month - timedelta(days=1)
        pto_requests = pto_requests.filter(start_date__gte=month_start, start_date__lte=month_end)
    
    # Order by most recent and by status (pending first)
    pto_requests = pto_requests.order_by('status', '-start_date')
    
    # Get all active employees for the filter
    employees = Employee.objects.filter(active=True).order_by('last_name', 'first_name')
    
    context = {
        'pto_requests': pto_requests,
        'employees': employees,
        'selected_status': status_filter,
        'selected_employee': employee_filter,
        'selected_date': date_filter,
        'pending_count': PTO.objects.filter(status=PTO.STATUS_PENDING).count(),
        'today': today
    }
    
    return render(request, 'sess_admin_portal/admin_pto.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def approve_pto(request, pto_id):
    """Approve a PTO request"""
    pto = get_object_or_404(PTO, id=pto_id)
    
    # Only process pending requests
    if pto.status != PTO.STATUS_PENDING:
        messages.error(request, "This PTO request has already been processed.")
        return redirect('admin_pto')
    
    # Get admin notes if provided
    admin_notes = request.POST.get('admin_notes', '')
    
    # Update request
    pto.status = PTO.STATUS_APPROVED
    pto.reviewed_at = timezone.now()
    pto.reviewed_by = request.user
    if admin_notes:
        pto.notes = admin_notes
    pto.save()
    
    messages.success(request, f"PTO request for {pto.employee.first_name} {pto.employee.last_name} approved successfully.")
    
    # Return to previous page if available
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    return redirect('admin_pto')

@login_required
@user_passes_test(is_admin_or_superuser)
def reject_pto(request, pto_id):
    """Reject a PTO request"""
    pto = get_object_or_404(PTO, id=pto_id)
    
    # Only process pending requests
    if pto.status != PTO.STATUS_PENDING:
        messages.error(request, "This PTO request has already been processed.")
        return redirect('admin_pto')
    
    # Get admin notes if provided
    admin_notes = request.POST.get('admin_notes', '')
    
    # Update request
    pto.status = PTO.STATUS_REJECTED
    pto.reviewed_at = timezone.now()
    pto.reviewed_by = request.user
    if admin_notes:
        pto.notes = admin_notes
    pto.save()
    
    messages.warning(request, f"PTO request for {pto.employee.first_name} {pto.employee.last_name} rejected.")
    
    # Return to previous page if available
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    return redirect('admin_pto')

@login_required
def pto_management(request):
    """View for employees to see and manage their PTO requests"""
    employee = get_object_or_404(Employee, user=request.user)
    
    # Get all PTO requests for this employee
    pto_requests = PTO.objects.filter(employee=employee).order_by('-submitted_at')
    
    # Calculate PTO statistics
    total_requests = pto_requests.count()
    pending_requests = pto_requests.filter(status=PTO.STATUS_PENDING).count()
    approved_requests = pto_requests.filter(status=PTO.STATUS_APPROVED).count()
    rejected_requests = pto_requests.filter(status=PTO.STATUS_REJECTED).count()
    
    # Calculate total days for the year
    today = timezone.now().date()
    year_start = date(today.year, 1, 1)
    year_end = date(today.year, 12, 31)
    
    days_taken = 0
    days_pending = 0
    
    for pto in pto_requests.filter(start_date__year=today.year):
        if pto.status == PTO.STATUS_APPROVED:
            days_taken += pto.days_requested
        elif pto.status == PTO.STATUS_PENDING:
            days_pending += pto.days_requested
    
    # For demonstration purposes, we'll assume each employee gets 20 PTO days per year
    # In a real application, this would come from a policy or employee record
    total_pto_days = 20
    remaining_days = total_pto_days - days_taken - days_pending
    
    context = {
        'pto_requests': pto_requests,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'days_taken': days_taken,
        'days_pending': days_pending,
        'total_pto_days': total_pto_days,
        'remaining_days': remaining_days
    }
    
    return render(request, 'sess_admin_portal/pto_management.html', context)

@login_required
def create_pto(request):
    """View for creating a new PTO request"""
    employee = get_object_or_404(Employee, user=request.user)
    
    if request.method == 'POST':
        pto_type = request.POST.get('pto_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date', None)
        start_time = request.POST.get('start_time', None)
        end_time = request.POST.get('end_time', None)
        reason = request.POST.get('reason')
        
        # Basic validation
        if not (pto_type and start_date and reason):
            messages.error(request, "Please fill in all required fields.")
            return redirect('create_pto')
        
        # Create the PTO request
        try:
            pto = PTO(
                employee=employee,
                pto_type=pto_type,
                start_date=start_date,
                reason=reason,
                status=PTO.STATUS_PENDING
            )
            
            # Set optional fields based on type
            if pto_type == PTO.TYPE_MULTIPLE_DAYS and end_date:
                pto.end_date = end_date
            
            if pto_type == PTO.TYPE_PARTIAL_DAY and start_time and end_time:
                pto.start_time = start_time
                pto.end_time = end_time
            
            pto.save()
            
            messages.success(request, "PTO request submitted successfully. It is now pending approval.")
            return redirect('pto_management')
        
        except Exception as e:
            messages.error(request, f"Error creating PTO request: {str(e)}")
            return redirect('create_pto')
    
    context = {
        'employee': employee,
        'today': timezone.now().date().isoformat(),
    }
    
    return render(request, 'sess_admin_portal/create_pto.html', context)

@login_required
def edit_pto(request, pto_id):
    """View for editing an existing PTO request"""
    employee = get_object_or_404(Employee, user=request.user)
    pto = get_object_or_404(PTO, id=pto_id, employee=employee)
    
    # Only allow editing of pending requests
    if pto.status != PTO.STATUS_PENDING:
        messages.error(request, "You can only edit pending PTO requests.")
        return redirect('pto_management')
    
    if request.method == 'POST':
        pto_type = request.POST.get('pto_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date', None)
        start_time = request.POST.get('start_time', None)
        end_time = request.POST.get('end_time', None)
        reason = request.POST.get('reason')
        
        # Basic validation
        if not (pto_type and start_date and reason):
            messages.error(request, "Please fill in all required fields.")
            return redirect('edit_pto', pto_id=pto_id)
        
        # Update the PTO request
        try:
            pto.pto_type = pto_type
            pto.start_date = start_date
            pto.reason = reason
            
            # Reset optional fields
            pto.end_date = None
            pto.start_time = None
            pto.end_time = None
            
            # Set optional fields based on type
            if pto_type == PTO.TYPE_MULTIPLE_DAYS and end_date:
                pto.end_date = end_date
            
            if pto_type == PTO.TYPE_PARTIAL_DAY and start_time and end_time:
                pto.start_time = start_time
                pto.end_time = end_time
            
            pto.save()
            
            messages.success(request, "PTO request updated successfully.")
            return redirect('pto_management')
        
        except Exception as e:
            messages.error(request, f"Error updating PTO request: {str(e)}")
            return redirect('edit_pto', pto_id=pto_id)
    
    context = {
        'pto': pto,
        'employee': employee
    }
    
    return render(request, 'sess_admin_portal/edit_pto.html', context)

@login_required
def delete_pto(request, pto_id):
    """View for deleting a PTO request"""
    employee = get_object_or_404(Employee, user=request.user)
    pto = get_object_or_404(PTO, id=pto_id, employee=employee)
    
    # Only allow deletion of pending requests
    if pto.status != PTO.STATUS_PENDING:
        messages.error(request, "You can only delete pending PTO requests.")
        return redirect('pto_management')
    
    if request.method == 'POST':
        # Delete the PTO request
        pto.delete()
        messages.success(request, "PTO request deleted successfully.")
        return redirect('pto_management')
    
    context = {
        'pto': pto
    }
    
    return render(request, 'sess_admin_portal/delete_pto.html', context)

@login_required
def view_pto(request, pto_id):
    """View for seeing details of a specific PTO request"""
    employee = get_object_or_404(Employee, user=request.user)
    
    # For employees, only show their own PTO
    if not (request.user.is_staff or request.user.is_superuser):
        pto = get_object_or_404(PTO, id=pto_id, employee=employee)
    else:
        # Admins can view any PTO
        pto = get_object_or_404(PTO, id=pto_id)
    
    context = {
        'pto': pto,
        'is_admin': request.user.is_staff or request.user.is_superuser
    }
    
    return render(request, 'sess_admin_portal/view_pto.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def admin_pto(request):
    """Admin view for managing all PTO requests"""
    # Get filter parameters
    status_filter = request.GET.get('status')
    employee_filter = request.GET.get('employee')
    date_filter = request.GET.get('date_range', 'upcoming')
    
    # Base query - all PTO requests
    pto_requests = PTO.objects.all()
    
    # Apply filters
    if status_filter:
        pto_requests = pto_requests.filter(status=status_filter)
    
    if employee_filter:
        pto_requests = pto_requests.filter(employee_id=employee_filter)
    
    # Apply date filtering
    today = timezone.now().date()
    if date_filter == 'upcoming':
        pto_requests = pto_requests.filter(start_date__gte=today)
    elif date_filter == 'past':
        pto_requests = pto_requests.filter(start_date__lt=today)
    elif date_filter == 'this_month':
        month_start = today.replace(day=1)
        if today.month == 12:
            next_month = date(today.year + 1, 1, 1)
        else:
            next_month = date(today.year, today.month + 1, 1)
        month_end = next_month - timedelta(days=1)
        pto_requests = pto_requests.filter(start_date__gte=month_start, start_date__lte=month_end)
    
    # Order by most recent and by status (pending first)
    pto_requests = pto_requests.order_by('status', '-start_date')
    
    # Get all active employees for the filter
    employees = Employee.objects.filter(active=True).order_by('last_name', 'first_name')
    
    context = {
        'pto_requests': pto_requests,
        'employees': employees,
        'selected_status': status_filter,
        'selected_employee': employee_filter,
        'selected_date': date_filter,
        'pending_count': PTO.objects.filter(status=PTO.STATUS_PENDING).count(),
        'today': today
    }
    
    return render(request, 'sess_admin_portal/admin_pto.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def approve_pto(request, pto_id):
    """Approve a PTO request"""
    pto = get_object_or_404(PTO, id=pto_id)
    
    # Only process pending requests
    if pto.status != PTO.STATUS_PENDING:
        messages.error(request, "This PTO request has already been processed.")
        return redirect('admin_pto')
    
    # Get admin notes if provided
    admin_notes = request.POST.get('admin_notes', '')
    
    # Update request
    pto.status = PTO.STATUS_APPROVED
    pto.reviewed_at = timezone.now()
    pto.reviewed_by = request.user
    if admin_notes:
        pto.notes = admin_notes
    pto.save()
    
    messages.success(request, f"PTO request for {pto.employee.first_name} {pto.employee.last_name} approved successfully.")
    
    # Return to previous page if available
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    return redirect('admin_pto')

@login_required
@user_passes_test(is_admin_or_superuser)
def reject_pto(request, pto_id):
    """Reject a PTO request"""
    pto = get_object_or_404(PTO, id=pto_id)
    
    # Only process pending requests
    if pto.status != PTO.STATUS_PENDING:
        messages.error(request, "This PTO request has already been processed.")
        return redirect('admin_pto')
    
    # Get admin notes if provided
    admin_notes = request.POST.get('admin_notes', '')
    
    # Update request
    pto.status = PTO.STATUS_REJECTED
    pto.reviewed_at = timezone.now()
    pto.reviewed_by = request.user
    if admin_notes:
        pto.notes = admin_notes
    pto.save()
    
    messages.warning(request, f"PTO request for {pto.employee.first_name} {pto.employee.last_name} rejected.")
    
    # Return to previous page if available
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    return redirect('admin_pto')

@login_required
def employee_requests(request):
    """View for employees to see and manage their requests"""
    employee = get_object_or_404(Employee, user=request.user)
    
    # Get all requests for this employee
    requests = EmployeeRequest.objects.filter(employee=employee).order_by('-submitted_at')
    
    # Get filter parameters
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    
    # Apply filters if provided
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    if type_filter:
        requests = requests.filter(request_type=type_filter)
    
    # Calculate requests statistics
    total_requests = requests.count()
    pending_requests = requests.filter(status=EmployeeRequest.STATUS_PENDING).count()
    in_progress_requests = requests.filter(status=EmployeeRequest.STATUS_IN_PROGRESS).count()
    resolved_requests = requests.filter(status=EmployeeRequest.STATUS_RESOLVED).count()
    rejected_requests = requests.filter(status=EmployeeRequest.STATUS_REJECTED).count()
    
    context = {
        'requests': requests,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'in_progress_requests': in_progress_requests,
        'resolved_requests': resolved_requests,
        'rejected_requests': rejected_requests,
        'selected_status': status_filter,
        'selected_type': type_filter
    }
    
    return render(request, 'sess_admin_portal/employee_requests.html', context)

@login_required
def create_request(request):
    """View for creating a new request"""
    employee = get_object_or_404(Employee, user=request.user)
    
    if request.method == 'POST':
        request_type = request.POST.get('request_type')
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        
        # Basic validation
        if not (request_type and subject and description):
            messages.error(request, "Please fill in all required fields.")
            return redirect('create_request')
        
        # Create the request
        try:
            employee_request = EmployeeRequest(
                employee=employee,
                request_type=request_type,
                subject=subject,
                description=description,
                status=EmployeeRequest.STATUS_PENDING
            )
            employee_request.save()
            
            messages.success(request, "Your request has been submitted successfully.")
            return redirect('employee_requests')
        
        except Exception as e:
            messages.error(request, f"Error creating request: {str(e)}")
            return redirect('create_request')
    
    context = {
        'employee': employee,
    }
    
    return render(request, 'sess_admin_portal/create_request.html', context)

@login_required
def view_request(request, request_id):
    """View for seeing details of a specific request"""
    # For regular employees, only show their own requests
    if not (request.user.is_staff or request.user.is_superuser):
        employee = get_object_or_404(Employee, user=request.user)
        employee_request = get_object_or_404(EmployeeRequest, id=request_id, employee=employee)
    else:
        # Admins can view any request
        employee_request = get_object_or_404(EmployeeRequest, id=request_id)
    
    context = {
        'employee_request': employee_request,
        'is_admin': request.user.is_staff or request.user.is_superuser
    }
    
    return render(request, 'sess_admin_portal/view_request.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def admin_requests(request):
    """Admin view for managing all employee requests"""
    # Get filter parameters
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    employee_filter = request.GET.get('employee')
    
    # Base query - all requests
    requests = EmployeeRequest.objects.all()
    
    # Apply filters
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    if type_filter:
        requests = requests.filter(request_type=type_filter)
    
    if employee_filter:
        requests = requests.filter(employee_id=employee_filter)
    
    # Order by status (pending first) and submission date
    requests = requests.order_by(
        Case(
            When(status=EmployeeRequest.STATUS_PENDING, then=0),
            When(status=EmployeeRequest.STATUS_IN_PROGRESS, then=1),
            When(status=EmployeeRequest.STATUS_RESOLVED, then=2),
            When(status=EmployeeRequest.STATUS_REJECTED, then=3),
            default=4,
            output_field=models.IntegerField(),
        ),
        '-submitted_at'
    )
    
    # Get all active employees for the filter
    employees = Employee.objects.filter(active=True).order_by('last_name', 'first_name')
    
    # Calculate request statistics
    total_requests = requests.count()
    pending_requests = requests.filter(status=EmployeeRequest.STATUS_PENDING).count()
    in_progress_requests = requests.filter(status=EmployeeRequest.STATUS_IN_PROGRESS).count()
    resolved_requests = requests.filter(status=EmployeeRequest.STATUS_RESOLVED).count()
    
    context = {
        'requests': requests,
        'employees': employees,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'in_progress_requests': in_progress_requests,
        'resolved_requests': resolved_requests,
        'selected_status': status_filter,
        'selected_type': type_filter,
        'selected_employee': employee_filter
    }
    return render(request, 'sess_admin_portal/admin_requests.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def resolve_request(request, request_id):
    """View for resolving, rejecting, or marking a request as in progress"""
    employee_request = get_object_or_404(EmployeeRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'in_progress':
            # Mark request as in progress
            employee_request.status = EmployeeRequest.STATUS_IN_PROGRESS
            employee_request.resolution_notes = notes if notes else None
            employee_request.save()
            
            messages.info(request, f"Request #{employee_request.id} has been marked as 'In Progress'.")
            
        elif action == 'resolve':
            # Resolve the request
            employee_request.status = EmployeeRequest.STATUS_RESOLVED
            employee_request.resolved_at = timezone.now()
            employee_request.resolved_by = request.user
            employee_request.resolution_notes = notes
            employee_request.save()
            
            messages.success(request, f"Request #{employee_request.id} has been resolved successfully.")
            
        elif action == 'reject':
            # Reject the request
            employee_request.status = EmployeeRequest.STATUS_REJECTED
            employee_request.resolved_at = timezone.now()
            employee_request.resolved_by = request.user
            employee_request.resolution_notes = notes
            employee_request.save()
            
            messages.warning(request, f"Request #{employee_request.id} has been rejected.")
        
        else:
            messages.error(request, "Invalid action specified.")
    
    # Redirect back to the referring page if available, otherwise to admin_requests
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    return redirect('admin_requests')

@login_required
def client_reports(request):
    """View for employees to see and manage their client reports"""
    employee = get_object_or_404(Employee, user=request.user)
    
    # Get all reports created by this employee
    reports = ClientReport.objects.filter(employee=employee).order_by('-created_at')
    
    # Get filter parameters
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    client_filter = request.GET.get('client')
    
    # Apply filters if provided
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    if type_filter:
        reports = reports.filter(report_type=type_filter)
    
    if client_filter:
        reports = reports.filter(client_id=client_filter)
    
    # Statistics
    total_reports = reports.count()
    draft_reports = reports.filter(status=ClientReport.STATUS_DRAFT).count()
    submitted_reports = reports.filter(status=ClientReport.STATUS_SUBMITTED).count()
    approved_reports = reports.filter(status=ClientReport.STATUS_APPROVED).count()
    needs_revision_reports = reports.filter(status=ClientReport.STATUS_NEEDS_REVISION).count()
    
    # Get clients this employee has access to
    # For simplicity, we're using the assigned client, but this could be expanded
    # to include all clients the employee has permission to access
    clients = [employee.client]
    
    context = {
        'reports': reports,
        'total_reports': total_reports,
        'draft_reports': draft_reports,
        'submitted_reports': submitted_reports,
        'approved_reports': approved_reports,
        'needs_revision_reports': needs_revision_reports,
        'clients': clients,
        'selected_status': status_filter,
        'selected_type': type_filter,
        'selected_client': client_filter,
        'report_types': ClientReport.TYPE_CHOICES
    }
    
    return render(request, 'sess_admin_portal/client_reports.html', context)

@login_required
def create_report(request, report_type):
    """View for creating a new client report"""
    employee = get_object_or_404(Employee, user=request.user)
    
    # Check if this is a valid report type
    valid_types = dict(ClientReport.TYPE_CHOICES)
    if report_type not in valid_types:
        messages.error(request, "Invalid report type specified.")
        return redirect('client_reports')
    
    # Get the client (currently just using assigned client)
    client = employee.client
    
    if request.method == 'POST':
        # Process form submission
        title = request.POST.get('title')
        report_date = request.POST.get('report_date')
        notes = request.POST.get('notes', '')
        
        # Collect form data based on report type
        form_data = {}
        
        # Each report type has different form fields
        if report_type == ClientReport.TYPE_INCIDENT:
            form_data = {
                'incident_date': request.POST.get('incident_date'),
                'incident_time': request.POST.get('incident_time'),
                'incident_location': request.POST.get('incident_location'),
                'description': request.POST.get('description'),
                'immediate_action': request.POST.get('immediate_action'),
                'medical_attention': request.POST.get('medical_attention') == 'on',
                'medical_attention_details': request.POST.get('medical_attention_details', ''),
                'witnesses': request.POST.get('witnesses', ''),
                'follow_up_required': request.POST.get('follow_up_required') == 'on',
                'follow_up_details': request.POST.get('follow_up_details', '')
            }
        
        elif report_type == ClientReport.TYPE_SLEEP_LOG:
            form_data = {
                'sleep_time': request.POST.get('sleep_time'),
                'wake_time': request.POST.get('wake_time'),
                'total_sleep': request.POST.get('total_sleep'),
                'sleep_quality': request.POST.get('sleep_quality'),
                'interruptions': request.POST.get('interruptions'),
                'sleep_aid_used': request.POST.get('sleep_aid_used') == 'on',
                'sleep_aid_details': request.POST.get('sleep_aid_details', ''),
                'notes': request.POST.get('sleep_notes', '')
            }
        
        elif report_type in [ClientReport.TYPE_IPP, ClientReport.TYPE_ANNUAL_SUPPORT]:
            form_data = {
                'goals': [],
                'strengths': request.POST.get('strengths', ''),
                'challenges': request.POST.get('challenges', ''),
                'support_needs': request.POST.get('support_needs', ''),
                'health_considerations': request.POST.get('health_considerations', ''),
                'living_situation': request.POST.get('living_situation', ''),
                'community_involvement': request.POST.get('community_involvement', ''),
                'education_employment': request.POST.get('education_employment', ''),
                'social_relationships': request.POST.get('social_relationships', ''),
                'transportation': request.POST.get('transportation', ''),
                'financial': request.POST.get('financial', ''),
                'cultural_considerations': request.POST.get('cultural_considerations', '')
            }
            
            # Process goals (dynamic fields)
            goal_count = int(request.POST.get('goal_count', 0))
            for i in range(1, goal_count + 1):
                goal = {
                    'goal': request.POST.get(f'goal_{i}', ''),
                    'strategies': request.POST.get(f'strategies_{i}', ''),
                    'timeline': request.POST.get(f'timeline_{i}', ''),
                    'progress_indicators': request.POST.get(f'progress_indicators_{i}', '')
                }
                if goal['goal']:  # Only add non-empty goals
                    form_data['goals'].append(goal)
        
        elif report_type == ClientReport.TYPE_QUARTERLY:
            form_data = {
                'quarter': request.POST.get('quarter'),
                'year': request.POST.get('year'),
                'goals_progress': request.POST.get('goals_progress', ''),
                'skills_development': request.POST.get('skills_development', ''),
                'health_status': request.POST.get('health_status', ''),
                'behavioral_observations': request.POST.get('behavioral_observations', ''),
                'social_interactions': request.POST.get('social_interactions', ''),
                'community_involvement': request.POST.get('community_involvement', ''),
                'challenges': request.POST.get('challenges', ''),
                'successes': request.POST.get('successes', ''),
                'recommendations': request.POST.get('recommendations', '')
            }
        
        elif report_type == ClientReport.TYPE_MEDICAL:
            form_data = {
                'visit_date': request.POST.get('visit_date'),
                'provider_name': request.POST.get('provider_name'),
                'facility': request.POST.get('facility'),
                'reason_for_visit': request.POST.get('reason_for_visit'),
                'diagnosis': request.POST.get('diagnosis', ''),
                'treatment_plan': request.POST.get('treatment_plan', ''),
                'medications_prescribed': request.POST.get('medications_prescribed', ''),
                'follow_up_needed': request.POST.get('follow_up_needed') == 'on',
                'follow_up_date': request.POST.get('follow_up_date', ''),
                'follow_up_details': request.POST.get('follow_up_details', ''),
                'notes': request.POST.get('medical_notes', '')
            }
        
        elif report_type == ClientReport.TYPE_INITIAL_ASSESSMENT:
            form_data = {
                'assessment_date': request.POST.get('assessment_date'),
                'assessor_name': request.POST.get('assessor_name'),
                'presenting_issues': request.POST.get('presenting_issues', ''),
                'medical_history': request.POST.get('medical_history', ''),
                'family_history': request.POST.get('family_history', ''),
                'educational_history': request.POST.get('educational_history', ''),
                'employment_history': request.POST.get('employment_history', ''),
                'social_history': request.POST.get('social_history', ''),
                'strengths': request.POST.get('assessment_strengths', ''),
                'needs': request.POST.get('assessment_needs', ''),
                'recommended_services': request.POST.get('recommended_services', ''),
                'diagnosis': request.POST.get('assessment_diagnosis', ''),
                'prognosis': request.POST.get('prognosis', ''),
                'notes': request.POST.get('assessment_notes', '')
            }
        
        # Basic validation
        if not (title and report_date):
            messages.error(request, "Please fill in all required fields.")
            # Render the form again with submitted data
            context = {
                'report_type': report_type,
                'report_type_display': valid_types[report_type],
                'client': client,
                'form_data': form_data,  # Pass back the submitted data
                'title': title,
                'report_date': report_date,
                'notes': notes
            }
            return render(request, 'sess_admin_portal/create_report.html', context)
        
        # Get submit action (save as draft or submit)
        submit_action = request.POST.get('submit_action', 'draft')
        
        # Create the report
        try:
            report = ClientReport(
                client=client,
                employee=employee,
                report_type=report_type,
                title=title,
                report_date=report_date,
                content=form_data,
                notes=notes,
                status=ClientReport.STATUS_DRAFT
            )
            report.save()
            
            # If the action is submit, update the status
            if submit_action == 'submit':
                report.submit()
                messages.success(request, f"{report_type} report submitted successfully for approval.")
            else:
                messages.success(request, f"{report_type} report saved as draft.")
            
            return redirect('client_reports')
        
        except Exception as e:
            messages.error(request, f"Error creating report: {str(e)}")
            # Render the form again with submitted data
            context = {
                'report_type': report_type,
                'report_type_display': valid_types[report_type],
                'client': client,
                'form_data': form_data,  # Pass back the submitted data
                'title': title,
                'report_date': report_date,
                'notes': notes
            }
            return render(request, 'sess_admin_portal/create_report.html', context)
    
    # GET request - show the form
    context = {
        'report_type': report_type,
        'report_type_display': valid_types[report_type],
        'client': client,
        'today': timezone.now().date().isoformat()
    }
    
    return render(request, 'sess_admin_portal/create_report.html', context)

@login_required
def view_report(request, report_id):
    """View for seeing details of a specific report"""
    # For regular employees, only show their own reports
    if not (request.user.is_staff or request.user.is_superuser):
        employee = get_object_or_404(Employee, user=request.user)
        report = get_object_or_404(ClientReport, id=report_id, employee=employee)
    else:
        # Admins can view any report
        report = get_object_or_404(ClientReport, id=report_id)
    
    context = {
        'report': report,
        'is_admin': request.user.is_staff or request.user.is_superuser,
        'can_edit': report.is_editable and report.employee.user == request.user
    }
    
    return render(request, 'sess_admin_portal/view_report.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def admin_reports(request):
    """Admin view for managing all client reports"""
    # Get filter parameters
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    employee_filter = request.GET.get('employee')
    client_filter = request.GET.get('client')
    
    # Base query - all reports
    reports = ClientReport.objects.all()
    
    # Apply filters
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    if type_filter:
        reports = reports.filter(report_type=type_filter)
    
    if employee_filter:
        reports = reports.filter(employee_id=employee_filter)
    
    if client_filter:
        reports = reports.filter(client_id=client_filter)
    
    # Order by status and creation date
    reports = reports.order_by(
        Case(
            When(status=ClientReport.STATUS_SUBMITTED, then=0),
            When(status=ClientReport.STATUS_NEEDS_REVISION, then=1),
            When(status=ClientReport.STATUS_DRAFT, then=2),
            When(status=ClientReport.STATUS_APPROVED, then=3),
            default=4,
            output_field=models.IntegerField(),
        ),
        '-created_at'
    )
    
    # Get all active employees and clients for the filter
    employees = Employee.objects.filter(active=True).order_by('last_name', 'first_name')
    clients = Client.objects.filter(active=True).order_by('last_name', 'first_name')
    
    # Statistics
    total_reports = reports.count()
    submitted_reports = reports.filter(status=ClientReport.STATUS_SUBMITTED).count()
    needs_revision_reports = reports.filter(status=ClientReport.STATUS_NEEDS_REVISION).count()
    
    context = {
        'reports': reports,
        'employees': employees,
        'clients': clients,
        'total_reports': total_reports,
        'submitted_reports': submitted_reports,
        'needs_revision_reports': needs_revision_reports,
        'selected_status': status_filter,
        'selected_type': type_filter,
        'selected_employee': employee_filter,
        'selected_client': client_filter,
        'report_types': ClientReport.TYPE_CHOICES
    }
    
    return render(request, 'sess_admin_portal/admin_reports.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def approve_report(request, report_id):
    """Approve a client report"""
    report = get_object_or_404(ClientReport, id=report_id)
    
    # Only submitted reports can be approved
    if report.status != ClientReport.STATUS_SUBMITTED:
        messages.error(request, "Only submitted reports can be approved.")
        return redirect('admin_reports')
    
    # Process the approval
    report.approve(request.user)
    messages.success(request, f"Report '{report.title}' has been approved.")
    
    # Return to previous page if available
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    return redirect('admin_reports')

@login_required
@user_passes_test(is_admin_or_superuser)
def request_revision(request, report_id):
    """Request revision for a client report"""
    report = get_object_or_404(ClientReport, id=report_id)
    
    # Only submitted reports can be sent back for revision
    if report.status != ClientReport.STATUS_SUBMITTED:
        messages.error(request, "Only submitted reports can be sent back for revision.")
        return redirect('admin_reports')
    
    if request.method == 'POST':
        revision_notes = request.POST.get('revision_notes', '')
        
        # Update the report
        report.notes = revision_notes
        report.request_revision()
        
        messages.warning(request, f"Report '{report.title}' has been sent back for revision.")
    
    # Return to previous page if available
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    return redirect('admin_reports')

