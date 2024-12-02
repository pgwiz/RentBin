from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone
from django.db import models

from django.db import models


class User(AbstractUser):
    # Override the default email field to make it unique and set as the primary identifier for login
    email = models.EmailField(unique=True, db_index=True)

    # Fields to distinguish between landlords and tenants
    is_landlord = models.BooleanField(default=False)
    is_tenant = models.BooleanField(default=False)

    # Optional phone number field
    phone_number = models.CharField(max_length=20, blank=True)

    # Additional many-to-many relationships for groups and permissions (default in AbstractUser)
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
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    due_date = models.DateField()
    message = models.TextField(blank=True)

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

