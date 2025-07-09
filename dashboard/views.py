from django.shortcuts import render
from musichall.views import get_user_profile
from musichall import models

# Create your views here.
def home_dash(request):
    context = get_user_profile(request)
    all_event = models.Evento.objects.count()
    all_user = models.Usuario.objects.count()
    all_sales = models.Venda.objects.count()
    
    atividade_recentes = models.Venda.objects.select_related('id_evento', 'id_cliente').order_by('-datavenda')[:6]
    atidades_formatadas = []
    for venda in atividade_recentes:
        atividade = {
            'data': venda.datavenda,
            'evento': venda.id_evento.nome,
            'descricao': f'Compra de ingresso para {venda.id_cliente.nome}',
            'usuario': venda.id_cliente
        }
        atidades_formatadas.append(atividade)
    
    context.update({
        'all_event': all_event,
        'all_user': all_user,
        'all_sales': all_sales,
        'atividades_recentes': atidades_formatadas
    })
    
    return render(request, 'home/dash_home.html', context)

def dash_venda(request):
    context = get_user_profile(request)
    vendas = models.Venda.objects.select_related('id_evento', 'id_cliente').order_by('-datavenda')
    context.update({
        'vendas': vendas,
        'total_vendas': vendas.count()
    })
    
    return render(request, 'dash_vendas/dash_vendas.html', context)

def dash_usuario(request):
    context = get_user_profile(request)
    usuario = models.Usuario.objects.all()
    context.update({
        'usuarios': usuario,
        'total_usuario': usuario.count()
    })
    
    return render(request, 'dash_usuarios/dash_usuarios.html', context)

def dash_evento(request):
    context = get_user_profile(request)
    evento = models.Evento.objects.all()
    context.update({
        'eventos': evento,
        'total_evento': evento.count()
    })
    
    return render(request, 'dash_evento/dash_evento.html', context)