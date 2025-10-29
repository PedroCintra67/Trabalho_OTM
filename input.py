import yfinance as yf
import pandas as pd
import numpy as np
from bcb import sgs

# --- 1. CONFIGURAÇÕES INICIAIS ---

# Período de análise dos dados
DATA_INICIO = '2020-10-01'
DATA_FIM = '2025-10-01' # Usando a data do seu script original

# Vamos definir os ativos separando por classe
# O sufixo .SA é para a B3 (Brasil)
# Pares BRL são para Cripto em Reais
ASSET_ACOES = ['VALE3.SA', 'LREN3.SA', 'PETR4.SA', 'BBAS3.SA']
ASSET_RENDA_FIXA = ['B5P211.SA'] # ETF que reflete títulos do governo
ASSET_CRIPTO = ['BTC-BRL', 'ETH-BRL']

# Lista completa de todos os ativos
LISTA_ATIVOS = ASSET_ACOES + ASSET_RENDA_FIXA + ASSET_CRIPTO

# Ativo para benchmark de mercado e para definir os dias úteis ( pregões)
BENCHMARK_MERCADO = '^BVSP'

# Código da Taxa Selic (Meta) no Banco Central
CODIGO_SELIC = 432

def baixar_dados_precos(tickers, inicio, fim):
    """
    Baixa os preços de fechamento ajustados do Yahoo Finance.
    """
    print(f"Baixando dados de preços para {len(tickers)} ativos...")
    try:
        dados_precos = yf.download(tickers=tickers, 
                                   start=inicio, 
                                   end=fim)['Adj Close']
        
        # Se baixar só 1 ativo, o yf não retorna um DataFrame com nome,
        # então corrigimos isso.
        if len(tickers) == 1:
            dados_precos = dados_precos.to_frame(name=tickers[0])
            
        print("Download de preços concluído.")
        return dados_precos
    
    except Exception as e:
        print(f"Erro ao baixar dados do yfinance: {e}")
        return None
    

def baixar_taxa_livre_de_risco(codigo_selic, inicio, fim):
    """
    Baixa a taxa Selic (meta) anualizada do Banco Central do Brasil.
    """
    print("Baixando dados da Taxa Selic do BCB...")
    try:
        selic_df = sgs.get({'selic': codigo_selic}, start=inicio, end=fim)
        # O BCB retorna a taxa em % a.a. (ex: 10.5). 
        # Vamos converter para decimal (ex: 0.105)
        selic_diaria_anualizada = selic_df['selic'] / 100
        selic_diaria_anualizada.name = 'Selic_Anualizada'
        
        print("Download da Selic concluído.")
        return selic_diaria_anualizada
    
    except Exception as e:
        print(f"Erro ao baixar dados da Selic: {e}")
        return None
    
def calcular_retornos_diarios(tickers, benchmark, selic_data, inicio, fim):
    """
    1. Baixa os dados de benchmark (Ibov) para usar como calendário mestre.
    2. Baixa os dados de preços dos ativos.
    3. Alinha todos os dados aos dias de pregão do Ibov.
    4. Calcula os retornos diários.
    """
    
    # 1. Usar o Ibovespa para definir os dias úteis (pregões)
    print("Obtendo calendário de pregões (Ibovespa)...")
    calendario_pregoes = yf.download(benchmark, start=inicio, end=fim).index
    
    # 2. Baixar os preços
    precos = baixar_dados_precos(tickers, inicio, fim)
    if precos is None:
        return None, None
        
    # 3. Alinhar todos os dados
    # Reindexa os preços ao calendário de pregões.
    # 'ffill' (forward fill) preenche os dias sem pregão (ex: fim de semana)
    # com o último preço válido. Isso é crucial para cripto.
    precos_alinhados = precos.reindex(calendario_pregoes, method='ffill')
    
    # Alinhar a Selic também
    selic_alinhada = selic_data.reindex(calendario_pregoes, method='ffill')
    
    # Remover quaisquer linhas que ainda tenham NaN (ex: início do período)
    precos_alinhados = precos_alinhados.dropna()
    selic_alinhada = selic_alinhada.loc[precos_alinhados.index]
    
    # 4. Calcular os retornos diários
    # pct_change() calcula a variação percentual de um dia para o outro
    retornos_diarios = precos_alinhados.pct_change()
    
    # O primeiro dia terá NaN após o pct_change(), então removemos
    retornos_diarios = retornos_diarios.dropna()
    
    # Alinhar a Selic com os retornos (que perderam o primeiro dia)
    selic_alinhada = selic_alinhada.loc[retornos_diarios.index]

    print("Retornos diários e Selic alinhados.")
    return retornos_diarios, selic_alinhada

def calcular_inputs_otimizacao():
    """
    Função principal que orquestra o download e o cálculo
    dos inputs para o modelo de otimização.
    
    Retorna um dicionário contendo:
    - 'retornos_medios': (μ) Retornos médios anuais de cada ativo.
    - 'matriz_cov': (Σ) Matriz de covariância anualizada.
    - 'matriz_retornos_historicos': DataFrame de retornos diários.
    - 'taxa_livre_de_risco': Taxa Selic anualizada mais recente.
    - 'nomes_dos_ativos': Lista com os nomes dos ativos.
    """
    
    # Baixar Selic primeiro
    selic_data = baixar_taxa_livre_de_risco(CODIGO_SELIC, DATA_INICIO, DATA_FIM)
    if selic_data is None:
        return None

    # Baixar e processar retornos
    retornos, selic = calcular_retornos_diarios(
        LISTA_ATIVOS, 
        BENCHMARK_MERCADO, 
        selic_data, 
        DATA_INICIO, 
        DATA_FIM
    )
    
    if retornos is None:
        return None
        
    DIAS_UTEIS_ANO = 252 # Padrão de mercado
    
    # --- Calcular os Inputs para Otimização ---
    
    # 1. Retornos Médios (μ) - Anualizados
    retornos_medios_anuais = retornos.mean() * DIAS_UTEIS_ANO
    
    # 2. Matriz de Covariância (Σ) - Anualizada
    matriz_cov_anual = retornos.cov() * DIAS_UTEIS_ANO
    
    # 3. Taxa Livre de Risco Anualizada
    # Pegamos a última disponível
    taxa_livre_de_risco = selic.iloc[-1]
    
    # 4. Matriz de Retornos Históricos (para modelos como CVaR)
    # Não precisa de cálculo, são os próprios retornos diários
    
    # 5. Nomes dos Ativos
    nomes_dos_ativos = list(retornos.columns)
    
    print("--- Inputs de Otimização Prontos ---")
    print(f"Ativos processados: {nomes_dos_ativos}")
    print(f"Período: {retornos.index.min().date()} a {retornos.index.max().date()}")
    print(f"Taxa Livre de Risco (Selic): {taxa_livre_de_risco:.2%}")
    
    # Retornar tudo em um dicionário organizado
    return {
        'retornos_medios': retornos_medios_anuais,
        'matriz_cov': matriz_cov_anual,
        'matriz_retornos_historicos': retornos,
        'taxa_livre_de_risco': taxa_livre_de_risco,
        'nomes_dos_ativos': nomes_dos_ativos,
        'n_ativos': len(nomes_dos_ativos)
    }

# --- Bloco de Teste ---
# Se você executar este arquivo (preparar_dados.py) diretamente,
# ele chamará a função principal e imprimirá os resultados.
if __name__ == '__main__':
    
    inputs = calcular_inputs_otimizacao()
    
    if inputs:
        print("\n--- TESTE DO ARQUIVO ---")
        print("\nRetornos Médios Anuais (μ):")
        print(inputs['retornos_medios'])
        
        print("\nMatriz de Covariância Anual (Σ):")
        print(inputs['matriz_cov'])
        
        print(f"\nNúmero de Ativos: {inputs['n_ativos']}")