from django.urls import path
from . import views

urlpatterns = [
    path('dash_home/', views.home_dash, name='dash_musichall'),
    path('dash_vendas/', views.dash_venda, name='dash_vendas'),
    path('dash_usuarios/', views.dash_usuario, name='dash_usuario'),
    path('dash_evento/', views.dash_evento, name='dash_evento')
]
