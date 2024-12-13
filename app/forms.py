from datetime import timedelta
from django import forms
from app.models import *
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from datetime import timedelta

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        fields = ['username', 'password']


class RegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

class AddClientForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    class Meta:
        model = Client
        fields = '__all__'
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class AddBeneficiaryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    
    class Meta:
        model = Beneficiary
        fields = '__all__'
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class AddAssistanceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        client = cleaned_data.get('client')
        assistance_type = cleaned_data.get('assistance_type')

        if assistance_type in ['Education', 'Medical']:
            if not client:
                raise forms.ValidationError("Client information is required.")

            from django.db.models import Q

            now = timezone.now()
            current_month_assistance = Assistance.objects.filter(
                client=client,
                date_added__month=now.month,
                date_added__year=now.year,
            ).filter(
                Q(assistance_type='Medical') | Q(assistance_type='Education'),
            )

            three_months_period = timedelta(days=90)
            three_months_ago = now.date() - three_months_period
            recent_assistance = Assistance.objects.filter(
                client=client,
                assistance_type=assistance_type,
                date_provided__gte=three_months_ago,
            )

            if recent_assistance.exists():
                raise forms.ValidationError(
                    f"{assistance_type} assistance has already been claimed within the last 3 months. "
                    "Please try again after the restriction period."
                )
            
            if current_month_assistance.exists():
                raise forms.ValidationError(
                    f"There is already assistance recorded made by the client and unable to request new assistance for {assistance_type}."
                )

        return cleaned_data

    class Meta:
        model = Assistance
        fields = '__all__'
        exclude = ['is_notified', 'is_claimed']
        widgets = {
            'amount': forms.TextInput(attrs={'type': 'number', 'readonly': 'true'}),
            'date_provided': forms.DateInput(attrs={'type': 'date'}),
        }

class AddNotificationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input','checked':'true'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()

        if NotificationSetting.objects.count() == 0:
            return cleaned_data
        
        if cleaned_data.get('is_primary_notification') == False:
            return cleaned_data
        
        if NotificationSetting.objects.filter(is_primary_notification=True).exists():
            raise forms.ValidationError(
                f"You can only have one primary notification template, please update the other notification."
            )

        return cleaned_data
    
    class Meta:
        model = NotificationSetting
        fields = '__all__'


class UpdateNotificationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        check_notifications_excluded = NotificationSetting.objects.exclude(notification_name=cleaned_data.get('notification_name')).filter(is_primary_notification=True).count()
        
        if check_notifications_excluded > 0:
            raise forms.ValidationError(
                f"You can only have one primary notification template, please update the other notification."
            )

        return cleaned_data
    
    class Meta:
        model = NotificationSetting
        fields = '__all__'


class AddUserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():

            field.widget.attrs.update({'class': 'form-control'})

            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active']
        widgets = {
            'date_joined': forms.DateTimeInput(attrs={'type': 'date'}),
            'password': forms.PasswordInput(attrs={'type': 'password'}),
        }

class UpdateUserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():

            field.widget.attrs.update({'class': 'form-control'})

            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active']

class UpdateAssistanceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
    
    class Meta:
        model = Assistance
        fields = '__all__'
        exclude = ['is_notified',]
        widgets = {
            'amount': forms.TextInput(attrs={'type': 'number','readonly':'true'}),
            'date_provided': forms.DateInput(attrs={'type': 'date'}),
        }


class UpdateBeneficiaryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    
    class Meta:
        model = Beneficiary
        fields = '__all__'
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class UpdateClientForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    class Meta:
        model = Client
        fields = '__all__'
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
