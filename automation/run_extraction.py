import os
import sys
import logging
from datetime import datetime
from extract import extract_and_save_data
from check_file import check_file_format

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation/extraction_log.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_extraction():
    """
    Executa a extração de dados e registra o resultado no log.
    """
    try:
        # Obter o diretório atual
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Caminho para o arquivo de dados
        file_path = os.path.join(current_dir, "..", "revendas_lpc_2025-04-20_2025-04-26")
        
        # Registrar início da execução
        logging.info(f"Iniciando verificação do arquivo em {datetime.now()}")
        
        # Verificar o arquivo antes de processá-lo
        check_result = check_file_format(file_path)
        
        # Verificar se há erros na verificação
        if "error" in check_result:
            logging.error(f"Erro na verificação do arquivo: {check_result['error']}")
            return
        
        # Verificar se há colunas ausentes
        if check_result.get("missing_columns"):
            logging.warning(f"Colunas ausentes no arquivo: {check_result['missing_columns']}")
            logging.warning("A extração pode falhar devido a dados ausentes")
        
        # Registrar início da extração
        logging.info(f"Iniciando extração de dados em {datetime.now()}")
        
        # Executar a extração
        extract_and_save_data(file_path)
        
        # Registrar conclusão da execução
        logging.info(f"Extração concluída em {datetime.now()}")
        
    except Exception as e:
        # Registrar erros
        logging.error(f"Erro durante a extração: {str(e)}")
        raise

if __name__ == "__main__":
    run_extraction() 