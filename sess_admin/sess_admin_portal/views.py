from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Avg, Q
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
    MedicationRegimen, ClientProgram, ExternalCareTeam, ProfilePicture, RegionalCenter, Announcement


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
    
    # Get all active employees
    employees = Employee.objects.filter(active=True)
    
    # Get submissions for current period
    submissions = TimesheetSubmission.objects.filter(
        start_date=start_date,
        end_date=end_date
    ).order_by('-submitted_at')
    
    # Calculate statistics
    total_submissions = submissions.count()
    pending_submissions = submissions.filter(status=TimesheetSubmission.STATUS_PENDING).count()
    
    # Calculate total hours for all submissions
    total_hours = 0
    for sub in submissions:
        sub_hours = sum(t.total_hours for t in sub.timesheets.all())
        sub.total_hours = sub_hours  # Add total_hours to each submission object
        total_hours += sub_hours
    
    # Get previous periods for dropdown
    previous_periods = []
    
    # First half of current month
    if today.day > 15:
        prev_start = today.replace(day=1)
        prev_end = today.replace(day=15)
        previous_periods.append({
            'id': f"{prev_start.year}-{prev_start.month}-1",
            'label': f"{prev_start.strftime('%b')} 1-15, {prev_start.year}"
        })
    
    # Previous month, second half
    last_month = today.replace(day=1) - timedelta(days=1)
    prev_start = last_month.replace(day=16)
    prev_end = last_month
    previous_periods.append({
        'id': f"{prev_start.year}-{prev_start.month}-2",
        'label': f"{prev_start.strftime('%b')} 16-{prev_end.day}, {prev_start.year}"
    })
    
    # Previous month, first half
    prev_start = last_month.replace(day=1)
    prev_end = last_month.replace(day=15)
    previous_periods.append({
        'id': f"{prev_start.year}-{prev_start.month}-1",
        'label': f"{prev_start.strftime('%b')} 1-15, {prev_start.year}"
    })
    
    context = {
        'submissions': submissions,
        'employees': employees,
        'total_submissions': total_submissions,
        'pending_submissions': pending_submissions,
        'total_hours': round(total_hours, 1),
        'current_period': current_period,
        'previous_periods': previous_periods
    }
    
    return render(request, 'sess_admin_portal/admin_timesheets.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def approve_timesheet(request, submission_id):
    """Approve a timesheet submission"""
    submission = get_object_or_404(TimesheetSubmission, id=submission_id)
    
    # Update status to approved
    submission.status = TimesheetSubmission.STATUS_APPROVED
    submission.save()
    
    # Also update all associated timesheets
    submission.timesheets.all().update(status=TimesheetSubmission.STATUS_APPROVED)
    
    messages.success(request, f"Timesheet for {submission.employee.first_name} {submission.employee.last_name} has been approved.")
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
    submission.timesheets.all().update(status=TimesheetSubmission.STATUS_REJECTED)
    
    messages.warning(request, f"Timesheet for {submission.employee.first_name} {submission.employee.last_name} has been rejected.")
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
