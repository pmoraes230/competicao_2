from django.urls import path
from . import views

urlpatterns = [
    path('validador/', views.validar_ingresso, name='validar_ingresso')
]
