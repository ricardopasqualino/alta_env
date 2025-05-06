from django.contrib import admin
from django.urls import path

from alta.views import (
    index, 
    p_cartao_precos, 
    p_plans, 
    p_ia, 
    p_mapeei, 
    p_lista_preco,
    p_acompanhar
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('cartao-precos/', p_cartao_precos, name='p_cartao_precos'),
    path('planos/', p_plans, name='p_plans'),
    path('ia/', p_ia, name='p_ia'),
    path('mapeei/', p_mapeei, name='p_mapeei'),
    path('lista-preco/', p_lista_preco, name='p_lista_preco'),
    path('acompanhar/', p_acompanhar, name='p_acompanhar'),
]
