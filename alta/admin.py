from django.contrib import admin

from .models import ( 
    Produto, 
    GasStation, 
    AddPrice, 
    PesquisaOrigem, 
    FAQ, 
    Profile, 
    Contato,
    Cidade,
    Estado,
    Lead
    )

class AddPriceAdmin(admin.ModelAdmin):
    list_display = ('gasstation_id', 'produto_id', 'preco_revenda', 'data_coleta')
    list_filter = ('gasstation_id', 'produto_id')
    search_fields = ('gasstation_id__razao', 'produto_id__produto')


class LeadAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'data_cadastro_formatada')
    list_filter = ('data_cadastro',)
    search_fields = ('nome', 'telefone')
    readonly_fields = ('data_cadastro',)

    def data_cadastro_formatada(self, obj):
        return obj.data_cadastro.strftime('%d/%m/%Y %H:%M')
    data_cadastro_formatada.short_description = 'Data de Cadastro'
    

admin.site.register(Lead, LeadAdmin)
admin.site.register(AddPrice, AddPriceAdmin)
admin.site.register(Produto)
admin.site.register(Cidade)
admin.site.register(Estado)
admin.site.register(GasStation)
admin.site.register(PesquisaOrigem)
admin.site.register(FAQ)
admin.site.register(Profile)
admin.site.register(Contato)

