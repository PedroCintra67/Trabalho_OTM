import yfinance as yf
import pandas as pd
import numpy as np
import datetime
from bcb import sgs

# --- 1. IMPORTAR CONFIGURAÇÕES DO USUÁRIO ---
import config

# --- 2. PARÂMETROS DE IMPLEMENTAÇÃO ---
# (Configurações internas do modelo, não do usuário)

# Benchmark usado para alinhar o calendário de pregões
BENCHMARK_MERCADO = '^BVSP'

# Código da "Taxa de juros - Selic - diária" (Anualizada base 252)
# Esta é a série que tentaremos baixar.
SELIC_CODIGO = 4390

# Valor de fallback (em decimal) caso a API do BCB falhe.
SELIC_FALLBACK = 0.09 # 9% a.a.

# Dias úteis (pregões) em um ano
DIAS_UTEIS_ANO = 252


# --- 3. FUNÇÕES DE COLETA DE DADOS ---

def baixar_taxa_livre_de_risco(data_inicio_str, data_fim_str):
    """
    (Sua Req. 1)
    Tenta baixar a série histórica da Selic do BCB.
    Se falhar, retorna o valor de fallback.
    Retorna a *última* taxa disponível como um float.
    """
    print(f"Tentando baixar Taxa Selic (Cód: {SELIC_CODIGO}) do BCB...")
    try:
        selic_df = sgs.get({'selic': SELIC_CODIGO}, 
                           start=data_inicio_str, 
                           end=data_fim_str)
        
        # Limpa e pega o último valor válido
        selic_df = selic_df.dropna()
        ultimo_valor = selic_df['selic'].iloc[-1]
        
        # Converte de % para decimal
        taxa_real = ultimo_valor / 100.0
        
        print(f"Sucesso: Selic real obtida ({taxa_real:.2%})")
        return taxa_real
    
    except Exception as e:
        print(f"*** AVISO: Falha ao baixar Selic do BCB (Erro: {e}).")
        print(f"*** Usando a taxa de fallback definida: {SELIC_FALLBACK:.2%}")
        return SELIC_FALLBACK

def baixar_dados_precos(tickers, inicio, fim):
    """
    Baixa os preços de fechamento (que agora já vêm ajustados
    por padrão pelo yfinance)
    """
    print(f"Baixando dados de preços para {len(tickers)} ativos...")
    try:
        dados_precos = yf.download(tickers=tickers, 
                                   start=inicio, 
                                   end=fim)['Close']
        
        if len(tickers) == 1:
            dados_precos = dados_precos.to_frame(name=tickers[0])
            
        print("Download de preços concluído.")
        return dados_precos
    
    except Exception as e:
        print(f"Erro ao baixar dados do yfinance: {e}")
        return None

def calcular_retornos_diarios(tickers, benchmark, inicio, fim):
    """
    1. Baixa os dados de benchmark (Ibov) para usar como calendário mestre.
    2. Baixa os dados de preços dos ativos.
    3. Alinha todos os dados aos dias de pregão do Ibov.
    4. Calcula os retornos diários.
    """
    
    print("Obtendo calendário de pregões (Ibovespa)...")
    try:
        calendario_pregoes = yf.download(benchmark, start=inicio, end=fim).index
    except Exception as e:
        print(f"Erro fatal: Não foi possível baixar o benchmark {benchmark}. {e}")
        return None

    precos = baixar_dados_precos(tickers, inicio, fim)
    if precos is None:
        return None
        
    # Remove qualquer ativo que falhou totalmente no download (colunas só com NaN)
    precos = precos.dropna(axis='columns', how='all')
    if precos.empty:
        print("Erro: Nenhum dado de preço foi baixado com sucesso.")
        return None
        
    print(f"Ativos baixados com sucesso: {list(precos.columns)}")

    precos_alinhados = precos.reindex(calendario_pregoes, method='ffill')
    precos_alinhados = precos_alinhados.dropna()
    
    retornos_diarios = precos_alinhados.pct_change()
    retornos_diarios = retornos_diarios.dropna()
    
    print("Retornos diários alinhados.")
    
    return retornos_diarios


