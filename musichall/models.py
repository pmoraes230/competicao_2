from django.db import models
import locale
from django.utils import timezone
import uuid

class Cliente(models.Model):
    nome = models.CharField(max_length=50)
    email = models.CharField(max_length=70)
    cpf = models.CharField(max_length=14)

    class Meta:
        managed = False
        db_table = 'cliente'
        
    def __str__(self):
        return self.nome


class Evento(models.Model):
    nome = models.CharField(max_length=50)
    dataevento = models.DateField(db_column='dataEvento')  # Field name made lowercase.
    horario = models.TimeField()
    localevento = models.CharField(db_column='localEvento', max_length=150)  # Field name made lowercase.
    imagem = models.ImageField(upload_to='')
    capacidadepessoas = models.IntegerField(db_column='capacidadePessoas')  # Field name made lowercase.
    preco_evento = models.DecimalField(db_column='preco_evento', max_digits=10, decimal_places=2)
    id_user = models.ForeignKey('Usuario', db_column='id_user', on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'evento'

    def __str__(self):
        return self.nome
    
    def formatted_day(self):
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')  # Set locale to Brazilian Portuguese
        return {
            'day': self.dataevento.strftime('%d'),
            'month': self.dataevento.strftime('%b').upper(),
        }


class Perfil(models.Model):
    nome = models.CharField(max_length=50, blank=True, null=True)
    descricao = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'perfil'
        
    def __str__(self):
        return self.nome


class Setorevento(models.Model):
    nome = models.CharField(max_length=50)
    quantidade_setor = models.CharField(max_length=80, blank=True, null=True)
    id_evento = models.ForeignKey('Evento', db_column='id_evento', on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'setorevento'
        
    def __str__(self):
        return self.nome


class Usuario(models.Model):
    nome = models.CharField(max_length=50)
    email = models.CharField(max_length=70)
    cpf = models.CharField(max_length=14)
    imagem = models.ImageField(upload_to='')
    senha = models.CharField(max_length=240)
    id_perfil = models.ForeignKey('perfil', db_column='id_perfil', on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'usuario'
        
    def __str__(self):
        return self.nome


class Venda(models.Model):
    id_evento = models.ForeignKey('Evento', db_column='id_evento', on_delete=models.CASCADE)
    id_cliente = models.ForeignKey('Cliente', db_column='id_cliente', on_delete=models.CASCADE)
    datavenda = models.DateField(db_column='dataVenda')  # Field name made lowercase.
    valor = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'venda'
        
    def __str__(self):
        return f'cliente: {self.id_cliente} - evento: {self.id_evento}'

class Ingresso(models.Model):
    id_ingresso = models.CharField(max_length=36, default=uuid.uuid4, unique=True, editable=False)
    id_evento = models.ForeignKey('Evento', db_column='id_evento', on_delete=models.CASCADE)
    id_cliente = models.ForeignKey('Cliente', db_column='id_cliente', on_delete=models.CASCADE, null=False)  # Adicionado null=True
    id_setor = models.ForeignKey('Setorevento', db_column='id_setor', on_delete=models.CASCADE)
    id_venda = models.ForeignKey('Venda', db_column='id_venda', on_delete=models.CASCADE, null=True)
    data_emissao = models.DateTimeField(default=timezone.now)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[('emitido', 'Emitido'), ('validado', 'Validado'), ('cancelado', 'Cancelado')],
        default='emitido'
    )

    class Meta:
        managed = False
        db_table = 'ingresso'

    def __str__(self):
        return f"Ingresso {self.id_ingresso} para {self.id_evento.nome} - {self.id_cliente.nome if self.id_cliente else 'Sem cliente'}"