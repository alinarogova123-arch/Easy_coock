from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from recipes import views

urlpatterns = (
    [
        path('admin/', admin.site.urls),
        path('', views.index, name='home'),
        path('auth/', views.authentication, name='auth'),
        path('logout/', views.logout_user, name='logout'),
        path('registration/', views.registration, name='registration'),
        path('lk/', views.lk, name='lk'),
        path('order/', views.get_order, name='order'),
        path(
            'subscription/<int:subscription_id>/menu/',
            views.get_daily_menu,
            name='subscription_menu',
        ),
        path(
            'recipe/<int:recipe_id>/',
            views.recipe_detail,
            name='recipe',
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
