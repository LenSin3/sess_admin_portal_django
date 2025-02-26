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
]