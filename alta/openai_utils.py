import os
import openai
from django.conf import settings
import numpy as np
from typing import List, Dict, Any

# Configurar a API key da OpenAI
openai.api_key = settings.OPENAI_API_KEY

def generate_embedding(text: str) -> List[float]:
    """
    Gera um embedding para o texto fornecido usando a API da OpenAI
    """
    try:
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Erro ao gerar embedding: {str(e)}")
        return None

def generate_price_embedding(addprice) -> Dict[str, Any]:
    """
    Gera um embedding para um objeto AddPrice
    """
    # Criar um texto descritivo do preço
    text = f"""
    Posto: {addprice.gasstation_id.razao}
    Produto: {addprice.produto_id.produto}
    Preço: R$ {addprice.preco_revenda}
    Data: {addprice.data_coleta}
    Cidade: {addprice.gasstation_id.cidade}
    Estado: {addprice.gasstation_id.estado}
    Bandeira: {addprice.gasstation_id.bandeira}
    """
    
    embedding = generate_embedding(text)
    if embedding:
        return {
            'addprice': addprice,
            'embedding': embedding
        }
    return None

def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calcula a similaridade de cosseno entre dois embeddings
    """
    return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)) 