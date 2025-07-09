from django.shortcuts import render,redirect
from django.contrib import messages
from musichall.views import role_required, get_user_profile
from musichall import models

# Create your views here.
def validar_ingresso(request):
    context = get_user_profile(request)
    if request.method == "POST":
        ingresso_id = request.POST.get('ingresso_id')
        if not ingresso_id:
            messages.error(request, 'Por favor, insira o id do ingresso.')
            return redirect('validar_ingresso')
        
        try:
            ingresso = models.Ingresso.objects.get(id_ingresso=ingresso_id)
            if ingresso.status == 'validado':
                messages.error(request, 'Este ingresso já foi validado.')
                return redirect('validar_ingresso')
            elif ingresso.status == 'cancelado':
                messages.error(request, 'Este ingresso foi cancelado.')
                return redirect('validar_ingresso')
            elif ingresso.status == 'emitido':
                ingresso.status = 'validado'
                ingresso.save()
                messages.error(request, f'Ingresso de {ingresso.id_cliente.nome} validado com sucesso para o show {ingresso.id_evento.nome}.')
            else:
                messages.error(request, 'Status do ingresso inválido.')
        except models.Ingresso.DoesNotExist:
            messages.error(request, 'Ingresso não encontrado')
            return redirect('validar_ingresso')
        
    return render(request, 'validador/validador.html', context)