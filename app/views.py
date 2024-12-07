from django.db.models.functions import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, DeactivationRequest, ContactQuery, Landlord, Tenant, Property, Announcement, RentPayment, Feedback, Reminder, ChatRoom, Message, Notification, Ticket , TenantApprovalRequest
from django.http import HttpResponse
from django.utils import timezone
import datetime
from decimal import Decimal
from datetime import timedelta
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.contrib import messages


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
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if hasattr(user, 'is_landlord') and user.is_landlord:
                return redirect('landlord_dashboard')
            elif hasattr(user, 'is_tenant') and user.is_tenant:
                return redirect('tenant_dashboard')
            else:
                return redirect('home')
        else:
            print(f"Authentication failed for username: {username}")
            messages.error(request, "Invalid username or password.")
            return render(request, 'app/login.html')

    return render(request, "app/login.html")
    

def logout_view(request):
    logout(request)
    return redirect('index')  # Ensure this matches the name defined in urls.py

def RegisterPageView(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            Notification.objects.create(message="A new Has signedup.")
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
    
    print("am setup", user.email)
    if Tenant.objects.filter(address=request.user.email).exists():
        return redirect('tenant_dashboard')
        
    if request.method == 'POST':
        form = TenantSetupForm(request.POST, request.FILES)
        if form.is_valid():
            tenant = form.save(commit=False)
            tenant.user = user
            tenant.rent_amount = tenant.current_property.rent  # Set rent from selected property
            tenant.registered_date = timezone.now()
            tenant.lease_end_date = timezone.now() + timedelta(days=3)
            tenant.lease_start_date = timezone.now() + timedelta(days=2)
            notif = f"{tenant.user} - finished setting up their account"
            Notification.objects.create(message=notif)
            tenant.account_status = 'active'
            tenant.save()
            return redirect('tenant_dashboard')  # Redirect after successful setup
    else:
        form = TenantSetupForm()

    return render(request, 'app/tenant/tenant_setup.html', {'form': form})
        
        

@login_required
def landlord_dashboard(request):
    user = request.user

    if not user.is_landlord:
        return redirect('accounts_login')  # Redirect non-landlords to login

    # Fetch landlord instance
    landlord = get_object_or_404(Landlord, user=user)

    # Existing queries
    properties = landlord.properties.all()
    announcements = Announcement.objects.filter(landlord__user=user)
    rent_payments = RentPayment.objects.filter(property__landlord__user=user)
    
    tenants = User.objects.filter(is_tenant=True).exclude(is_landlord=True)
    
    
    pending_requests = TenantApprovalRequest.objects.filter(landlord__user=user, status='Pending')
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    notifications_count = notifications.count()
    
    tenants_tabl = Tenant.objects.filter(account_status="Active")  # Fetch only active tenants
    
    reminders = []
    for tenant in tenants_tabl:
        if tenant.lease_end_date and tenant.rent_amount > 0:
            reminder_message = f"Dear {tenant.user.username}, you are required to catch up on your rent of {tenant.rent_amount} which is due on {tenant.lease_end_date}."
            reminders.append({
               # 'test_id':tenant.user,
                'tenant': tenant,
                'message': reminder_message,
                'due_date': tenant.lease_end_date,
            })
    for reminder in reminders:
        print(f"Tenant ID: {reminder['tenant'].user.id if reminder['tenant'] else 'No tenant'}")
    # Handle announcement form submission
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

    # Context for rendering
    context = {
        'notifications': notifications,
        'notifications_count': notifications_count,
        'landlord': landlord,
        'properties': properties,
        'announcements': announcements,
        'rent_payments': rent_payments,
        'tenants': tenants,
        'pending_requests': pending_requests,
        'form': form,
        'reminders': reminders,
    }

    return render(request, 'app/landlord/lan_dashboard.html', context)

@login_required
def send_reminder(request, reminder_id):
    user = request.user
    if not user.is_landlord:
        return redirect('accounts_login')

    reminder = get_object_or_404(Reminder, id=reminder_id)

    # Send the notification to the tenant
    notification_message = f"Reminder: {reminder.message}"
    Notification.objects.create(
        user=reminder.tenant.user,
        message=notification_message
    )

    messages.success(request, f"Reminder sent to {reminder.tenant.username}.")
    return redirect('landlord_dashboard')

@login_required
def edit_profile(request):
    tenant = request.user.tenant 
    
    if request.method == 'POST':
        tenant.phone_number = request.POST.get('phone_number', tenant.phone_number)
        tenant.address = request.POST.get('address', tenant.address)
        tenant.save()
        return redirect('tenant_profile')  
        
    return render(request, 'app/tenant/edit_profile.html', {'tenant': tenant})

@login_required
def edit_announcement(request, id):
    announcement = get_object_or_404(Announcement, id=id)
    if request.user != announcement.landlord.user:
        messages.error(request, "You do not have permission to edit this announcement.")
        return redirect('landlord_dashboard')

    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "Announcement updated successfully!")
            return redirect('landlord_dashboard')
    else:
        form = AnnouncementForm(instance=announcement)

    return render(request, 'app/landlord/edit_announcement.html', {'form': form})

