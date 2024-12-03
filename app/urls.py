from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.HomePageView,  name='home'),
    path('contact/', views.ContactPageView, name='contact'),
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
    path('manage-tenants/', views.manage_tenants, name='manage_tenants'),
    path('toggle-tenant-status/<int:tenant_id>/', views.toggle_tenant_status, name='toggle_tenant_status'),

    path('account/create/', views.create_landlord, name='create_landlord'),
    path('landlord/create/', views.create_initial_landlord, name='create_initial_landlord'),
    path('accounts/create_admin/', views.create_initial_admin, name='create_initial_admin'),

    # Tenant URLs
    path('tenant/create_profile/', views.create_tenant_profile, name='create_tenant_profile'),
    path('tenant/register/', views.create_tenant_profile, name='tenant_register'),
    path('tenant/dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
    path('tenant/setup/', views.tenant_setup, name='tenant_setup'),
    
    path('tenant/request-property-change/', views.request_property_change, name='request_property_change'),
    path('tenant/profile/', views.tenant_profile, name='tenant_profile'),
    #path('tenant/payment/<int:rent_id>/', views.make_payment, name='make_payment'),
    path('make_payment/', views.make_payment, name='make_payment'),
    
]


