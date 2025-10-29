"""
================================================
ARQUIVO DE CONFIGURAÇÃO DO PROJETO DE OTIMIZAÇÃO
================================================

Este é o único arquivo que o usuário deve alterar.
Ele define todos os parâmetros de entrada para o modelo.
"""

# --- 1. PARÂMETROS DE INVESTIMENTO ---

# O valor total a ser investido (em R$).
VALOR_TOTAL_INVESTIMENTO = 100000.00 # Ex: R$ 100.000,00

# O horizonte de tempo (em anos) dos dados históricos que
# serão usados para "prever" o comportamento futuro.
ANOS_DE_DADOS = 5


# --- 2. LISTA DE ATIVOS PARA OTIMIZAÇÃO ---
# (Sinta-se à vontade para adicionar, remover ou comentar
#  linhas para testar diferentes universos de ativos)

# Ações Brasileiras (Ações)
LISTA_ACOES = [
    'PETR4.SA', # Petrobras
    'VALE3.SA', # Vale
    'ITUB4.SA', # Itaú Unibanco
    'BBDC4.SA', # Bradesco
    'BBAS3.SA', # Banco do Brasil
    'ABEV3.SA', # Ambev
    'MGLU3.SA', # Magazine Luiza
    'LREN3.SA', # Lojas Renner
    'RADL3.SA', # Raia Drogasil
    'WEGE3.SA', # WEG
    'SUZB3.SA', # Suzano
    'RENT3.SA', # Localiza
]

# BDRs (Ações Estrangeiras)
LISTA_BDRS = [
    'AAPL34.SA', # Apple
    'MSFT34.SA', # Microsoft
    'GOGL34.SA', # Google
    'MELI34.SA', # Mercado Livre
    'TSLA34.SA', # Tesla
    'NVDC34.SA', # Nvidia
]

# ETFs (Fundos de Índice)
LISTA_ETFS = [
    'BOVA11.SA', # ETF do Ibovespa
    'IVVB11.SA', # ETF do S&P 500
    'GOLD11.SA', # ETF de Ouro
    'SMAL11.SA', # ETF de Small Caps
]

# FIIs (Fundos Imobiliários)
LISTA_FIIS = [
    'HGLG11.SA', # CSHG Logística
    'KNCR11.SA', # Kinea Renda
    'MXRF11.SA', # Maxi Renda
]

# Renda Fixa (ETFs)
LISTA_RENDA_FIXA = [
    'B5P211.SA', # ETF de Títulos IPCA (curto prazo)
    'IMAB11.SA', # ETF de Títulos IPCA (longo prazo)
]

# Criptomoedas
LISTA_CRIPTO = [
    'BTC-USD', # Bitcoin
    'ETH-USD', # Ethereum
    'SOL-USD', # Solana
]

# Combinação de todas as listas
LISTA_COMPLETA_ATIVOS = (
    LISTA_ACOES + 
    LISTA_BDRS + 
    LISTA_ETFS + 
    LISTA_FIIS + 
    LISTA_RENDA_FIXA + 
    LISTA_CRIPTO
)


# --- 3. COMENTÁRIOS PARA MELHORIAS FUTURAS ---

# TODO: Implementar perfis de investidor
# A ideia é usar o perfil (ex: 'CONSERVADOR', 'MODERADO', 'AGRESSIVO')
# para definir restrições de otimização.
PERFIL_INVESTIDOR = 'MODERADO'


# TODO: Implementar restrições de "mundo real" (Lotes Mínimos)
# Atualmente, o modelo otimiza pesos contínuos (ex: 1.2345% de PETR4).
# Na vida real, só podemos comprar "lotes".
# Isso mudaria o problema para uma "Programação Inteira Mista" (MIP).