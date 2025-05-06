# Automação de Extração de Dados

Este diretório contém scripts para automatizar a extração de dados do arquivo `revendas_lpc_2025-04-20_2025-04-26` e salvá-los na tabela `addprice` do banco de dados PostgreSQL.

## Scripts

- `extract.py`: Script principal para extração e salvamento dos dados
- `run_extraction.py`: Script para executar a extração de forma automatizada
- `check_file.py`: Script para verificar o formato do arquivo antes da extração
- `extraction_log.log`: Arquivo de log com o histórico de execuções
- `file_check_log.log`: Arquivo de log com o histórico de verificações de arquivo

## Requisitos

- Python 3.6+
- Django
- Acesso ao PostgreSQL
- Usuário admin cadastrado no sistema

## Como Usar

### Execução Manual

Para executar a extração manualmente:

```bash
python run_extraction.py
```

O script irá:
1. Verificar o formato do arquivo
2. Registrar avisos sobre colunas ausentes ou extras
3. Executar a extração se o arquivo estiver em formato adequado
4. Registrar o progresso no arquivo de log

### Agendamento

#### Windows (Task Scheduler)

1. Abra o Agendador de Tarefas
2. Crie uma nova tarefa
3. Configure o trigger (ex: diariamente às 8h)
4. Ação: Iniciar um programa
5. Programa: `python`
6. Argumentos: `caminho/para/run_extraction.py`

#### Linux (cron)

Adicione ao crontab:

```bash
0 8 * * * cd /caminho/do/projeto && python automation/run_extraction.py
```

## Formato do Arquivo

O arquivo deve conter as seguintes colunas:

- cnpj
- razao_social
- fantasia
- endereco
- estado
- regiao
- cidade
- bairro
- numero
- cep
- complemento
- produto
- codigo_anp
- nome_pesquisa_anp
- preco_revenda
- preco_compra
- unidade_medida
- pesquisa_origem

O arquivo pode estar em formato CSV ou TSV.

## Logs

### Log de Extração (extraction_log.log)

Registra:
- Início e fim da extração
- Progresso (a cada 100 registros)
- Erros durante o processo
- Total de registros processados

### Log de Verificação (file_check_log.log)

Registra:
- Resultado da verificação do arquivo
- Colunas ausentes ou extras
- Tipo de arquivo detectado (CSV/TSV)
- Número total de linhas
- Amostra dos primeiros registros

## Solução de Problemas

### Erros Comuns

1. **Usuário admin não encontrado**
   - Verifique se existe um usuário admin no sistema
   - Crie um usuário admin se necessário

2. **Arquivo não encontrado**
   - Verifique se o arquivo está no diretório correto
   - Verifique se o nome do arquivo está correto

3. **Erro na conversão de preços**
   - Verifique se os valores estão em formato numérico válido
   - Verifique se os separadores decimais estão corretos

4. **Colunas ausentes**
   - Verifique se todas as colunas necessárias estão presentes
   - Verifique se os nomes das colunas estão corretos

### Verificação do Arquivo

Antes de executar a extração, o script verifica:
- Existência do arquivo
- Formato do arquivo (CSV/TSV)
- Presença de todas as colunas necessárias
- Formato dos dados nas primeiras linhas

Se houver problemas, o script registrará avisos no log e poderá interromper a execução. 