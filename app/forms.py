from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Landlord, Tenant, RentPayment, Property, Announcement


class TenantSetupForm(forms.ModelForm):
    current_property = forms.ModelChoiceField(
        queryset=Property.objects.all(),
        empty_label="Select a property",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Property",
    )

    class Meta:
        model = Tenant
        fields = [
            'phone_number', 'profile_picture', 'date_of_birth',
            'emergency_contact', 'address', 'current_property', 'rental_history', 'notes'
        ]
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter emergency contact'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter address'
            }),
            'rental_history': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe your rental experience',
                'rows': 3
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Additional notes (optional)',
                'rows': 2
            }),
        }
        
            
class TenantRegistrationForm(UserCreationForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
    }))
    last_name = forms.CharField(widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your phone number'
    }))
    profile_picture = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={
        'class': 'form-control',
    }))
    date_of_birth = forms.DateField(widget=forms.SelectDateWidget(years=range(1900, 2025), attrs={
        'class': 'form-control'
    }))
    emergency_contact = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter an emergency contact'
    }))

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2', 'phone_number', 'profile_picture', 'date_of_birth', 'emergency_contact']

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content']

class TenantProfileForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = [
            'phone_number',
            'address',
            'profile_picture',
            'emergency_contact',
            'date_of_birth',
            'notes'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),  # Use date input widget for birth date
        }
class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['address', 'city', 'state', 'zip_code', 'rent', 'bedrooms', 'bathrooms', 'description']
        labels = {
            'address': 'Property Address',
            'city': 'City',
            'state': 'State',
            'zip_code': 'Zip Code',
            'rent': 'Monthly Rent (Ksh)',
            'bedrooms': 'Number of Bedrooms',
            'bathrooms': 'Number of Bathrooms',
            'description': 'Property Description',
        }
        widgets = {
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter property address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter city'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter state'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter zip code'
            }),
            'rent': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter monthly rent'
            }),
            'bedrooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter number of bedrooms'
            }),
            'bathrooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter number of bathrooms'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter property description'
            }),
        }


class RegistrationForm(UserCreationForm):
    USER_TYPE_CHOICES = (
        ('landlord', 'Landlord'),
        ('tenant', 'Tenant'),
    )
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, widget=forms.RadioSelect)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name', 'phone_number')  # Include email and phone number

class LandlordRegistrationForm(forms.ModelForm):
    # Add any landlord-specific fields here
    class Meta:
        model = Landlord
        fields = '__all__'  # Or specify the fields you want


class CreateLandlordForm(UserCreationForm):
    address = forms.CharField(max_length=255, required=True)
    profile_picture = forms.ImageField(required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    emergency_contact = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number', 'password1', 'password2']


class RentPaymentForm(forms.ModelForm):
    class Meta:
        model = RentPayment
        fields = ['amount', 'due_date', 'status']

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User  # Add this line
        fields = UserCreationForm.Meta.fields + ('email',)