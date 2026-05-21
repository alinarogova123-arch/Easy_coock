from django.contrib import admin
from django.urls import path
from recipes import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home' ),
    path('auth/', views.authentication, name='auth'),
    path('logout/', views.logout_user, name='logout'),
    path('registration/', views.registration, name='registration'),
    path('lk/', views.lk, name='lk'),
    path('card<int:card_num>/', views.get_card, name='card'),
    path('order/', views.get_order, name='order'),    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)\
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
