from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.HomePageView,  name='home'),
    path('contact/', views.submit_contact_query, name='contact'),
    path('contact/', views.submit_contact_query, name='submit_contact_query'),
    
    
    path('login/', views.LoginPageView, name='LoginPageView'),  # This matches the name used in your redirect
    path('login/', views.LoginPageView, name='login'),  # This matches the name used in your redirect
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.create_tenant_profile, name='register'),


    path('properties/', views.property_list, name='property_list'),
    path('property/<int:property_id>/edit/', views.edit_property, name='edit_property'),

    path('properties/delete/<int:property_id>/', views.delete_property, name='delete_property'),
    path('properties/add/', views.add_property, name='add_property'),
    path('property/<int:property_id>/', views.property_detail, name='property_detail'),

    #Account Login
    path('accounts/login/', views.LoginPageView, name='accounts_login'),
    #path('accounts/login/', views.accounts_login, name='accounts_login'),

    # Landlord URLs
    path('add_property/', views.add_property, name='add_property'),
    #path('property_list/', views.property_list, name='property_list'),

    path('landlord/dashboard/', views.landlord_dashboard, name='landlord_dashboard'),
    path('landlord/send_reminder/<int:reminder_id>/', views.send_reminder, name='send_reminder'),
    path('tenant/<int:tenant_id>/send-reminder/', views.send_reminder, name='send_reminder'),
    #path('tenant/<int:tenant_id>/send-reminder/', send_reminder, name='send_reminder'),
    #path('landlord/send_reminder/<int:reminder_id>/', views.send_reminder, name='send_reminder'),
    
    
    path('manage-tenants/', views.manage_tenants, name='manage_tenants'),
    path('tenant/<int:tenant_id>/', views.tenant_detail, name='tenant_detail'),
    path('tenant/<int:tenant_id>/deactivate/', views.deactivate_tenant, name='deactivate_tenant'),
    path('tenant/<int:tenant_id>/activate/', views.activate_tenant, name='activate_tenant'),
    path('approve-deactivation/<int:tenant_id>/', views.approve_deactivation, name='approve_deactivation'),
    path('reject-deactivation/<int:tenant_id>/', views.reject_deactivation, name='reject_deactivation'),
    path('tenant/<int:tenant_id>/send-reminder/', views.send_reminder, name='send_reminder'),
    path('toggle-tenant-status/<int:tenant_id>/', views.toggle_tenant_status, name='toggle_tenant_status'),
    path('notification/mark-as-read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
    path('edit_announcement/<int:id>/', views.edit_announcement, name='edit_announcement'),
    path('delete_announcement/<int:id>/', views.delete_announcement, name='delete_announcement'),
    
    path('account/create/', views.create_landlord, name='create_landlord'),
    path('landlord/create/', views.create_initial_landlord, name='create_initial_landlord'),
    path('notification/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('accounts/create_admin/', views.create_initial_admin, name='create_initial_admin'),

    # Tenant URLs
    path('tenant/create_profile/', views.create_tenant_profile, name='create_tenant_profile'),
    path('tenant/register/', views.create_tenant_profile, name='tenant_register'),
    path('tenant/dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
    path('tenant/setup/', views.tenant_setup, name='tenant_setup'),
    
    path('tenant/request-property-change/', views.request_property_change, name='request_property_change'),
    path('tenant/profile/', views.tenant_profile, name='tenant_profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    
    #path('tenant/payment/<int:rent_id>/', views.make_payment, name='make_payment'),
    path('make_payment/', views.make_payment, name='make_payment'),
    
    path('tickets/', views.ticket_home, name='ticket_home'),
    path('chats/', views.chat_page, name='chat_page'),
    path('chats/<int:room_id>/', views.room_messages, name='room_messages'),
    
    path('chat/<int:room_id>/', views.chat_room_view, name='chat_room'),
    path('chat/create/', views.create_chat_room, name='create_chat_room'),
    path('chat/list/', views.chat_room_list, name='chat_room_list'),
    path('notifications/', views.notifications_view, name='notifications_view'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),

]


