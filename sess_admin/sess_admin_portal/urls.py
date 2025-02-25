from django.urls import path
from . import views

urlpatterns = [
  path('', views.home, name='home'),
  path('timesheet_management/', views.timesheet_management, name='timesheet_management'),
  path('timesheet_management/edit/<int:submission_id>/', views.timesheet_management, name='edit_timesheet'),
  path('timesheet/', views.view_timesheet, name='timesheet'),
  path('timesheet_success/', views.timesheet_success, name='timesheet_success'),
  path('client_management/', views.client_management, name='client_management'),
  path('client_management/edit/<int:client_id>/', views.client_management, name='edit_client'),
]