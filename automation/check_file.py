import os
import csv
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation/file_check_log.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def check_file_format(file_path):
    """
    Verifica o formato do arquivo e retorna informações sobre sua estrutura.
    
    Args:
        file_path (str): Caminho para o arquivo
        
    Returns:
        dict: Informações sobre o arquivo
    """
    # Verificar se o arquivo existe
    if not os.path.exists(file_path):
        logging.error(f"Arquivo não encontrado: {file_path}")
        return {"error": "Arquivo não encontrado"}
    
    # Colunas esperadas
    expected_columns = [
        'cnpj', 'razao_social', 'fantasia', 'endereco', 'numero', 
        'complemento', 'bairro', 'cep', 'cidade', 'estado', 
        'bandeira', 'produto', 'preco_revenda', 'preco_compra', 'unidade_medida'
    ]
    
    # Tentar determinar o delimitador
    with open(file_path, 'r', encoding='utf-8') as file:
        # Ler as primeiras linhas para determinar o delimitador
        first_lines = [file.readline() for _ in range(5)]
        
        # Verificar se é CSV ou TSV
        if ',' in first_lines[0]:
            delimiter = ','
            file_type = 'CSV'
        elif '\t' in first_lines[0]:
            delimiter = '\t'
            file_type = 'TSV'
        else:
            logging.error("Não foi possível determinar o delimitador do arquivo")
            return {"error": "Delimitador não identificado"}
    
    # Analisar o arquivo
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        
        # Obter as colunas do arquivo
        file_columns = reader.fieldnames
        
        # Verificar colunas ausentes
        missing_columns = [col for col in expected_columns if col not in file_columns]
        
        # Verificar colunas extras
        extra_columns = [col for col in file_columns if col not in expected_columns]
        
        # Contar linhas
        file.seek(0)
        next(reader)  # Pular o cabeçalho
        row_count = sum(1 for _ in reader)
        
        # Verificar valores nas primeiras linhas
        file.seek(0)
        next(reader)  # Pular o cabeçalho novamente
        sample_rows = []
        for i, row in enumerate(reader):
            if i < 5:  # Analisar apenas as 5 primeiras linhas de dados
                sample_rows.append(row)
            else:
                break
    
    # Preparar resultado
    result = {
        "file_type": file_type,
        "delimiter": delimiter,
        "row_count": row_count,
        "missing_columns": missing_columns,
        "extra_columns": extra_columns,
        "sample_rows": sample_rows
    }
    
    # Registrar resultados
    logging.info(f"Tipo de arquivo: {file_type}")
    logging.info(f"Delimitador: {delimiter}")
    logging.info(f"Total de linhas: {row_count}")
    
    if missing_columns:
        logging.warning(f"Colunas ausentes: {missing_columns}")
    else:
        logging.info("Todas as colunas esperadas estão presentes")
    
    if extra_columns:
        logging.info(f"Colunas extras: {extra_columns}")
    
    return result

if __name__ == "__main__":
    # Obter o diretório atual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Caminho para o arquivo de dados
    file_path = os.path.join(current_dir, "..", "revendas_lpc_2025-04-20_2025-04-26")
    
    # Verificar o arquivo
    result = check_file_format(file_path)
    
    # Exibir resultados
    if "error" in result:
        print(f"Erro: {result['error']}")
    else:
        print("\nResumo da verificação:")
        print(f"Tipo de arquivo: {result['file_type']}")
        print(f"Total de linhas: {result['row_count']}")
        
        if result['missing_columns']:
            print(f"Colunas ausentes: {', '.join(result['missing_columns'])}")
        else:
            print("Todas as colunas esperadas estão presentes")
        
        if result['extra_columns']:
            print(f"Colunas extras: {', '.join(result['extra_columns'])}")
        
        print("\nAmostra das primeiras linhas:")
        for i, row in enumerate(result['sample_rows']):
            print(f"Linha {i+1}: {row}") 