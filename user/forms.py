from django import forms 
from user.models import CustomUser
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django import forms
from .models import Address

class UserRegForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget = forms.PasswordInput)
    phone_number = forms.CharField(max_length=15)

    class Meta:
        model = CustomUser
        fields = ['first_name','last_name','username','email','phone_number']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email = email).exists():
            raise ValidationError("This email is already exist. please use another one")
        return email 
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise ValidationError("phone number must contain only digits.")
        if len(phone_number)<10:
            raise ValidationError("phone number must be at atleat 10 digits")
        return phone_number
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password',"Password and Confirm Password do not match.")

        return cleaned_data
    

# ------------------------------------------------------------------------------------------------------------------------------------------------------

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'street_address', 'apartment_suite', 'landmark', 'city', 'postal_code', 'phone_number', 'state', 'is_default']

