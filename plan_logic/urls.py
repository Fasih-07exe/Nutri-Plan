from django.urls import path
from .views import diet_plan_view, download_diet_plan,aboutus,swap_meal
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', diet_plan_view, name='diet'),
    path('download-diet-plan/', download_diet_plan, name='download_diet_plan'),
    path('aboutus/', aboutus, name='aboutus'),
    path('swap-meal/', swap_meal, name='swap_meal'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
