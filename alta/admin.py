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
    Estado
    )

class AddPriceAdmin(admin.ModelAdmin):
    list_display = ('gasstation_id', 'produto_id', 'preco_revenda', 'data_coleta')
    list_filter = ('gasstation_id', 'produto_id')
    search_fields = ('gasstation_id__razao', 'produto_id__produto')

admin.site.register(AddPrice, AddPriceAdmin)
admin.site.register(Produto)
admin.site.register(Cidade)
admin.site.register(Estado)
admin.site.register(GasStation)
admin.site.register(PesquisaOrigem)
admin.site.register(FAQ)
admin.site.register(Profile)
admin.site.register(Contato)

