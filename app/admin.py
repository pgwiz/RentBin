from django.contrib import admin
from .models import User, Landlord, Tenant, Property, RentPayment, Announcement, Feedback, Reminder, TenantApprovalRequest, ChatRoom, Message
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'first_name', 'last_name', 'is_landlord', 'is_tenant', 'is_active', 'is_staff')
    search_fields = ('email',)
    ordering = ('email',)

admin.site.register(User, CustomUserAdmin)

@admin.register(Landlord)
class LandlordAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_status', 'registered_date')
    search_fields = ('user__username', 'user__email')

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_property', 'account_status')
    search_fields = ('user__username', 'user__email')

admin.site.register(Property)
admin.site.register(RentPayment)
admin.site.register(Announcement)
admin.site.register(Feedback)
admin.site.register(Reminder)
admin.site.register(TenantApprovalRequest)
admin.site.register(ChatRoom)
admin.site.register(Message)
