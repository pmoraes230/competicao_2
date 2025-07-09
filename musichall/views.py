from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import logout
import uuid
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io
from django.utils import timezone
from django.urls import reverse
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from functools import wraps
from . import models


# Create your views here.
def get_user_profile(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = models.Usuario.objects.select_related('id_perfil').get(id=user_id)
            return {
                'user_id': user.id,
                'user_name': user.nome,
                'user_imagem': user.imagem.url if user.imagem else None,
                'user_role': user.id_perfil.nome,
                'is_authenticated': True
            }
        except models.Usuario.DoesNotExist:
            return {'user_name': '', 'is_authenticated': False}
    return {'user_name': '', 'is_authenticated': False}

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_profile = get_user_profile(request)
            
            # Verifica se user_profile é válido e é um dicionário
            if not user_profile or not isinstance(user_profile, dict):
                messages.error(request, 'Erro ao verificar sua sessão. Faça login novamente.')
                return redirect(reverse('login'))
            
            # Verifica autenticação
            if not user_profile.get('is_authenticated', False):
                messages.error(request, 'Você precisa estar logado para acessar esta página.')
                return redirect(reverse('login'))
            
            user_role = user_profile.get('user_role')
            
            # Verifica se o papel está na lista de papéis permitidos
            if user_role not in roles:
                if user_role == 'Totem':
                    messages.info(request, 'Acesso restrito. Redirecionando para validação de ingresso.')
                    return redirect(reverse('validar_ingresso'))
                messages.error(request, 'Você não tem permissão para acessar esta página.')
                return redirect(reverse('home'))
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
            
def login(request):
    if request.method == 'GET':
        return render(request, 'login/login.html')
    
    username = request.POST.get('login')
    password = request.POST.get('senha')
    
    if not all([username, password]):
        messages.error(request, 'Preencha todos os campos.')
        return render(request, 'login/login.html')
    
    try:
        user = models.Usuario.objects.filter(cpf=username).first() or models.Usuario.objects.filter(email=username).first()
        if not user:
            messages.error(request, 'Usuário não encontrado.')
            return render(request, 'login/login.html')

        if check_password(password, user.senha):
            request.session['user_id'] = user.id
            request.session['user_name'] = user.nome
            request.session['user_role'] = user.id_perfil.nome
            
            messages.success(request, f'Bem-vindo, {user.nome}!')
            if user.id_perfil.nome == 'Totem':
                return redirect('validar_ingresso')
            return redirect('home')
        else:
            messages.error(request, 'Senha incorreta.')
            return render(request, 'login/login.html')
        
    except Exception as e:
        messages.error(request, f'Erro ao buscar usuário: {str(e)}')
        return render(request, 'login/login.html')
    
def logout_view(request):
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('login')

@role_required('Administrador', 'Staff', 'Vendedor')
def home(request):
    context = get_user_profile(request)  # Obtém o contexto do usuário autenticado
    
    name_user = request.session.get('user_name')
    id_user = request.session.get('user_id')
    imagem_user = request.session.get('user_imagem')
    
    # Adiciona informações do banco de dados ao contexto
    context.update({
        'events': models.Evento.objects.all().order_by('dataevento'),
        'perfil': models.Perfil.objects.all(),
        'user_name': name_user,
        'user_id': id_user,
        'image_user': imagem_user,
    })
    return render(request, 'home/home.html', context)

@role_required('Administrador')
def create_user(request):
    context = get_user_profile(request)  # Obtém o contexto do usuário autenticado
    
    if request.method == 'POST':
        name = request.POST.get('nome')
        email = request.POST.get('email')
        cpf = request.POST.get('cpfinput')
        profile_id = request.POST.get('perfil')
        image = request.POST.get('imagem')
        password = request.POST.get('senha')
        password_confirmation = request.POST.get('senha_confirmar')
        
        print(f"Received data: {name}, {email}, {cpf}, {profile_id}, {image}, {password}, {password_confirmation}")
        if not image:
            messages.error(request, 'Por favor, selecione uma imagem.')
            return redirect('create_user')
        
        if password != password_confirmation:
            messages.error(request, 'As senhas não coincidem.')
            return redirect('create_user')
        
        if len(password) < 4:
            messages.error(request, 'A senha deve ter mais de 4 caracteres ou mais.')
            return redirect('create_user')
        
        if models.Usuario.objects.filter(cpf=cpf).exists():
            messages.error(request, 'Já existe um usuário com este CPF.')
            return redirect('create_user')
        
        if models.Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Email já cadastrado')
            return redirect('create_user')
            
        if not name or not email or not cpf or not profile_id or not image or not password or not password_confirmation:
            messages.error(request, 'Preencha todos os campos obrigatórios.')
            return redirect('create_user')
        
        try:
            user = models.Usuario.objects.create(
                nome=name,
                email=email,
                cpf=cpf,
                id_perfil_id=profile_id,
                imagem=image,
                senha=make_password(password)  # Armazena a senha de forma segura
            )
            
            user.full_clean()  # Valida o usuário antes de salvar
            user.save()
            
            messages.success(request, 'Usuário criado com sucesso!')
            return redirect('create_user')
        except Exception as e:
            messages.error(request, f'Erro ao criar usuário: {str(e)}')
            return redirect('create_user')
            
    context.update({
        'perfis': models.Perfil.objects.all(),
        })
    
    return render(request, 'usuario/create_user.html', context)

@role_required('Administrador', 'Staff', 'Vendedor')
def edit_user(request, id):
    context = get_user_profile(request)
    
    try:
        user = models.Usuario.objects.get(id=id)
    except models.Usuario.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        return redirect('home')
    
    if request.method == 'POST':
        name = request.POST.get('nome')
        email = request.POST.get('email')
        cpf = request.POST.get('cpfinput')
        profile_id = request.POST.get('perfil')
        image = request.FILES.get('imagem')  # Captura o arquivo enviado
        password = request.POST.get('senha')
        password_confirmation = request.POST.get('senha_confirmar')
        
        if password:  # Só valida e atualiza a senha se o campo não estiver vazio
            if password != password_confirmation:
                messages.error(request, 'As senhas não coincidem.')
                return redirect('edit_user', id=id)
            
            if len(password) < 4:
                messages.error(request, 'A senha deve ter mais de 4 caracteres ou mais.')
                return redirect('edit_user', id=id)
            
            user.senha = make_password(password)  # Atualiza a senha apenas se fornecida
        
        # Atualiza os dados do usuário
        user.nome = name
        user.email = email
        user.cpf = cpf
        user.id_perfil_id = profile_id
        if image:
            user.imagem = image  # Atualiza a imagem apenas se uma nova for enviada
        user.senha = make_password(password)
        user.save()

        messages.success(request, 'Usuário atualizado com sucesso!')
        return redirect('home')
    
    context.update({
        'user': user,
        'perfis': models.Perfil.objects.all(),
        })
    return render(request, 'usuario/edit_user.html', context)

@role_required('Administrador')
def delete_user(request, id):
    try:
        user = models.Usuario.objects.get(id=id)
        if request.method == 'POST':
            user.delete()
            messages.success(request, 'Usuário deletado com sucesso!')
            return redirect('home')
        context = {
            'user': user,
            **get_user_profile(request)  # Obtém o contexto do usuário autenticado
        }
        return render(request, 'usuario/delete_user.html', context)
    except models.Usuario.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        return redirect('home')

@role_required('Administrador')
def create_profile(request):
    context = get_user_profile(request)
    
    if request.method == 'POST': 
        name = request.POST.get('nome')
        description = request.POST.get('descricao')
        
        if not all([name, description]):
            messages.error(request, 'Todos os campos são obrigatórios.')
            return redirect('create_profile')
        
        try:
            new_profile = models.Perfil.objects.create(
                nome=name,
                descricao=description
            )
            
            new_profile.full_clean()
            new_profile.save()
            
            messages.success(request, 'Perfil Salvo com sucesso!')
            return redirect('create_profile')
        except ValueError as ve:
            messages.error(request, f'Erro ao salvar perfil {str(ve)}')
            return redirect('create_profile')
    return render(request, 'perfil/create_perfil.html', context)

@role_required('Administrador')
def create_event(request):
    context = get_user_profile(request)
    
    if request.method == 'POST':
        name = request.POST.get('nome')
        date_event = request.POST.get('dataevento')
        hour_event = request.POST.get('datahorario')
        adress_event = request.POST.get('local')
        price_event = request.POST.get('price')
        image = request.POST.get('imagem')
        number_persons = request.POST.get('qtd_pessoas')
        
        if not all([name, date_event, hour_event, adress_event, image, number_persons, price_event]):
            messages.error(request, 'Todos os campos são obrigatórios.')
            return redirect('create_event')
        
        if models.Evento.objects.filter(dataevento=date_event, horario=hour_event, localevento=adress_event).exists():
            messages.error(request, 'Já existe um evento marcado para esta data, horário e local.')
            return redirect('create_event')
        
        try:
            user_id = request.session.get('user_id')
            if not user_id:
                messages.error(request, 'Usuário não autenticado.')
                return redirect('login')
            
            try:
                usuario = models.Usuario.objects.get(id=user_id)
            except models.Usuario.DoesNotExist:
                messages.error(request, 'Usuário não encontrado.')
                return redirect('login')
            
            new_event = models.Evento.objects.create(
                nome=name,
                dataevento=date_event,
                horario=hour_event,
                localevento=adress_event,
                preco_evento=price_event,
                imagem=image,
                capacidadepessoas=number_persons,
                id_user=usuario
            )
            
            new_event.full_clean()
            new_event.save()
            
            request.session['last_event_id'] = new_event.id
            messages.success(request, 'Evento cadastrado com sucesso.')
            return redirect('create_setor')
            
        except ValueError as e:
            messages.error(request, f'Erro ao salvar evento: {str(e)}')
            return redirect('create_event')
    
    return render(request, 'evento/create_event.html', context)

@role_required('Administrador')
def create_setor(request):
    context = get_user_profile(request)
    
    eventos = models.Evento.objects.all()
    context['eventos'] = eventos
    
    event_id = request.POST.get('event_id') or request.session.get('last_event_id')
    
    if request.method == 'POST':
        nome_setor = request.POST.getlist('nome[]')
        limit_tickets = request.POST.getlist('ticket[]')
        id_event = request.POST.get('event')
        
        if not id_event:
            messages.error(request, 'Por favor, selecione um evento antes de cadastrar o setor')
            return redirect('create_setor')
        
        if not all([nome_setor, limit_tickets]):
            messages.error(request, 'Pelo menos um setor deve ser preenchido.')
            return redirect('create_setor')
        
        try:
            evento = models.Evento.objects.get(id=id_event)
            total_existent_ticket = models.Setorevento.objects.filter(id_evento=id_event).aggregate(total=Sum('quantidade_setor'))['total'] or 0
            total_new_ticket = sum(int(ticket) for ticket in limit_tickets if ticket)
            
            if total_existent_ticket + total_new_ticket > evento.capacidadepessoas:
                messages.error(request, f'A soma das cadeiras ({total_existent_ticket + total_new_ticket}) excede o limite de pessoas no evento ({evento.capacidadepessoas}).')
                return redirect('create_setor')
            
            for nome, ticket in zip(nome_setor, limit_tickets):
                if nome and ticket:
                    setor = models.Setorevento.objects.create(
                        nome=nome,
                        quantidade_setor=int(ticket),
                        id_evento_id=id_event
                    )
                    setor.full_clean()
                    setor.save()
            
            messages.success(request, f'{len(nome_setor)} setor cadastrado com sucesso!.')
            return redirect('create_setor')
        except models.Evento.DoesNotExist:
            messages.error(request, 'Evento não encontrado.')
            return redirect('create_setor')
        except ValueError as e:
            messages.error(request, f'Erro ao salver setor: {str(e)}')
        
    
    if event_id:
        try:
            event = models.Evento.objects.get(id=event_id)
            context['event'] = event
            context['remaining_seats'] = max(0, event.capacidadepessoas - (models.Setorevento.objects.filter(id_evento_id=event_id).aggregate(total=Sum('quantidade_setor'))['total'] or 0))
        except models.Evento.DoesNotExist:
            if 'last_event_id' in request.session:
                del request.session['last_event_id']
            messages.error(request, 'Evento não encontrado.')
            return redirect('create_setor')
    
    return render(request, 'setor/create_setor.html', context)

@role_required('Administrador')
def register_client(request, id):
    context = get_user_profile(request)
    
    if request.method == 'POST':
        name_client = request.POST.get('nome')
        email_client = request.POST.get('email')
        cpf_client = request.POST.get('cpf')
        
        if not all([name_client, email_client, cpf_client]):
            messages.error(request, 'Todos os campos são obrigátorios.')
            return redirect(reverse('register_cliente', args=[id]))
        
        try:
            client = models.Cliente.objects.create(
                nome=name_client,
                email=email_client,
                cpf=cpf_client
            )
            client.full_clean()
            client.save()
            
            messages.success(request, 'Cliente cadastrado.')
            request.session['cliente_id'] = client.id
            return redirect(reverse('details_event', args=[id]))
        except ValueError as ve:
            messages.error(request, f'Erro ao salvar cliente: {str(ve)}')
            return redirect(reverse('register_cliente', args=[id]))
        
    context['event_id'] = id
    return render(request, 'cliente/create_client.html', context)

def event_details(request, id_event): 
    context = get_user_profile(request)
    try:
        event = models.Evento.objects.get(id=id_event)
        setores = models.Setorevento.objects.filter(id_evento_id=id_event)
        
        context.update({
            'event': event,
            'setores': setores,
        })
        
        client_id = request.session.get('cliente_id')
        if client_id:
            try:
                cliente = models.Cliente.objects.get(id=client_id)
                context['cliente'] = cliente
            except models.Cliente.DoesNotExist:
                del request.session['cliente_id']
                
        return render(request, 'evento/details_event.html', context)
        
    except models.Evento.DoesNotExist:
        messages.error(request, 'Evento não encontrado')

def buy_ticket(request, event_id):
    try:
        client_id = request.session.get('cliente_id')
        if not client_id:
            messages.info(request, 'Por favor, cadastre o cliente antes de comprar ingresso.')
            return redirect(reverse('register_cliente', args=[event_id]))

        client = models.Cliente.objects.get(id=client_id)
        event = models.Evento.objects.get(id=event_id)
        setores = models.Setorevento.objects.filter(id_evento_id=event_id)

        if request.method == 'POST':
            setor_id = request.POST.get('setor')
            amount = int(request.POST.get('quantidade', 1))

            if not setor_id:
                messages.error(request, 'Por favor, selecione um setor.')
                return redirect(reverse('buy_ticket', args=[event_id]))

            setor = models.Setorevento.objects.get(id=setor_id)

            if amount < 1:
                messages.error(request, 'A quantidade deve ser pelo menos 1.')
                return redirect(reverse('buy_ticket', args=[event_id]))
            
            if amount > 10:
                messages.error(request, 'Limite máximo de ingresso para ser comprado é 10')
                return redirect(reverse('buy_ticket', args=[event_id]))

            if setor.quantidade_setor < amount:
                messages.error(request, f'Apenas {setor.quantidade_setor} ingressos disponíveis para o setor {setor.nome}.')
                return redirect(reverse('buy_ticket', args=[event_id]))

            # Calcular o preço total com base no setor
            total_price = amount * (event.preco_evento or 0.00)  # Usar preço do setor
            venda = models.Venda.objects.create(
                id_evento=event,
                id_cliente=client,  
                datavenda=timezone.now(),  # Usar DateTime se alterar para DateTimeField
                valor=total_price
            )
            venda.full_clean()

            # Criar ingressos individuais
            ingressos = []
            for _ in range(amount):
                ingresso = models.Ingresso.objects.create(
                    id_ingresso=str(uuid.uuid4()),
                    id_evento=event,
                    id_cliente=client,
                    id_setor=setor,
                    id_venda=venda,
                    data_emissao=timezone.now(),
                    valor=event.preco_evento or 0.00,
                    status='emitido'
                )
                ingressos.append(ingresso)
                setor.quantidade_setor -= 1
                setor.save()

            messages.success(request, 'Compra realizada com sucesso! Ingressos emitidos.')
            return redirect(reverse('confirmacao_compra', args=[venda.id]))

        context = {
            'event': event,
            'setores': setores,
            'cliente': client,
            **get_user_profile(request)
        }
        return render(request, 'evento/details_event.html', context)

    except models.Evento.DoesNotExist:
        messages.error(request, 'Evento não encontrado.')
        return redirect('home')
    except models.Cliente.DoesNotExist:
        messages.error(request, 'Cliente não encontrado. Por favor, cadastre-se novamente.')
        return redirect(reverse('register_cliente', args=[event_id]))
    except models.Setorevento.DoesNotExist:
        messages.error(request, 'Setor não encontrado.')
        return redirect(reverse('buy_ticket', args=[event_id]))
    
def confirmacao_compra(request, venda_id):
    try:
        venda = models.Venda.objects.get(id=venda_id)
        ingressos = models.Ingresso.objects.filter(id_venda=venda)
        context = {
            'venda': venda,
            'ingressos': ingressos,
            'event': venda.id_evento,
            'cliente': venda.id_cliente,
            **get_user_profile(request)
        }
        return render(request, 'evento/confirmacao_compra.html', context)
    except models.Venda.DoesNotExist:
        messages.error(request, 'Venda não encontrada.')
        return redirect('home')
    
def gerar_ingresso_pdf(request, venda_id):
    try:
        venda = models.Venda.objects.get(id=venda_id)
        ingressos = models.Ingresso.objects.filter(id_venda=venda)

        # Criar o buffer para o PDF
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        # Configurar o layout do PDF
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, 10 * inch, "Ingresso para Evento")
        c.setFont("Helvetica", 12)

        # Informações da venda
        c.drawString(1 * inch, 9.5 * inch, f"Venda ID: {venda.id}")
        c.drawString(1 * inch, 9.2 * inch, f"Evento: {venda.id_evento.nome}")
        c.drawString(1 * inch, 8.9 * inch, f"Cliente: {venda.id_cliente.nome}")
        c.drawString(1 * inch, 8.6 * inch, f"Data da Venda: {venda.datavenda.strftime('%d/%m/%Y')}")
        c.drawString(1 * inch, 8.3 * inch, f"Valor Total: R$ {venda.valor:.2f}")

        # Listar ingressos
        y_position = 7.8 * inch
        c.drawString(1 * inch, y_position, "Ingressos:")
        c.line(1 * inch, y_position - 0.1 * inch, 7.5 * inch, y_position - 0.1 * inch)

        y_position -= 0.4 * inch
        for index, ingresso in enumerate(ingressos):
            if index > 0:
                c.line(1 * inch, y_position, 7.5 * inch, y_position)
            c.drawString(1 * inch, y_position, f"Ingresso ID: {ingresso.id_ingresso}")
            c.drawString(1 * inch, y_position - 0.2 * inch, f"Setor: {ingresso.id_setor.nome}")
            c.drawString(1 * inch, y_position - 0.4 * inch, f"Valor: R$ {ingresso.valor:.2f}")
            c.drawString(1 * inch, y_position - 0.6 * inch, f"Data de Emissão: {ingresso.data_emissao.strftime('%d/%m/%Y %H:%M')}")
            y_position -= 1.0 * inch

        # Finalizar o PDF
        c.showPage()
        c.save()

        # Preparar o e-mail
        subject = f'Confirmação de Compra - Ingresso Venda {venda.id}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [venda.id_cliente.email]  # Supondo que o modelo Cliente tenha um campo 'email'

        # Renderizar o template HTML
        html_content = render_to_string('email/email_ingresso.html', {
            'venda': venda,
            'ingressos': ingressos,
        })
        # Criar versão em texto puro (removendo tags HTML)
        text_content = strip_tags(html_content)

        # Criar o e-mail com EmailMultiAlternatives
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,  # Corpo em texto puro
            from_email=from_email,
            to=to_email,
        )
        email.attach_alternative(html_content, "text/html")  # Anexar versão HTML

        # Anexar o PDF
        buffer.seek(0)
        email.attach(f'ingresso_venda_{venda.id}.pdf', buffer.getvalue(), 'application/pdf')

        # Enviar o e-mail
        print("enviado")
        email.send()

        # Enviar o PDF como resposta para download
        buffer.seek(0)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ingresso_venda_{venda.id}.pdf"'
        response.write(buffer.getvalue())
        buffer.close()
        return response

    except models.Venda.DoesNotExist:
        messages.error(request, 'Venda não encontrada.')
        return redirect('home')
    except Exception as e:
        messages.error(request, f'Erro ao enviar o e-mail: {str(e)}')
        return redirect('home')

