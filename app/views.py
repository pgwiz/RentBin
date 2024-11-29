from django.db.models.functions import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, Landlord, Tenant, Property, Announcement, RentPayment, Feedback, Reminder, TenantApprovalRequest
from django.http import HttpResponse
from django.utils import timezone

from .forms import (
TenantSetupForm,
    AnnouncementForm,
    RegistrationForm,
    PropertyForm,
    TenantProfileForm,
    LandlordRegistrationForm,
    TenantRegistrationForm,
    CreateLandlordForm, CustomUserCreationForm,  # Import the new form
)
from django.contrib import messages

def HomePageView(request):
    announcements = Announcement.objects.all().order_by('-date_posted')  # Get announcements in descending order of date
    context = {
        'announcements': announcements,
    }
    return render(request, "app/index.html", context)

def ContactPageView(request):
    return render(request, "app/contact.html")

def LoginPageView(request):
    if request.method == 'POST':
        username = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_landlord:
                return redirect('landlord_dashboard')
            elif user.is_tenant:
                return redirect('tenant_dashboard')
            else:
                return redirect('home')
        else:
            return render(request, 'app/login.html', {'error': 'Invalid credentials'})

    return render(request, "app/login.html")


def logout_view(request):
    logout(request)
    return redirect('index')  # Ensure this matches the name defined in urls.py

