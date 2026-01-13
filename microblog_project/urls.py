from django.urls import path
from . import views

urlpatterns = [
    # ... other URL patterns ...
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)