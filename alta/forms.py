from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.core.cache import cache

from .models import (
    AddPrice, 
    Contato, 
    Profile,
    Estado,
    Cidade,
    Lead,
)


class CreateUserForm(UserCreationForm):
    # Campos do Profile
    telefone = forms.CharField(max_length=20, required=False)
    empresa = forms.CharField(max_length=100, required=False)
    cargo = forms.CharField(max_length=50, required=False)
    cpf = forms.CharField(max_length=100, required=False)
    
    # Campos do GasStation
    cidade = forms.ModelChoiceField(queryset=Cidade.objects.all(), required=False)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2',
        ]

    def clean(self):
        cleaned_data = super().clean()
        cidade = cleaned_data.get('cidade')
        
        # Se uma cidade foi selecionada, automaticamente define o estado correspondente
        if cidade:
            # Busca o estado relacionado à cidade através da ForeignKey
            estado_relacionado = cidade.estado
            if estado_relacionado:
                # Armazena o estado internamente para uso no método save()
                self.estado_automatico = estado_relacionado
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # O signal já cria o Profile automaticamente, então apenas atualizamos os dados
            try:
                profile = user.profile
                profile.telefone = self.cleaned_data.get('telefone')
                profile.empresa = self.cleaned_data.get('empresa')
                profile.cargo = self.cleaned_data.get('cargo')
                profile.cpf = self.cleaned_data.get('cpf')
                profile.cidade = self.cleaned_data.get('cidade')
                # Usa o estado automático se disponível, senão usa o estado do formulário (se existir)
                profile.estado = getattr(self, 'estado_automatico', None) or self.cleaned_data.get('estado')
                profile.save()
            except Profile.DoesNotExist:
                # Fallback caso o signal não tenha funcionado
                Profile.objects.create(
                    user=user,
                    telefone=self.cleaned_data.get('telefone'),
                    empresa=self.cleaned_data.get('empresa'),
                    cargo=self.cleaned_data.get('cargo'),
                    cpf=self.cleaned_data.get('cpf'),
                    cidade=self.cleaned_data.get('cidade'),
                    estado=getattr(self, 'estado_automatico', None) or self.cleaned_data.get('estado')
                )
        return user


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
        ]



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


class NewLeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['nome', 'telefone']
