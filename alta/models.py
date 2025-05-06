from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.utils import timezone


class Produto(models.Model):
    produto = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='Produto')
    codigo_anp = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='Código do Produto')
    nome_pesquisa_anp = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='Nome Pesquisa ANP')

    def __str__(self):
        return self.produto


class GasStation(models.Model):
    cnpj = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='CNPJ', db_index=True)
    razao = models.CharField(default=None, null=True, blank=True, max_length=500, verbose_name='Razão Social', db_index=True)
    fantasia = models.CharField(default=None, null=True, blank=True, max_length=500, verbose_name='Fantasia', db_index=True)
    endereco = models.CharField(default=None, null=True, blank=True, max_length=150, verbose_name='Endereço', db_index=True)
    estado = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='Estado', db_index=True )
    cidade = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='Cidade', db_index=True)
    bairro = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='Bairro', db_index=True)
    numero = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='Número', db_index=True)
    cep = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='CEP', db_index=True)
    complemento = models.CharField(default=None, null=True, blank=True, max_length=500, verbose_name='Complemento', db_index=True)
    bandeira = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='Bandeira')
    data_bandeira = models.DateField(default=date(2025, 1, 1), null=True, blank=True, verbose_name='Atualização na bandeira')
    data_autorizacao = models.DateField(default=date(2025, 1, 1), null=True, blank=True, verbose_name='Data da autorização')
    nr_autorizacao = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='NR autorização')
    codigo_simp = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='Código SIMP')

    def __str__(self):
        return self.razao

    class Meta:
        indexes = [
            models.Index(fields=['cnpj']),
            models.Index(fields=['razao']),
            models.Index(fields=['estado']),
            models.Index(fields=['cidade']),
            models.Index(fields=['bairro']),
            models.Index(fields=['endereco']),
            models.Index(fields=['complemento']),
            models.Index(fields=['cep']),
            models.Index(fields=['bandeira']),
        ]


class PesquisaOrigem(models.Model):
    origem = models.CharField(max_length=100, null=True, blank=True, default=None, verbose_name='Origem da pesquisa')

    def __str__(self):
        return self.origem
    

class AddPrice(models.Model):
    data_coleta = models.DateField(default=timezone.now, verbose_name='Data do Registro')    
    cnpj = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='CNPJ', db_index=True)
    gasstation_id = models.ForeignKey(GasStation, on_delete=models.CASCADE, default=None, null=True, blank=True, verbose_name='Lista de Postos', db_index=True)
    produto = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='Produto', db_index=True)
    produto_id = models.ForeignKey(Produto, on_delete=models.CASCADE, default=None, null=True, blank=True, verbose_name='Produto ID', db_index=True)
    pesquisa_origem = models.ForeignKey(PesquisaOrigem, on_delete=models.CASCADE, default=None, null=True, blank=True, verbose_name='Origem da pesquisa', db_index=True)
    unidade_medida = models.CharField(max_length=50, null=True, blank=True, default=None, verbose_name='Unidade de medida')
    preco_revenda = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='Preço de venda', db_index=True)
    preco_compra = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Preço de compra', db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True, blank=True, verbose_name='Usuário', db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['data_coleta']),
            models.Index(fields=['gasstation_id']),
            models.Index(fields=['produto_id']),
            models.Index(fields=['preco_revenda']),
            models.Index(fields=['preco_compra']),
            models.Index(fields=['user']),
            models.Index(fields=['data_coleta', 'produto_id']),  # Índice composto para consultas por data e produto
            models.Index(fields=['gasstation_id', 'data_coleta']),  # Índice composto para consultas por posto e data
            models.Index(fields=['produto_id', 'data_coleta', 'preco_revenda']),  # Índice composto para análises de preço
        ]
        ordering = ['-data_coleta']  # Ordenação padrão por data decrescente
    

class FAQ(models.Model):
    title = models.CharField(default=None, null=False, blank=False, max_length=100, verbose_name='Título')
    description = models.CharField(default=None, null=False, blank=False, max_length=500,verbose_name='Descrição')

    def __str__(self):
        return self.title
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Usuário')
    telefone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Telefone')
    empresa = models.CharField(max_length=100, null=True, blank=True, verbose_name='Empresa')
    cargo = models.CharField(max_length=100, null=True, blank=True, verbose_name='Cargo')
    cpf = models.CharField(max_length=100, null=True, blank=True, verbose_name='CPF')

    def __str__(self):
        return self.telefone
 
    
class Contato(models.Model):
    nome = models.CharField(default=None, null=False, blank=False, max_length=100, verbose_name='Nome')
    email = models.EmailField(max_length=254, default=None, null=False, blank=False, verbose_name="Email")
    telefone = models.CharField(default=None, null=False, blank=False, max_length=100, verbose_name='Telefone')
    assunto = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='Assunto')
    mensagem = models.TextField(max_length=254, default=None, null=True, blank=True, verbose_name='Mensagem')

    def __str__(self):
        return self.nome
    

class Estado(models.Model):
    estado = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='Estado', db_index=True)

    def __str__(self):
        return self.estado
    

class Cidade(models.Model):
    cidade = models.CharField(default=None, null=True, blank=True, max_length=100, verbose_name='Cidade', db_index=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, default=None, null=True, blank=True, verbose_name='Estado')

    def __str__(self):
        return self.cidade
    
    