@role_required('Administrador')
def list_setores(request):
    context = get_user_profile(request)
    setor = models.Setorevento.objects.all()
    
    context['setores'] = setor
    return render(request, 'setor/list_setor.html', context)

@role_required('Administrador')
def update_setor(request, id):
    context = get_user_profile(request)
    
    try:
        setor = models.Setorevento.objects.get(id=id)
    except models.Setorevento.DoesNotExist:
        messages.error(request, 'Setor não encontrado.')
        return redirect('list_setor')
    
    if request.method == 'POST':
        nome_setor = request.POST.get('nome')
        limit_ticket = request.POST.get('ticket')
    
        if not all([nome_setor, limit_ticket]):
            messages.error(request, 'Todos os campos são obrigatórios.')
            return redirect('update_setor', id=id)
        
        try:
            setor.nome = nome_setor
            setor.quantidade_setor = int(limit_ticket)
            setor.full_clean()
            setor.save()
            
            messages.success(request, 'Setor atualizado com sucesso!')
            return redirect('update_setor', id=id)
        except ValueError as e:
            messages.error(request, f'Erro ao atualizar setor: {str(e)}')
            return redirect('update_setor', id=id)
    
    context.update({
        'setor': setor,
        'event': setor.id_evento,
    })
            
    return render(request, 'setor/edit_setor.html', context)

@role_required('Administrador')
def delete_setor(request, id):
    try:
        setor = models.Setorevento.objects.get(id=id)
        if request.method == 'POST':
            setor.delete()
            messages.success(request, 'Setor apagado com sucesso.')
            return redirect('list_setor')
        context = {
            'setor': setor,
            **get_user_profile(request)
        }
        return render(request, 'setor/delete_setor.html', context)
    except models.Setorevento.DoesNotExist:
        messages.error(request, 'Setor não encontrado.')
        return redirect('list_setor')

@role_required('Administrador')
def list_users(request):
    context = get_user_profile(request)

    context.update({
        'users': models.Usuario.objects.all()
    })
    
    return render(request, 'usuario/list_usuario.html', context)
    