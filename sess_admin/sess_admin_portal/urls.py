from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('timesheet_management/', views.timesheet_management, name='timesheet_management'),
    path('timesheet_management/edit/<int:submission_id>/', views.timesheet_management, name='edit_timesheet'),
    path('timesheet/', views.view_timesheet, name='timesheet'),
    path('timesheet_success/', views.timesheet_success, name='timesheet_success'),
    
    # Client management (main view handles all sections)
    path('client_management/', views.client_management, name='client_management'),
    
    # Daily report CRUD operations
    path('daily_report/add/<int:client_id>/', views.add_daily_report, name='add_daily_report'),
    path('daily_report/edit/<int:report_id>/', views.edit_daily_report, name='edit_daily_report'),
    path('daily_report/view/<int:report_id>/', views.view_daily_report, name='view_daily_report'),
    path('daily_report/delete/<int:report_id>/', views.delete_daily_report, name='delete_daily_report'),
    
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile and settings
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    
    # Admin analytics
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    
    # Announcement management
    path('announcements/', views.manage_announcements, name='manage_announcements'),
    path('announcements/create/', views.create_announcement, name='create_announcement'),
    path('announcements/<int:announcement_id>/edit/', views.edit_announcement, name='edit_announcement'),
    path('announcements/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),
    path('announcements/<int:announcement_id>/view/', views.view_announcement, name='view_announcement'),
    
    # Admin timesheet management
    # Admin timesheet management
    path('timesheets/', views.admin_timesheets, name='admin_timesheets'),
    path('approve-timesheet/<int:submission_id>/', views.approve_timesheet, name='approve_timesheet'),
    path('reject-timesheet/<int:submission_id>/', views.reject_timesheet, name='reject_timesheet'),
    path('timesheet-details/<int:submission_id>/', views.get_timesheet_details, name='get_timesheet_details'),
    path('batch-process-timesheets/', views.batch_process_timesheets, name='batch_process_timesheets'),
    
    # New PTO Management
    path('pto/', views.pto_management, name='pto_management'),
    path('pto/create/', views.create_pto, name='create_pto'),
    path('pto/<int:pto_id>/edit/', views.edit_pto, name='edit_pto'),
    path('pto/<int:pto_id>/delete/', views.delete_pto, name='delete_pto'),
    path('pto/<int:pto_id>/view/', views.view_pto, name='view_pto'),
    path('approve-pto/<int:pto_id>/', views.approve_pto, name='approve_pto'),
    path('reject-pto/<int:pto_id>/', views.reject_pto, name='reject_pto'),
    path('admin-pto/', views.admin_pto, name='admin_pto'),
    
    # General Requests
    path('requests/', views.employee_requests, name='employee_requests'),
    path('requests/create/', views.create_request, name='create_request'),
    path('requests/<int:request_id>/view/', views.view_request, name='view_request'),
    path('admin-requests/', views.admin_requests, name='admin_requests'),
    path('resolve-request/<int:request_id>/', views.resolve_request, name='resolve_request'),
    
    # Client Reports
    path('reports/', views.client_reports, name='client_reports'),
    path('reports/create/<str:report_type>/', views.create_report, name='create_report'),
    path('reports/<int:report_id>/view/', views.view_report, name='view_report'),
    path('admin-reports/', views.admin_reports, name='admin_reports'),
]