from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),
    path('create_user/', views.create_user, name='create_user'),
    path('edit_user/<int:id>/', views.edit_user, name='edit_user'),
    path('delete_user/<int:id>', views.delete_user, name='delete_user'),
    path('create_profile/', views.create_profile, name='create_profile'),
    path('create_event/', views.create_event, name='create_event'),
    path('details_event/<int:id_event>', views.event_details, name='details_event'),
    path('create_setor/', views.create_setor, name='create_setor'),
    path('list_setor/', views.list_setores, name='list_setor'),
    path('update_setor/<int:id>', views.update_setor, name='update_setor'),
    path('delete_setor/<int:id>', views.delete_setor, name='delete_setor')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
