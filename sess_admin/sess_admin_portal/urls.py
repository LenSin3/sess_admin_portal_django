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
    path('timesheets/', views.admin_timesheets, name='admin_timesheets'),
    path('approve_timesheet/<int:submission_id>/', views.approve_timesheet, name='approve_timesheet'),
    path('reject_timesheet/<int:submission_id>/', views.reject_timesheet, name='reject_timesheet'),
]