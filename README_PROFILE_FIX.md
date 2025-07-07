# Correção do Erro "User has no profile"

## Problema
O erro `RelatedObjectDoesNotExist: User has no profile` ocorre quando um usuário não tem um Profile associado.

## Solução Implementada

### 1. Signals Automáticos
- Criado arquivo `alta/signals.py` que cria automaticamente um Profile quando um usuário é criado
- Registrado no `alta/apps.py` para ser carregado automaticamente

### 2. Tratamento nas Views
- Todas as views que acessam `request.user.profile` agora verificam se o Profile existe
- Se não existir, criam automaticamente um Profile vazio
- Se o usuário não tiver cidade configurada, redirecionam para a página de perfil

### 3. Comando de Gerenciamento
- Criado comando `create_missing_profiles` para criar Profiles para usuários existentes

## Como Usar

### Para Usuários Existentes (Sem Profile)
Execute o comando para criar Profiles para todos os usuários que não têm:

```bash
python manage.py create_missing_profiles
```

### Para Novos Usuários
O Profile será criado automaticamente quando um novo usuário se registrar.

### Para Usuários Sem Cidade Configurada
Se um usuário não tiver cidade configurada no Profile, será redirecionado para a página de perfil para configurar.

## Views Corrigidas
- `p_monitorar_produtos`
- `p_monitorar_concorrentes`
- `p_lista_preco`
- `add_price`

## Arquivos Modificados
- `alta/signals.py` (novo)
- `alta/apps.py` (modificado)
- `alta/views.py` (modificado)
- `alta/management/commands/create_missing_profiles.py` (novo)

## Status
✅ **Problema resolvido!** O sistema agora:
- Cria Profiles automaticamente para novos usuários
- Trata usuários existentes sem Profile
- Redireciona usuários sem cidade configurada
- Mantém compatibilidade com o código existente 