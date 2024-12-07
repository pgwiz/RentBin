from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now


class User(AbstractUser):
    email = models.EmailField(unique=True, db_index=True)

    # distinguish between landlords and tenants
    is_landlord = models.BooleanField(default=False)
    is_tenant = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='rentbin_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='rentbin_users_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    # String representation of the User model (usually email for better identification)
    def __str__(self):
        return self.email


class Landlord(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)  # Link to User
    account_status = models.CharField(max_length=20, choices=[('active', 'Active'), ('inactive', 'Inactive'), ('banned', 'Banned')], default='active')
    address = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    registered_date = models.DateTimeField(auto_now_add=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Landlord: {self.user.username}"

class Property(models.Model):
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE, default=1, related_name='properties')
    address = models.CharField(max_length=255, default='')
    city = models.CharField(max_length=100, default='')
    state = models.CharField(max_length=100, default='')
    zip_code = models.CharField(max_length=20, default='000')
    rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.address}, {self.city}, {self.state}"




class Tenant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Enter a valid phone number.")]
    )
    rent_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0.0)]
    )
    address = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    registered_date = models.DateTimeField(auto_now_add=True)
    account_status = models.CharField(max_length=20, choices=[('active', 'Active'), ('inactive', 'Inactive'), ('banned', 'Banned')], default='active')
    emergency_contact = models.CharField(max_length=15, blank=True)
    rental_history = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    current_property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    lease_start_date = models.DateField(null=True, blank=True)
    lease_end_date = models.DateField(null=True, blank=True)
    last_payment_date = models.DateField(null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=[('up-to-date', 'Up-to-date'), ('late', 'Late'), ('overdue', 'Overdue')], default='up-to-date')
    payment_method = models.CharField(max_length=50, blank=True)

    #def save(self, *args, **kwargs):
        #if not self.user.is_active:
            #raise ValidationError("User must be active to create a Tenant.")
        #super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
                    
class Announcement(models.Model):
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)

class RentPayment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="rent_payments")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="rent_payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=[('Pending', 'Pending'), ('Paid', 'Paid'), ('Late', 'Late')],
        default='Pending'
    )

    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status != 'Paid'

class Feedback(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    date_submitted = models.DateTimeField(auto_now_add=True)

class Reminder(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    landlord = models.ForeignKey(User, on_delete=models.CASCADE, related_name='landlord_reminders')
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    due_date = models.DateField()
    message = models.TextField()
    
    def __str__(self):
        return f"Reminder for {self.tenant} - Due: {self.due_date}"
        
        
class TenantApprovalRequest(models.Model):
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Pending'
    )

    def clean(self):
        if self.tenant.current_property != self.property:
            raise ValidationError("The tenant's current property does not match the specified property.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Tenant Approval Request"
        verbose_name_plural = "Tenant Approval Requests"
        
User = get_user_model()

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} ({self.get_status_display()})"


class ChatRoom(models.Model):
    ROOM_TYPE_CHOICES = [
        ('community', 'Community'),
        ('tenant', 'Tenant'),
        ('landlord', 'Landlord'),
    ]

    name = models.CharField(max_length=255)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPE_CHOICES, default='community')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return f"Message by {self.user.username} in {self.room.name}"
        
class DeactivationRequest(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    reason = models.TextField()
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )

    def __str__(self):
        return f"Deactivation Request for {self.user.username} - Status: {self.status}"   
        
class ContactQuery(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} by {self.name}"

def get_default_user():
    landlord = Landlord.objects.first()
    if landlord:
        return landlord.user.id
    return User.objects.get_or_create(
        username='lan_',
        defaults={
            'email': 'lan_@gmail.com',
            'is_landlord': True,
            'is_active': True,
        }
    )[0].id

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=get_default_user)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message