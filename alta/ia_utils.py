import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from django.conf import settings
import json
import time
from functools import lru_cache
from .models import AddPrice, PriceEmbedding

def vetorizar_texto(texto):
    """
    Vetoriza um texto usando o modelo da OpenAI
    """
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(
            input=texto,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Erro ao vetorizar texto: {str(e)}")
        return None

def preparar_contexto_precos(addprice_queryset):
    """
    Prepara o contexto para análise de preços a partir de um queryset de AddPrice
    """
    contexto = []
    for preco in addprice_queryset:
        contexto.append({
            'data': preco.data_coleta.strftime('%d/%m/%Y'),
            'produto': preco.produto,
            'preco_revenda': float(preco.preco_revenda),
            'preco_compra': float(preco.preco_compra) if preco.preco_compra else None,
            'posto': preco.gasstation_id.razao if preco.gasstation_id else None,
            'cidade': preco.gasstation_id.cidade if preco.gasstation_id else None,
            'estado': preco.gasstation_id.estado if preco.gasstation_id else None,
            'bandeira': preco.gasstation_id.bandeira if preco.gasstation_id else None
        })
    return contexto

def processar_pergunta_ia(pergunta, contexto, max_contexto_tokens=2000):
    """
    Processa a pergunta usando a API da OpenAI e o contexto fornecido
    """
    try:
        if not settings.OPENAI_API_KEY:
            print("Erro: OPENAI_API_KEY não configurada")
            return "Erro de configuração: API key não encontrada"

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Verificar se o contexto está vazio
        if not contexto:
            print("Contexto vazio na função processar_pergunta_ia")
            return "Não foram encontrados dados para processar sua pergunta."
        
        print(f"Processando {len(contexto)} registros no contexto")
        
        # Limitar o tamanho do contexto
        contexto_limpo = []
        for preco in contexto:
            try:
                dados_preco = {
                    'data': preco['data_coleta'],
                    'produto': preco['produto'],
                    'preco': preco['preco_revenda'],
                    'posto': preco['posto'],
                    'cidade': preco['cidade'],
                    'estado': preco['estado'],
                    'bandeira': preco['bandeira']
                }
                contexto_limpo.append(dados_preco)
            except Exception as e:
                print(f"Erro ao processar preço: {str(e)}")
                continue

        # Preparar o prompt com o contexto
        prompt = f"""Você é um especialista em análise de preços de combustíveis.
        Use apenas as informações fornecidas no contexto para responder à pergunta.
        Se a informação não estiver disponível no contexto, informe que não possui dados suficientes.
        
        Regras importantes:
        1. Considere variações de escrita (ex: JUNDIAI, Jundiaí, JUNDIAÍ)
        2. Se a pergunta for sobre uma cidade específica, verifique todas as variações do nome
        3. Forneça informações detalhadas quando disponíveis
        4. Sempre inclua uma tabela com os postos e seus preços
        5. Calcule e apresente:
           - Preço médio
           - Preço mínimo
           - Preço máximo
        6. Formate a resposta em markdown para melhor visualização
        7. Sempre mencione a data dos dados fornecidos
        8. Organize os dados por produto quando houver mais de um tipo
        9. Se a pergunta for sobre preço médio, mínimo ou máximo, destaque esses valores
        10. Se houver muitos postos, mostre apenas os 10 mais recentes na tabela

        Contexto:
        {json.dumps(contexto_limpo, ensure_ascii=False, indent=2)}

        Pergunta: {pergunta}

        Resposta:"""

        print("Enviando requisição para a API da OpenAI...")
        
        # Implementar retry mechanism
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                print(f"Tentativa {attempt + 1} de {max_retries}")
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": """Você é um especialista em análise de preços de combustíveis.
                        Suas respostas devem sempre incluir:
                        1. Uma tabela formatada em markdown com os postos e preços
                        2. Cálculos estatísticos (média, mínimo, máximo)
                        3. Data dos dados
                        4. Organização por produto quando aplicável
                        
                        Exemplo de formato de resposta:
                        # Análise de Preços de Combustíveis
                        
                        ## Dados dos Postos
                        | Posto | Bandeira | Produto | Preço (R$) | Data |
                        |-------|----------|---------|------------|------|
                        | Posto A | Shell | Gasolina | 5,00 | 01/01/2024 |
                        | Posto B | Ipiranga | Etanol | 3,50 | 01/01/2024 |
                        
                        ## Estatísticas
                        - **Preço Médio:** R$ 4,25
                        - **Preço Mínimo:** R$ 3,50
                        - **Preço Máximo:** R$ 5,00
                        
                        Dados coletados em: 01/01/2024"""},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                resposta = response.choices[0].message.content
                print(f"Resposta recebida da API: {resposta[:200]}...")
                
                if not resposta or len(resposta.strip()) == 0:
                    raise ValueError("Resposta vazia da API")
                    
                return resposta
                
            except Exception as e:
                print(f"Erro na tentativa {attempt + 1}: {str(e)}")
                if "rate_limit_exceeded" in str(e) and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Aguardando {delay} segundos antes da próxima tentativa...")
                    time.sleep(delay)
                    continue
                elif "api_key" in str(e).lower():
                    print("Erro de autenticação com a API")
                    return "Erro de configuração: API key inválida"
                elif "timeout" in str(e).lower():
                    print("Erro de timeout na requisição")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"Aguardando {delay} segundos antes da próxima tentativa...")
                        time.sleep(delay)
                        continue
                raise e

    except Exception as e:
        print(f"Erro ao processar pergunta: {str(e)}")
        return f"Desculpe, ocorreu um erro ao processar sua pergunta: {str(e)}"

def calcular_similaridade(vetor1, vetor2):
    """
    Calcula a similaridade entre dois vetores usando cosseno
    """
    try:
        return cosine_similarity([vetor1], [vetor2])[0][0]
    except Exception as e:
        print(f"Erro ao calcular similaridade: {str(e)}")
        return 0.0

def encontrar_precos_similares(preco_referencia, lista_precos, limite=5):
    """
    Encontra os preços mais similares a um preço de referência
    """
    try:
        # Vetorizar o preço de referência
        vetor_referencia = vetorizar_texto(str(preco_referencia))
        if not vetor_referencia:
            return []

        # Calcular similaridade com todos os preços
        similaridades = []
        for preco in lista_precos:
            vetor_preco = vetorizar_texto(str(preco))
            if vetor_preco:
                similaridade = calcular_similaridade(vetor_referencia, vetor_preco)
                similaridades.append((preco, similaridade))

        # Ordenar por similaridade e retornar os top N
        similaridades.sort(key=lambda x: x[1], reverse=True)
        return similaridades[:limite]

    except Exception as e:
        print(f"Erro ao encontrar preços similares: {str(e)}")
        return []

def criar_ou_atualizar_embedding(addprice):
    """
    Cria ou atualiza o embedding para um registro de AddPrice
    """
    try:
        # Preparar o texto para vetorização
        texto = f"""
        Produto: {addprice.produto}
        Preço de Revenda: {addprice.preco_revenda}
        Preço de Compra: {addprice.preco_compra if addprice.preco_compra else 'N/A'}
        Posto: {addprice.gasstation_id.razao if addprice.gasstation_id else 'N/A'}
        Cidade: {addprice.gasstation_id.cidade if addprice.gasstation_id else 'N/A'}
        Estado: {addprice.gasstation_id.estado if addprice.gasstation_id else 'N/A'}
        Data: {addprice.data_coleta}
        """
        
        # Vetorizar o texto com retry
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                embedding = vetorizar_texto(texto)
                if embedding and len(embedding) > 0:
                    # Criar ou atualizar o PriceEmbedding
                    price_embedding, created = PriceEmbedding.objects.get_or_create(
                        addprice=addprice,
                        defaults={
                            'embedding': embedding,
                            'produto_nome': addprice.produto,
                            'posto_nome': addprice.gasstation_id.razao if addprice.gasstation_id else None
                        }
                    )
                    
                    if not created:
                        price_embedding.embedding = embedding
                        price_embedding.produto_nome = addprice.produto
                        price_embedding.posto_nome = addprice.gasstation_id.razao if addprice.gasstation_id else None
                        price_embedding.save()
                    
                    return price_embedding
                else:
                    raise ValueError("Embedding vazio ou inválido")
                    
            except Exception as e:
                if "rate_limit_exceeded" in str(e) and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                raise e
                
        return None
        
    except Exception as e:
        print(f"Erro ao criar/atualizar embedding: {str(e)}")
        return None 