def RegisterPageView(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if form.cleaned_data['user_type'] == 'landlord':
                Landlord.objects.create(user=user)
            elif form.cleaned_data['user_type'] == 'tenant':
                Tenant.objects.create(user=user)
            return redirect('LoginPageView')  # Redirect to login after registration
    else:
        form = RegistrationForm()
    return render(request, "app/register.html", {'form': form})

def logout_view(request):
    logout(request)
    return redirect('LoginPageView')



@login_required
def tenant_setup(request):
    user = request.user

    # Check if the user already has a tenant profile
    if hasattr(user, 'tenant'):
        return redirect('tenant_dashboard')  # Redirect to tenant dashboard if already set up

    if request.method == 'POST':
        form = TenantSetupForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a new Tenant instance and associate it with the logged-in user
            tenant = form.save(commit=False)
            tenant.user = user
            tenant.registered_date = timezone.now()  # Set registered date to current time
            tenant.account_status = 'active'  # Set initial status to active
            tenant.save()

            # Redirect to the tenant dashboard after successful setup
            return redirect('tenant_dashboard')
    else:
        form = TenantSetupForm()

    # Get available properties to display in the form
    properties = Property.objects.filter(landlord__user=user)

    context = {
        'form': form,
        'properties': properties,
    }
    return render(request, 'app/tenant/tenant_setup.html', context)

@login_required
def landlord_dashboard(request):
    user = request.user

    if not user.is_landlord:
        return redirect('accounts_login')  # Ensure this is the correct URL name for login

    landlord = get_object_or_404(Landlord, user=user)
    properties = landlord.properties.all()
    announcements = Announcement.objects.filter(landlord__user=user)
    rent_payments = RentPayment.objects.filter(property__landlord__user=user)
    tenants = Tenant.objects.filter(current_property__landlord__user=user)
    pending_requests = TenantApprovalRequest.objects.filter(landlord__user=user, status='Pending')

    tenants = User.objects.filter(is_tenant=True).exclude(is_landlord=True)

    context = {
        'landlord': landlord,
        'tenants': tenants,  # Pass the tenants to the template
    }

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.landlord = landlord
            announcement.save()
            messages.success(request, "Announcement posted successfully!")
            return redirect('landlord_dashboard')
    else:
        form = AnnouncementForm()

    context = {
        'landlord': landlord,
        'properties': properties,
        'announcements': announcements,
        'rent_payments': rent_payments,
        'tenants': tenants,
        'pending_requests': pending_requests,
        'form': form,
    }

    return render(request, 'app/landlord/lan_dashboard.html', context)

@login_required
def toggle_tenant_status(request, tenant_id):
    if not request.user.is_landlord:
        return redirect('home')  # Redirect non-landlord users

    # Get the tenant's user object
    tenant_user = get_object_or_404(User, id=tenant_id, is_tenant=True)

    # Toggle the is_active field
    tenant_user.is_active = not tenant_user.is_active
    tenant_user.save()

    # Optionally, add a success message
    messages.success(request, f"Tenant status updated to {'Active' if tenant_user.is_active else 'Inactive'}.")

    # Redirect back to the manage tenants page or wherever you need
    return redirect('landlord_dashboard')


@login_required
def manage_tenants(request):
    # Ensure the user is a landlord
    if not request.user.is_landlord:
        return redirect('home')  # Redirect non-landlord users to the homepage or another page

    # Fetch the landlord object
    landlord = get_object_or_404(Landlord, user=request.user)

    # Get all tenants associated with the landlord's properties
    tenants = Tenant.objects.filter(current_property__landlord=landlord)

    # Get pending deactivation requests (assuming there is a request model)
    deactivation_requests = TenantApprovalRequest.objects.filter(
        landlord=landlord,
        status='Pending'
    )

    context = {
        'tenants': tenants,
        'deactivation_requests': deactivation_requests,
    }

    return render(request, 'app/landlord/manage_tenants.html', context)



@login_required
def tenant_dashboard(request):
    user = request.user

    if not isinstance(user, User) or not user.is_tenant:
        return redirect('login')

    try:
        tenant = user.tenant
    except Tenant.DoesNotExist:
        return redirect('login')

    properties = tenant.current_property
    upcoming_rent = RentPayment.objects.filter(
        tenant=tenant,
        status='Pending',
        due_date__gte=datetime.date.today()
    )
    announcements = Announcement.objects.filter(
        landlord__property=properties
    )

    context = {
        'tenant': tenant,
        'properties': [properties] if properties else [],
        'upcoming_rent': upcoming_rent,
        'announcements': announcements,
    }
    return render(request, 'app/tenant/tenant_dashboard.html', context)

@login_required
def tenant_profile(request):
    user = request.user

    if not isinstance(user, User) or not user.is_tenant:
        return redirect('login')

    try:
        tenant = user.tenant
    except Tenant.DoesNotExist:
        return redirect('login')

    context = {'tenant': tenant}
    return render(request, 'app/tenant/tenant_profile.html', context)

@login_required
def make_payment(request, rent_id):
    rent = get_object_or_404(RentPayment, id=rent_id)
    # ... (payment processing logic) ...
    return render(request, 'app/tenant/tenant_payment.html', {'rent': rent})


def create_landlord(request):
    if request.method == 'POST':
        form = CreateLandlordForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log in the newly created landlord
            return redirect('landlord_dashboard')  # Redirect to landlord dashboard
    else:
        form = CreateLandlordForm()
    return render(request, 'app/landlord/create_landlord.html', {'form': form})

def accounts_login(request, username=None):
    # Check if the 'next' URL is provided (it will be in the GET parameters if the user is redirected to the login page)
    next_url = request.GET.get('next', '')  # Default to empty string if 'next' is not provided

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Attempt to authenticate the user using the provided credentials
        user = authenticate(request, username=username, password=password)

        if user is not None and isinstance(user, User):  # Ensure user is an instance of your custom User model
            # Successful login, log the user in and redirect
            login(request, user)

            # Redirect based on user type (Landlord or Tenant)
            if user.is_landlord:
                response = redirect('landlord_dashboard')
            elif user.is_tenant:
                response = redirect('tenant_dashboard')
            else:
                response = redirect('home')  # Default redirect if neither landlord nor tenant

            # If a 'next' URL was provided, redirect to that page after login
            if next_url:
                response = redirect(next_url)

            # Set a cookie to indicate the user is logged in
            response.set_cookie('logged_in', 'true', max_age=3600)  # Cookie expires in 1 hour
            return response
        else:
            # Invalid login credentials
            messages.error(request, "Invalid email or password. Please try again.")  # Error message

            return render(request, 'app/accounts/accounts_login.html')  # Rerender login page

    # If GET request, render the login page
    return render(request, 'app/accounts/accounts_login.html')

def create_initial_landlord(request):
    if request.method == 'POST':
        form = CreateLandlordForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_landlord = True
            user.save()

            landlord = Landlord.objects.create(user=user)

            landlord.address = form.cleaned_data.get('address')
            landlord.profile_picture = form.cleaned_data.get('profile_picture')
            landlord.date_of_birth = form.cleaned_data.get('date_of_birth')
            landlord.emergency_contact = form.cleaned_data.get('emergency_contact')
            landlord.save()

            login(request, user)

            return redirect('landlord_dashboard')
    else:
        form = CreateLandlordForm()
    return render(request, 'app/accounts/create_initial_landlord.html', {'form': form})


def create_initial_admin(request):
    form = CustomUserCreationForm()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.email = form.cleaned_data['email']
            user.save()
            login(request, user)
            return redirect('admin:index')
        else:
            form = CustomUserCreationForm()
    return render(request, 'app/accounts/create_initial_admin.html', {'form': form})



@login_required
def add_property(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            # Fetch the landlord associated with the logged-in user
            landlord = get_object_or_404(Landlord, user=request.user)

            # Save the form data, but don't commit to the database yet
            property_instance = form.save(commit=False)
            property_instance.landlord = landlord  # Associate the property with the landlord
            property_instance.save()  # Save the property instance

            messages.success(request, 'Property added successfully!')
            return redirect('property_list')  # Redirect to the property list
        else:
            # Handle form errors gracefully
            messages.error(request, 'Please correct the errors below.')
    else:
        # Instantiate a blank form for a GET request
        form = PropertyForm()

    # Render the add property template with the form
    return render(request, 'app/landlord/add_property.html', {'form': form})


@login_required
def property_list(request):
    if request.user.is_landlord:
        landlord = get_object_or_404(Landlord, user=request.user)
        properties = Property.objects.filter(landlord=landlord).select_related('landlord')
    else:
        properties = Property.objects.none()
    return render(request, 'app/landlord/property_list.html', {'properties': properties})


def edit_property(request, property_id):
    property_instance = get_object_or_404(Property, id=property_id)
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Property updated successfully!")
            return redirect('property_list')
    else:
        form = PropertyForm(instance=property_instance)

    return render(request, 'app/landlord/edit_property.html', {'form': form, 'property': property_instance})


def delete_property(request, property_id):
    property_instance = get_object_or_404(Property, id=property_id)
    if request.method == 'POST':
        property_instance.delete()
        messages.success(request, "Property deleted successfully!")
        return redirect('property_list')
    return render(request, 'app/landlord/delete_property.html', {'property': property_instance})

def property_detail(request, property_id):
    property_instance = get_object_or_404(Property, id=property_id)

    return render(request, 'app/landlord/property_detail.html', {'property': property_instance})


def create_tenant_profile(request):
    if request.method == 'POST':
        form = TenantRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create the User object and set the initial fields
            user = User(
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name'),
                email=form.cleaned_data['email'],
                username=form.cleaned_data['email'],  # Use the email as the username
                is_tenant=True,  # Set the user type as tenant
                is_active=False,  # Set account status as inactive
                phone_number=form.cleaned_data['phone_number'],
            )
            user.set_password(form.cleaned_data['password1'])  # Set and hash the password
            user.save()  # Save the user instance

            # Create the Tenant object and set its fields
            tenant = Tenant(
                user=user,
                phone_number=form.cleaned_data['phone_number'],
                profile_picture=form.cleaned_data.get('profile_picture'),
                date_of_birth=form.cleaned_data['date_of_birth'],
                emergency_contact=form.cleaned_data.get('emergency_contact'),
                account_status='inactive',  # Ensure status is set to 'inactive'
            )
            tenant.save()  # Save the tenant instance

            messages.success(request, "Registration successful! Your account is pending approval.")
            return redirect('LoginPageView')  # Redirect to the login page
        else:
            print("Form errors:", form.errors)
    else:

        form = TenantRegistrationForm()

    return render(request, 'app/register.html', {'form': form})