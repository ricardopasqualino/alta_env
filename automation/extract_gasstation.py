import os
import sys
import django
import pandas as pd
import logging
from datetime import datetime

# Adicionar o diretório raiz ao caminho de importação
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Importar os modelos após configurar o ambiente Django
from alta.models import GasStation

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gasstation_extraction.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def extract_and_save_gasstations(file_path, limit=None):
    """
    Extrai dados do arquivo Excel e salva na tabela GasStation.
    
    Args:
        file_path (str): Caminho para o arquivo Excel
        limit (int, optional): Limite de registros a serem processados. Se None, processa todos.
    """
    # Verificar se o arquivo existe
    if not os.path.exists(file_path):
        logging.error(f"Erro: O arquivo {file_path} não foi encontrado.")
        return
    
    # Contador para acompanhar o progresso
    contador = 0
    registros_salvos = 0
    registros_atualizados = 0
    
    try:
        # Ler o arquivo Excel
        logging.info(f"Lendo arquivo Excel: {file_path}")
        df = pd.read_excel(file_path)
        logging.info(f"Colunas encontradas no arquivo: {list(df.columns)}")
        
        # Limitar o número de registros se especificado
        if limit is not None:
            df = df.head(limit)
            logging.info(f"Limitando processamento aos {limit} primeiros registros")
        
        # Mapeamento de colunas do Excel para campos do modelo
        # Ajuste este mapeamento de acordo com as colunas do seu arquivo Excel
        column_mapping = {
            'CNPJ': 'cnpj',
            'Razão Social': 'razao',
            'Endereço': 'endereco',
            'COMPLEMENTO': 'complemento',
            'BAIRRO': 'bairro',
            'CEP': 'cep',
            'MUNICÍPIO': 'cidade',
            'UF': 'estado',
            'Vinculação a Distribuidor': 'bandeira',
            'Data de Vinculação a Distribuidor': 'data_bandeira',
            'Data Publicação DOU - Autorização': 'data_autorizacao',
            'Nº Autorizacao': 'nr_autorizacao',
            'Código Instalação i-Simp': 'codigo_simp'
        }
        
        # Processar cada linha do DataFrame
        for index, row in df.iterrows():
            contador += 1
            
            try:
                # Extrair dados da linha
                cnpj = str(row.get('CNPJ', '')).strip()
                
                # Verificar se o CNPJ está presente
                if not cnpj:
                    logging.warning(f"Linha {contador}: CNPJ ausente. Pulando...")
                    continue
                
                # Criar dicionário com os dados do posto
                gas_station_data = {}
                
                # Mapear colunas do Excel para campos do modelo
                for excel_col, model_field in column_mapping.items():
                    if excel_col in row and pd.notna(row[excel_col]):
                        # Converter para string e remover espaços em branco
                        value = str(row[excel_col]).strip()
                        
                        # Tratamento especial para campos de data
                        if model_field in ['data_bandeira', 'data_autorizacao']:
                            try:
                                value = pd.to_datetime(value).date()
                            except (ValueError, TypeError):
                                value = None
                        
                        gas_station_data[model_field] = value
                
                # Buscar ou criar o posto de gasolina
                try:
                    gas_station = GasStation.objects.get(cnpj=cnpj)
                    
                    # Atualizar os campos existentes
                    for field, value in gas_station_data.items():
                        if hasattr(gas_station, field):
                            setattr(gas_station, field, value)
                    
                    gas_station.save()
                    registros_atualizados += 1
                    
                    if contador % 100 == 0:
                        logging.info(f"Posto atualizado: {cnpj} - {gas_station_data.get('razao', '')}")
                
                except GasStation.DoesNotExist:
                    # Criar um novo posto
                    gas_station = GasStation.objects.create(**gas_station_data)
                    registros_salvos += 1
                    
                    if contador % 100 == 0:
                        logging.info(f"Novo posto criado: {cnpj} - {gas_station_data.get('razao', '')}")
                
                # Imprimir progresso a cada 100 registros
                if contador % 100 == 0:
                    logging.info(f"Processados {contador} registros. Salvos: {registros_salvos}, Atualizados: {registros_atualizados}")
                
            except Exception as e:
                logging.error(f"Erro ao processar linha {contador}: {str(e)}")
    
    except Exception as e:
        logging.error(f"Erro ao ler o arquivo Excel: {str(e)}")
        return
    
    logging.info(f"Processamento concluído. Total de registros processados: {contador}")
    logging.info(f"Total de registros salvos: {registros_salvos}")
    logging.info(f"Total de registros atualizados: {registros_atualizados}")

if __name__ == "__main__":
    # Caminho para o arquivo de dados
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "files", "export_gasstation.xlsx")
    
    # Executar a extração e salvamento de todos os registros
    extract_and_save_gasstations(file_path) 