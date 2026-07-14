from django.contrib import admin
from django import forms
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from .models import School, SchoolSettings
from accounts.models import User


class CreateSchoolWithAdminForm(forms.Form):
    name = forms.CharField(max_length=255, label='School Name')
    code = forms.CharField(max_length=50, label='School Code')
    address = forms.CharField(widget=forms.Textarea, required=False, label='Address')
    phone = forms.CharField(max_length=20, label='Phone')
    email = forms.EmailField(label='School Email')
    
    admin_first_name = forms.CharField(max_length=150, label='Admin First Name')
    admin_last_name = forms.CharField(max_length=150, label='Admin Last Name')
    admin_email = forms.EmailField(label='Admin Email')
    admin_password = forms.CharField(widget=forms.PasswordInput, label='Admin Password', min_length=6)
    admin_password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirm Admin Password', min_length=6)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('admin_password')
        confirm = cleaned_data.get('admin_password_confirm')
        if password and confirm and password != confirm:
            raise forms.ValidationError('Admin passwords do not match.')
        return cleaned_data


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'phone', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'email']
    actions = ['create_school_with_admin']

    def create_school_with_admin(self, request, queryset):
        if 'create' in request.POST:
            form = CreateSchoolWithAdminForm(request.POST)
            if form.is_valid():
                school = School.objects.create(
                    name=form.cleaned_data['name'],
                    code=form.cleaned_data['code'],
                    address=form.cleaned_data['address'],
                    phone=form.cleaned_data['phone'],
                    email=form.cleaned_data['email'],
                )
                User.objects.create_user(
                    email=form.cleaned_data['admin_email'],
                    password=form.cleaned_data['admin_password'],
                    first_name=form.cleaned_data['admin_first_name'],
                    last_name=form.cleaned_data['admin_last_name'],
                    role='ADMIN',
                    school=school,
                    is_staff=True,
                    is_superuser=True,
                )
                messages.success(request, f'Successfully created school "{school.name}" with admin user.')
                return redirect(reverse('admin:tenants_school_changelist'))
        else:
            form = CreateSchoolWithAdminForm()

        return render(request, 'admin/create_school_with_admin.html', {
            'form': form,
            'title': 'Create School with Admin',
            'opts': self.model._meta,
        })
    create_school_with_admin.short_description = 'Create school with admin user and password'


@admin.register(SchoolSettings)
class SchoolSettingsAdmin(admin.ModelAdmin):
    list_display = ['school', 'academic_year', 'current_term', 'currency']
    list_filter = ['academic_year', 'current_term']
