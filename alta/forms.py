from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.core.cache import cache

from .models import (
    AddPrice, 
    Contato, 
)


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 
                  'last_name', 
                  'username', 
                  'email', 
                  'password1', 
                  'password2',
                  ]


class ContatoForm(ModelForm):
    class Meta:
        model = Contato
        fields = ['nome', 
                  'email', 
                  'telefone', 
                  'assunto', 
                  'mensagem', 
                  ]


class NewPrice(forms.ModelForm):
    class Meta:
        model = AddPrice
        fields = [
            'gasstation_id',
            'produto_id',
            'preco_revenda',
            'data_coleta',
            'pesquisa_origem',
        ]
        widgets = {
            'gasstation_id': forms.Select(attrs={
                'class': 'form-select mb-3',
                'onchange': 'atualizarInfosPosto(this)'
            })
        }


class PriceForm(forms.ModelForm):
    class Meta:
        model = AddPrice
        fields = [
            'gasstation_id',
            'produto_id',
            'preco_revenda',
            ] 


class AddPriceForm(forms.ModelForm):
    class Meta:
        model = AddPrice
        fields = [
            'gasstation_id',
            'produto_id',
            'pesquisa_origem',
            'preco_revenda',
            'preco_compra',
            'unidade_medida',
            'user'
        ]