@login_required
def delete_announcement(request, id):
    announcement = get_object_or_404(Announcement, id=id)
    if request.user != announcement.landlord.user:
        messages.error(request, "You do not have permission to delete this announcement.")
        return redirect('landlord_dashboard')

    announcement.delete()
    messages.success(request, "Announcement deleted successfully!")
    return redirect('landlord_dashboard')

@login_required
def toggle_tenant_status(request, tenant_id):
    if not request.user.is_landlord:
        return redirect('home')

    tenant_user = get_object_or_404(User, id=tenant_id, is_tenant=True)
    tenant_user.is_active = not tenant_user.is_active
    tenant_user.save()
    
    messages.success(request, f"Tenant status updated to {'Active' if tenant_user.is_active else 'Inactive'}.")
    
    return redirect('landlord_dashboard')



def tenant_detail(request, tenant_id):
    print(f"Received tenant_id: {tenant_id}") 
    
    tenant = get_object_or_404(Tenant, user_id=tenant_id)
    context = {
        'tenant': tenant,
    }
    return render(request, 'app/landlord/tenant_detail.html', context)    
    
@login_required
def manage_tenants(request):
    if not request.user.is_landlord:
        return redirect('home')

    landlord = get_object_or_404(Landlord, user=request.user)
    tenants = Tenant.objects.filter(current_property__landlord=landlord)
    deactivation_requests = DeactivationRequest.objects.filter(
        user__tenant__current_property__landlord=landlord, status='pending'
    )

    context = {
        'tenants': tenants,
        'deactivation_requests': deactivation_requests,
    }

    return render(request, 'app/landlord/manage_tenants.html', context)


@login_required
def deactivate_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    tenant.account_status = 'inactive'
    tenant.save()
    messages.success(request, f'Tenant {tenant.user.get_full_name()} has been deactivated.')
    return redirect('manage_tenants')

@login_required
def activate_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    tenant.account_status = 'active'
    tenant.save()
    messages.success(request, f'Tenant {tenant.user.get_full_name()} has been activated.')
    return redirect('manage_tenants')


@login_required
def approve_deactivation(request, tenant_id):
    tenant = get_object_or_404(Tenant, user__id=tenant_id)
    user = tenant.user
    tenant.delete()
    user.is_active = False
    user.save()
    messages.success(request, f'Account for {user.get_full_name()} has been deactivated and tenant record deleted.')
    return redirect('manage_tenants')

@login_required
def reject_deactivation(request, tenant_id):
    
    print(f"Received tenant_id: {tenant_id}") 
    
    #user = User.objects.get(id=1)
    #print(user.tenants.all())  # This should show the associated tenant if it exists
    tenant = get_object_or_404(Tenant, user__id=tenant_id)
   # print(f"Received tenant_id: {tenant_id}") 
    tenant.account_status = 'inactive'
    tenant.save()
    messages.success(request, f'Deactivation request for {tenant.user.get_full_name()} has been rejected. Account set to inactive.')
    return redirect('manage_tenants')
    