# --- 4. FUNÇÃO PRINCIPAL DE ORQUESTRAÇÃO ---

def calcular_inputs_otimizacao():
    """
    Função principal que orquestra o download e o cálculo
    dos inputs para o modelo de otimização, usando o 'config.py'.
    """
    
    # --- 1. Calcular Datas (Req. "Últimos 5 Anos") ---
    print("Calculando período de análise...")
    data_fim = datetime.date.today()
    # .timedelta(days=...) é mais preciso que (anos*365)
    data_inicio = data_fim - datetime.timedelta(days=int(config.ANOS_DE_DADOS * 365.25))
    
    # Converter para string (formato YYYY-MM-DD) para as APIs
    data_fim_str = data_fim.isoformat()
    data_inicio_str = data_inicio.isoformat()
    
    print(f"Período definido: {data_inicio_str} a {data_fim_str}")
    
    # --- 2. Obter Taxa Livre de Risco (Req. 1) ---
    taxa_livre_de_risco = baixar_taxa_livre_de_risco(data_inicio_str, data_fim_str)
    
    # --- 3. Obter Retornos dos Ativos (Req. 2) ---
    retornos = calcular_retornos_diarios(
        config.LISTA_COMPLETA_ATIVOS, 
        BENCHMARK_MERCADO, 
        data_inicio_str, 
        data_fim_str
    )
    
    if retornos is None or retornos.empty:
        print("Erro fatal: Não foi possível calcular os retornos dos ativos.")
        return None
        
    # --- 4. Calcular Inputs para Otimização (μ e Σ) ---
    print("Calculando μ (Retornos Médios) e Σ (Matriz de Covariância)...")
    retornos_medios_anuais = retornos.mean() * DIAS_UTEIS_ANO
    matriz_cov_anual = retornos.cov() * DIAS_UTEIS_ANO
    
    nomes_dos_ativos = list(retornos.columns)
    
    # Checagem final por dados inválidos
    if retornos_medios_anuais.isnull().any() or matriz_cov_anual.isnull().values.any():
        print("Erro: Dados de retorno ou covariância contêm NaN após processamento.")
        print("Verifique os tickers no 'config.py'. Ativos problemáticos:")
        print(retornos_medios_anuais[retornos_medios_anuais.isnull()])
        return None

    print("\n--- Inputs de Otimização Prontos ---")
    print(f"Ativos processados: {nomes_dos_ativos}")
    print(f"Período: {retornos.index.min().date()} a {retornos.index.max().date()}")
    print(f"Taxa Livre de Risco utilizada: {taxa_livre_de_risco:.2%}")
    
    return {
        'retornos_medios': retornos_medios_anuais,
        'matriz_cov': matriz_cov_anual,
        'matriz_retornos_historicos': retornos,
        'taxa_livre_de_risco': taxa_livre_de_risco,
        'nomes_dos_ativos': nomes_dos_ativos,
        'n_ativos': len(nomes_dos_ativos)
    }

# --- Bloco de Teste ---
if __name__ == '__main__':
    """
    Se você executar este arquivo (preparar_dados.py) diretamente,
    ele chamará a função principal e imprimirá os resultados.
    Útil para testar a coleta de dados isoladamente.
    """
    print("--- TESTANDO 'preparar_dados.py' ---")
    
    inputs = calcular_inputs_otimizacao()
    
    if inputs:
        print("\n--- TESTE CONCLUÍDO COM SUCESSO ---")
        print(f"\nNúmero de Ativos: {inputs['n_ativos']}")
        print("\nRetornos Médios Anuais (μ):")
        print(inputs['retornos_medios'])
    else:
        print("\n--- TESTE FALHOU ---")