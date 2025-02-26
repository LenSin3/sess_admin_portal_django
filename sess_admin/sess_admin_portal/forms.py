# Create a new file forms.py (or add to existing file)
from django import forms
from .models import Announcement

class AnnouncementForm(forms.ModelForm):
    """Form for creating and editing announcements"""
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'announcement_type', 'important', 'expiry_date', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'announcement_type': forms.Select(attrs={'class': 'form-select'}),
            'important': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }