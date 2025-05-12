import os
import django
import datetime
import sys
import pandas as pd
from decimal import Decimal
import glob

# Adicionar o diretório raiz ao caminho de importação
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Importar os modelos após configurar o ambiente Django
from alta.models import AddPrice, GasStation, Produto, PesquisaOrigem

def extract_and_save_data(file_path):
    """
    Extrai dados do arquivo Excel e salva na tabela addprice.
    
    Args:
        file_path (str): Caminho para o arquivo Excel
    """
    # Verificar se o arquivo existe
    if not os.path.exists(file_path):
        print(f"Erro: O arquivo {file_path} não foi encontrado.")
        return
    
    try:
        # Ler o arquivo Excel pulando as primeiras linhas de cabeçalho
        print(f"\nLendo arquivo Excel: {file_path}")
        df = pd.read_excel(file_path, skiprows=9)  # Pula até a linha 10 (índice 9)
        
        # Mostrar todas as colunas disponíveis no arquivo
        print("\nColunas disponíveis no arquivo Excel:")
        for col in df.columns:
            print(f"- {col}")
        
        # Mostrar as primeiras 5 linhas do arquivo
        print("\nPrimeiras 5 linhas do arquivo:")
        print(df.head())
        
        # Contador para acompanhar o progresso
        contador = 0
        registros_salvos = 0
        
        # Processar cada linha do DataFrame
        for index, row in df.iterrows():
            contador += 1
            
            try:
                # Extrair dados da linha com os nomes exatos das colunas
                cnpj = str(row['CNPJ']).strip() if pd.notna(row['CNPJ']) else ''
                produto_nome = str(row['PRODUTO']).strip() if pd.notna(row['PRODUTO']) else ''
                preco_revenda = str(row['PREÇO DE REVENDA']).strip() if pd.notna(row['PREÇO DE REVENDA']) else ''
                unidade_medida = str(row['UNIDADE DE MEDIDA']).strip() if pd.notna(row['UNIDADE DE MEDIDA']) else ''
                data_coleta = row['DATA DA COLETA'] if pd.notna(row['DATA DA COLETA']) else None
                
                # Log dos valores lidos
                print(f"\nProcessando linha {contador}:")
                print(f"  CNPJ: {cnpj}")
                print(f"  PRODUTO: {produto_nome}")
                print(f"  PREÇO DE REVENDA: {preco_revenda}")
                print(f"  UNIDADE DE MEDIDA: {unidade_medida}")
                print(f"  DATA DA COLETA: {data_coleta}")
                
                # Verificar se os dados essenciais estão presentes
                dados_faltantes = []
                if not cnpj:
                    dados_faltantes.append("CNPJ")
                if not produto_nome:
                    dados_faltantes.append("PRODUTO")
                if not preco_revenda:
                    dados_faltantes.append("PREÇO DE REVENDA")
                
                if dados_faltantes:
                    print(f"Linha {contador}: Dados essenciais ausentes: {', '.join(dados_faltantes)}")
                    continue
                
                # Converter preços para Decimal
                try:
                    preco_revenda_decimal = Decimal(str(preco_revenda).replace(',', '.'))
                    print(f"Preço convertido: Revenda={preco_revenda_decimal}")
                except (ValueError, TypeError) as e:
                    print(f"Linha {contador}: Erro ao converter preços: {str(e)}")
                    continue
                
                # Buscar o posto de gasolina pelo CNPJ
                try:
                    gas_station = GasStation.objects.get(cnpj=cnpj)
                    print(f"Posto encontrado: {cnpj} (ID: {gas_station.id})")
                except GasStation.DoesNotExist:
                    print(f"Posto não encontrado para CNPJ: {cnpj}. Criando novo posto...")
                    
                    # Extrair dados adicionais da planilha para o novo posto
                    razao = str(row['RAZÃO']).strip() if pd.notna(row['RAZÃO']) else ''
                    fantasia = str(row['FANTASIA']).strip() if pd.notna(row['FANTASIA']) else ''
                    endereco = str(row['ENDEREÇO']).strip() if pd.notna(row['ENDEREÇO']) else ''
                    estado = str(row['ESTADO']).strip() if pd.notna(row['ESTADO']) else ''
                    cidade = str(row['MUNICÍPIO']).strip() if pd.notna(row['MUNICÍPIO']) else ''
                    bairro = str(row['BAIRRO']).strip() if pd.notna(row['BAIRRO']) else ''
                    cep = str(row['CEP']).strip() if pd.notna(row['CEP']) else ''
                    complemento = str(row['COMPLEMENTO']).strip() if pd.notna(row['COMPLEMENTO']) else ''
                    bandeira = str(row['BANDEIRA']).strip() if pd.notna(row['BANDEIRA']) else ''
                    numero = str(row['NÚMERO']).strip() if pd.notna(row['NÚMERO']) else ''
                    
                    # Criar novo posto
                    gas_station = GasStation.objects.create(
                        cnpj=cnpj,
                        razao=razao,
                        fantasia=fantasia,
                        endereco=endereco,
                        estado=estado,
                        cidade=cidade,
                        bairro=bairro,
                        cep=cep,
                        complemento=complemento,
                        bandeira=bandeira,
                        numero=numero,
                        data_bandeira=None,  # Definido como nulo
                        data_autorizacao=None,  # Definido como nulo
                    )
                    print(f"Novo posto criado com sucesso: {cnpj} (ID: {gas_station.id})")
                
                # Buscar o produto pelo nome
                try:
                    produto = Produto.objects.get(produto=produto_nome)
                    print(f"Produto encontrado: {produto_nome} (ID: {produto.id})")
                except Produto.DoesNotExist:
                    print(f"Produto não encontrado: {produto_nome}")
                    produto = None
                
                # Criar o registro de preço com os campos corretos
                novo_registro = AddPrice.objects.create(
                    data_coleta=data_coleta,  # Usando a data da coluna DATA DA COLETA
                    produto_id_id=produto.id if produto else None,  # Usando o ID do produto
                    gasstation_id_id=gas_station.id if gas_station else None,  # Usando o ID do posto
                    pesquisa_origem_id=1,  # Valor fixo conforme solicitado
                    unidade_medida=unidade_medida,
                    preco_revenda=preco_revenda_decimal,
                    preco_compra=None,  # Campo não existe no Excel
                    user_id=1,  # Valor fixo conforme solicitado
                    cnpj=cnpj,  # Salvando o CNPJ da planilha
                    produto=produto_nome  # Salvando o nome do produto da planilha
                )
                
                # Verificar se o registro foi criado corretamente
                print(f"\nRegistro criado com sucesso:")
                print(f"  ID: {novo_registro.id}")
                print(f"  Data Coleta: {novo_registro.data_coleta}")
                print(f"  Produto ID: {novo_registro.produto_id}")
                print(f"  Posto ID: {novo_registro.gasstation_id}")
                print(f"  Preço Revenda: {novo_registro.preco_revenda}")
                print(f"  Unidade Medida: {novo_registro.unidade_medida}")
                
                registros_salvos += 1
                
            except Exception as e:
                print(f"Erro ao processar linha {contador}: {str(e)}")
                continue
    
    except Exception as e:
        print(f"Erro ao ler o arquivo Excel: {str(e)}")
        return
    
    print(f"\nProcessamento concluído para o arquivo {file_path}")
    print(f"Total de registros processados: {contador}")
    print(f"Total de registros salvos: {registros_salvos}")

if __name__ == "__main__":
    # Caminho específico para o arquivo
    file_path = os.path.join("static", "files", "2025", "revendas_lpc_2025-04-13_2025-04-19.xlsx")
    
    # Verificar se o arquivo existe
    if not os.path.exists(file_path):
        print(f"Erro: O arquivo {file_path} não foi encontrado.")
        sys.exit(1)
    
    print(f"\n{'='*50}")
    print(f"Iniciando processamento do arquivo: {os.path.basename(file_path)}")
    print(f"{'='*50}")
    
    extract_and_save_data(file_path)
    
    print(f"\n{'='*50}")
    print(f"Processamento concluído para: {os.path.basename(file_path)}")
    print(f"{'='*50}\n")