@login_required
def send_reminder(request, tenant_id):
    if request.method == 'POST':
        message = request.POST.get('message')
        tenant = get_object_or_404(Tenant, user__id=tenant_id)
        landlord = request.user

        if not tenant.current_property:
            return JsonResponse({'status': 'error', 'message': 'Tenant does not have an active property.'})

       # if tenant.current_property.landlord != landlord:
       #     return JsonResponse({'status': 'error', 'message': 'Tenant is not associated with this landlord.'})

        lease_start_date = tenant.lease_start_date
        lease_end_date = tenant.lease_end_date

        if not lease_start_date or not lease_end_date:
            return JsonResponse({'status': 'error', 'message': 'Lease dates are not set for this tenant.'})

        reminder = Reminder(
            landlord=landlord,
            tenant=tenant,  # Assign the Tenant instance here
            property=tenant.current_property,
            due_date=lease_end_date,
            message=message
        )
        reminder.save()
        Notification.objects.create(user=tenant.user, message=message)

        return JsonResponse({'status': 'success', 'message': 'Reminder sent and logged successfully!'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method!'})        
        
        
        
@login_required
def tenant_dashboard(request):
    user = request.user
    print(user.email)
    tenant = user.tenant
    if not Tenant.objects.filter(address=request.user.email).exists():
        print("not exist")
        return redirect('tenant_setup')
    
    # dashboard logic
    current_property = tenant.current_property
    upcoming_rent = None

    if tenant.lease_end_date:
        days_remaining = (tenant.lease_end_date - timezone.now().date()).days
        if days_remaining < 14:
            upcoming_rent = {
                "due_date": tenant.lease_end_date,
                "amount": tenant.rent_amount,
                "days_remaining": days_remaining,
                "tenant_id": tenant.user_id,  # Include tenant ID for payment URL
                "payment_button": True,  # Show the payment button when due soon
            }

    announcements = Announcement.objects.filter(
        landlord=current_property.landlord if current_property else None
    )

    # Fetch available properties for change requests
    available_properties = (
        Property.objects.exclude(id=current_property.id) if current_property else Property.objects.all()
    )

    # Fetch notifications for the tenant
    notifications = Notification.objects.filter(user=user).order_by('-created_at')

    context = {
        'tenant': tenant,
        'current_property': current_property,
        'upcoming_rent': upcoming_rent,
        'announcements': announcements,
        'available_properties': available_properties,
        'notifications': notifications,  # Add notifications to context
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

    # Handle deactivation request form submission
    if request.method == "POST":
        reason = request.POST.get('reason')
        if reason:
            DeactivationRequest.objects.create(user=user, reason=reason)
            return redirect('tenant_profile')

    context = {'tenant': tenant}
    return render(request, 'app/tenant/tenant_profile.html', context)
    
    
@login_required
def request_property_change(request):
    if request.method == 'POST':
        property_id = request.POST.get('property_id')
        user = request.user

        # Ensure the tenant exists
        if not hasattr(user, 'tenant'):
            messages.error(request, "You do not have a tenant profile.")
            return redirect('tenant_dashboard')

        # Check if the property exists
        property_instance = get_object_or_404(Property, id=property_id)

        # Save the change request
        TenantApprovalRequest.objects.create(
            landlord=property_instance.landlord,
            tenant=user.tenant,
            property=property_instance,
            status='Pending'
        )
        messages.success(request, "Your property change request has been submitted.")
        return redirect('tenant_dashboard')
        

@login_required
def make_payment(request):
    tenant = request.user.tenant
    property = tenant.current_property
    rent_amount = tenant.rent_amount
    lease_end_date = tenant.lease_end_date

    property_rent = tenant.current_property.rent  # Rent amount for the current property

    # Check if there is any balance remaining to be paid
    if tenant.rent_amount <= 0:
        messages.info(request, "You have no pending rent payments.")
        return render(request, 'app/tenant/no_payments.html')

    if request.method == 'POST':
        # Get the payment details from the form
        payment_method = request.POST.get('payment_method')
        amount_paid = float(request.POST.get('amount_paid', 0))

        # Prevent excess payments
        if amount_paid > tenant.rent_amount:
            return JsonResponse({'success': False, 'message': "You cannot pay more than the outstanding balance."})

        # Add a new record to RentPayment table
        rent_payment = RentPayment.objects.create(
            tenant=tenant,
            property=tenant.current_property,
            amount=amount_paid,
            due_date=tenant.lease_end_date,  # Optional, depending on logic
            payment_date=timezone.now(),
            status='Paid'
        )

        # Update the existing record in Tenant table
        tenant.rent_amount = tenant.rent_amount - Decimal(amount_paid)

        # Calculate the lease extension based on payment
        lease_extension_days = int(30 * (Decimal(amount_paid) / property_rent))
        
        if tenant.lease_end_date and tenant.lease_end_date >= timezone.now().date():
            tenant.lease_end_date += timezone.timedelta(days=lease_extension_days)
        else:
            tenant.lease_start_date = timezone.now()
            tenant.lease_end_date = timezone.now() + timezone.timedelta(days=lease_extension_days)

        tenant.last_payment_date = rent_payment.payment_date
        tenant.payment_method= payment_method
        notif = f"{tenant.user} - payed {amount_paid} and have an outstanding of ksh. {tenant.rent_amount}"
        Notification.objects.create(message=notif)
        tenant.save()
        
        return JsonResponse({
            'success': True,
            'payment_method': payment_method,
            'amount_paid': amount_paid,
            'remaining_balance': tenant.rent_amount,
            'lease_end_date': tenant.lease_end_date.strftime('%Y-%m-%d'),
            'payment_date': rent_payment.payment_date.strftime('%Y-%m-%d %H:%M:%S'),
        })
    context = {
        'property': property,
        'lease_end_date': lease_end_date,
        'rent_amount': tenant.rent_amount,
    }
    return render(request, 'app/tenant/tenant_payment.html', {'rent_balance': tenant.rent_amount})   
        
def create_landlord(request):
    if request.method == 'POST':
        form = CreateLandlordForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # new  landlord login
            return redirect('landlord_dashboard')  # lan dashboard
    else:
        form = CreateLandlordForm()
    return render(request, 'app/landlord/create_landlord.html', {'form': form})

def accounts_login(request, username=None):
    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password) #auth login.. dash 

        if user is not None and isinstance(user, User):
            login(request, user)
            
            if user.is_landlord:
                response = redirect('landlord_dashboard')
            elif user.is_tenant:
                response = redirect('tenant_dashboard')
            else:
                response = redirect('home')
            if next_url:
                response = redirect(next_url)
            
            response.set_cookie('logged_in', 'true', max_age=3600)
            return response
        else:
            messages.error(request, "Invalid email or password. Please try again.")  # Error message

            return render(request, 'app/accounts/accounts_login.html')
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
            
            landlord = get_object_or_404(Landlord, user=request.user)
            
            property_instance = form.save(commit=False)
            property_instance.landlord = landlord
            property_instance.save()
            notif = f"{landlord} - added new property"
            Notification.objects.create(message=notif)
            messages.success(request, 'Property added successfully!')
            return redirect('property_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PropertyForm()
    
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
        notif = f" one of the properties has been deleted"
        Notification.objects.create(message=notif)
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
            
            user = User(
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name'),
                email=form.cleaned_data['email'],
                username=form.cleaned_data['email'],
                is_tenant=True,
                is_active=False,
                phone_number=form.cleaned_data['phone_number'],
            )
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            tenant = Tenant(
                user=user,
                phone_number=form.cleaned_data['phone_number'],
                profile_picture=form.cleaned_data.get('profile_picture'),
                date_of_birth=form.cleaned_data['date_of_birth'],
                emergency_contact=form.cleaned_data.get('emergency_contact'),
                account_status='inactive',
            )
            tenant.save()  
            messages.success(request, "Registration successful! Your account is pending approval.")
            return redirect('LoginPageView')  
            
        else:
            print("Form errors:", form.errors)
    else:

        form = TenantRegistrationForm()

    return render(request, 'app/register.html', {'form': form})
        
        
        
def ticket_home(request):
    if request.method == "POST":
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        Ticket.objects.create(user=request.user, subject=subject, message=message)
        return redirect('ticket_home')

    tickets = Ticket.objects.filter(user=request.user) if request.user.is_authenticated else []
    return render(request, 'app/ticket_home.html', {'tickets': tickets})


@login_required
def chat_page(request):
    user = request.user
    rooms = ChatRoom.objects.all()
    user_tickets = Ticket.objects.filter(user=user) if user.is_tenant else Ticket.objects.all()
    return render(request, 'app/chat_page.html', {
        'rooms': rooms,
        'user_tickets': user_tickets,
    })


@login_required
def room_messages(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    user = request.user
    
    if room.room_type == 'landlord':
        if user.is_tenant:
            messages = room.messages.filter(user=user).order_by('timestamp')
        else:
            messages = room.messages.all().order_by('timestamp')
    else:
        messages = room.messages.all().order_by('timestamp')

    if request.method == "POST":
        action = request.POST.get('action')
        if action == "delete" and not user.is_tenant:  # Landlord can delete
            message_id = request.POST.get('message_id')
            message = get_object_or_404(Message, id=message_id)
            message.delete()
        else:
            content = request.POST.get('message')
            if content:
                Message.objects.create(room=room, user=request.user, content=content)

        return redirect('room_messages', room_id=room.id)

    return render(request, 'app/room_messages.html', {
        'room': room,
        'messages': messages,
        'is_landlord': not user.is_tenant,
    })
    
    
@login_required
def chat_room_list(request):
    rooms = ChatRoom.objects.all()
    return render(request, 'app/chat_room_list.html', {'rooms': rooms})
        
        
@login_required
def chat_room_view(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)

    # Filter messages for this room
    messages = room.messages.order_by('timestamp')

    if request.method == 'POST':
        content = request.POST.get('message')
        if content:
            Message.objects.create(room=room, user=request.user, content=content)
        return redirect('chat_room', room_id=room.id)

    context = {
        'room': room,
        'messages': messages,
    }
    return render(request, 'app/chat_room.html', context)


@login_required
def create_chat_room(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        room_type = request.POST.get('room_type', 'community')
        if name:
            ChatRoom.objects.create(name=name, room_type=room_type)
            return redirect('chat_room_list')
            notif = f" New chatroom created"
            Notification.objects.create(message=notif)

    return render(request, 'app/create_chat_room.html')

@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    
    if request.user not in room.participants.all():
        return redirect('tenant_dashboard')  # Redirect if the user isn't a participant

    if request.method == 'POST':
        content = request.POST.get('message')
        if content:
            Message.objects.create(room=room, sender=request.user, content=content)
        return redirect('chat_room', room_id=room.id)

    messages = room.messages.order_by('timestamp')  # Display messages in chronological order
    return render(request, 'app/chat_room.html', {'room': room, 'messages': messages})
        
        
def submit_contact_query(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        subject = request.POST['subject']
        message = request.POST['message']
        
        
        ContactQuery.objects.create(name=name, email=email, subject=subject, message=message)
        notif = f"n_{name}_{email}- submited a notification"
        Notification.objects.create(message=notif)
        
        messages.success(request, "Your query has been submitted successfully!")
        return redirect('contact')
        
    return render(request, 'app/contact.html')
    
    
@login_required
def view_contact_queries(request):
    queries = ContactQuery.objects.all().order_by('-created_at')
    return render(request, 'app/landlord/contacts_view.html', {'queries': queries})
        
def get_notifications(request):
    notifications = Notification.objects.all().order_by('-created_at')
    return render(request, 'app/landlord/notification_base.html', {'notifications': notifications})
        
        

def notifications_view(request):
    
    # Fetch notifications for the logged-in user
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifications_count = notifications.filter(is_read=False).count()

    context = {
        'notifications': notifications,
        'notifications_count': notifications_count,
    }
    return render(request, 'app/landlord/notifications.html', context)

def mark_notification_read(request, notification_id):
    # Mark a specific notification as read
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications_view')        
    
    
@login_required
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))
    
    
@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))
    
    