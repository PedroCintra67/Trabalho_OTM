"""
================================================
ARQUIVO DE ANÁLISE E VISUALIZAÇÃO (Req. 3 e 4)
================================================

Este script é o "painel de controle" final.
Ele NÃO executa a otimização.

Seu trabalho é:
1. Ler o arquivo 'resultados_otimizacao.csv'.
2. Calcular métricas adicionais (como o Índice de Sharpe).
3. Apresentar 3 ANÁLISES SEPARADAS dos portfólios de destaque
   (Mínimo Risco, Máximo Retorno, Melhor Custo-Benefício).
4. Plotar o gráfico da Fronteira de Pareto e salvá-lo (sem exibir).
5. Plotar UM gráfico de pizza final para o portfólio de
   Melhor Custo-Benefício (Sharpe) e salvá-lo.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os # Para verificar se o arquivo existe

# --- 1. IMPORTAR DADOS DE OUTROS ARQUIVOS ---
import preparar_dados
import config

# --- 2. CONSTANTES DE ANÁLISE ---
ARQUIVO_RESULTADOS_CSV = 'resultados_otimizacao.csv'
ARQUIVO_FRONTEIRA_PNG = 'fronteira_de_pareto.png'
ARQUIVO_PIZZA_FINAL_PNG = 'distribuicao_carteira_otima_sharpe.png' # Nome do gráfico de pizza

# --- 3. FUNÇÕES AUXILIARES ---

def formatar_portifolio_para_print(series_portifolio, nomes_ativos, titulo=""):
    """Função auxiliar para imprimir a composição da carteira."""
    
    pesos_brutos = series_portifolio.filter(like='w_')
    pesos_relevantes = pesos_brutos[pesos_brutos > 0.005] # Pesos > 0.5%
    pesos_ordenados = pesos_relevantes.sort_values(ascending=False)
    valor_total = config.VALOR_TOTAL_INVESTIMENTO
    
    print(f"--- Composição da Carteira: {titulo} ---")
    if pesos_ordenados.empty:
        print("  Não há alocações significativas (todos os pesos < 0.5%).")
    else:
        for ativo, peso in pesos_ordenados.items():
            nome_limpo = ativo.replace('w_', '')
            valor_ativo = peso * valor_total
            print(f"  {nome_limpo:<10} | {peso:7.2%} | (R$ {valor_ativo:,.2f})")
            
        percentual_outros = 1.0 - pesos_ordenados.sum()
        if percentual_outros > 0.005: 
            valor_outros = percentual_outros * valor_total
            print(f"  Outros Ativos: {percentual_outros:.2%} | (R$ {valor_outros:,.2f})")
    print("-" * 40)

# --- NOVO: Função de Gráfico de Pizza ---
def plotar_distribuicao_pizza(series_portifolio, titulo, nome_arquivo):
    """
    (Sua Req. de Gráfico de Pizza Final)
    Plota um gráfico de pizza da distribuição de capital para
    o portfólio de Máximo Sharpe.
    """
    print(f"  Gerando gráfico de pizza para '{titulo}'...")
    pesos_brutos = series_portifolio.filter(like='w_')
    
    # Para um gráfico de pizza, agrupamos fatias pequenas
    threshold = 0.02 # Agrupar ativos com menos de 2%
    
    pesos_relevantes = pesos_brutos[pesos_brutos >= threshold]
    
    # Calcular a fatia "Outros"
    outros = pesos_brutos[pesos_brutos < threshold].sum()
    if outros > 0.001: # Só adiciona "Outros" se for relevante
        pesos_relevantes['Outros Ativos'] = outros
        
    pesos_relevantes = pesos_relevantes.sort_values(ascending=False)
    
    # Preparar labels (remover 'w_')
    labels = [ativo.replace('w_', '') for ativo in pesos_relevantes.index]
    
    plt.figure(figsize=(10, 8))
    # 'autopct' formata os percentuais, 'startangle' gira o gráfico
    plt.pie(pesos_relevantes.values, labels=labels, autopct='%1.1f%%', startangle=90, 
            pctdistance=0.85) # Coloca os percentuais dentro das fatias
    
    # Adiciona um círculo no centro para fazer um "donut chart" (mais legível)
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    
    plt.title(f"Distribuição de Capital: {titulo}", fontsize=16)
    plt.axis('equal') # Garante que a pizza seja um círculo
    plt.tight_layout()
    plt.savefig(nome_arquivo, dpi=300)
    print(f"  Gráfico de pizza salvo como '{nome_arquivo}'")
    plt.close() # Fecha a figura para não ocupar memória

# --- 4. BLOCO DE EXECUÇÃO PRINCIPAL ---
if __name__ == '__main__':
    
    print("--- INICIANDO ANÁLISE E VISUALIZAÇÃO DOS RESULTADOS ---")
    
    # --- PASSO 1: Carregar a Taxa Livre de Risco ---
    print("Carregando dados de input (para obter Taxa Selic)...")
    inputs = preparar_dados.calcular_inputs_otimizacao()
    if inputs is None:
        print("Erro fatal: Não foi possível carregar os dados de input.")
        exit()
        
    taxa_livre_de_risco = inputs['taxa_livre_de_risco']
    nomes_ativos = inputs['nomes_dos_ativos']
    
    # --- PASSO 2: Carregar o CSV com os resultados ---
    print(f"Lendo o arquivo de resultados '{ARQUIVO_RESULTADOS_CSV}'...")
    if not os.path.exists(ARQUIVO_RESULTADOS_CSV):
        print(f"Erro: Arquivo '{ARQUIVO_RESULTADOS_CSV}' não encontrado.")
        print("Por favor, execute o 'executar_otimizacao.py' primeiro.")
        exit()
        
    try:
        df_resultados = pd.read_csv(ARQUIVO_RESULTADOS_CSV, sep=';', decimal=',')
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}")
        exit()
        
    # --- PASSO 3: Calcular Custo-Benefício (Índice de Sharpe) ---
    df_resultados['Risco_StDev'] = np.sqrt(df_resultados['Risco_Anual'])
    df_resultados['Sharpe_Ratio'] = (df_resultados['Retorno_Anual'] - taxa_livre_de_risco) \
                                    / df_resultados['Risco_StDev']
                                    
    # --- PASSO 4: APRESENTAR AS 3 ANÁLISES SEPARADAS ---
    
    # ANÁLISE 1: Portfólio de MÍNIMO RISCO (PMV)
    portifolio_min_risco = df_resultados.loc[df_resultados['Risco_Anual'].idxmin()]
    
    print("\n====================================================================")
    print("               ANÁLISE 1: PORTFÓLIO DE MÍNIMO RISCO")
    print("                (Foco exclusivo na menor variância)")
    print("====================================================================")
    print(f"  Retorno Esperado:   {portifolio_min_risco['Retorno_Anual']:.2%}")
    print(f"  Risco (Variância):  {portifolio_min_risco['Risco_Anual']:.4f}")
    print(f"  Volatilidade (Desvio Padrão): {portifolio_min_risco['Risco_StDev']:.2%}")
    print(f"  Índice Sharpe:      {portifolio_min_risco['Sharpe_Ratio']:.2f}")
    formatar_portifolio_para_print(portifolio_min_risco, nomes_ativos, "Mínimo Risco")
    # Gráfico de barras removido daqui

    # ANÁLISE 2: Portfólio de MÁXIMO RETORNO
    portifolio_max_retorno = df_resultados.loc[df_resultados['Retorno_Anual'].idxmax()]

    print("\n====================================================================")
    print("              ANÁLISE 2: PORTFÓLIO DE MÁXIMO RETORNO")
    print("         (Foco exclusivo no maior retorno esperado possível)")
    print("====================================================================")
    print(f"  Retorno Esperado:   {portifolio_max_retorno['Retorno_Anual']:.2%}")
    print(f"  Risco (Variância):  {portifolio_max_retorno['Risco_Anual']:.4f}")
    print(f"  Volatilidade (Desvio Padrão): {portifolio_max_retorno['Risco_StDev']:.2%}")
    print(f"  Índice Sharpe:      {portifolio_max_retorno['Sharpe_Ratio']:.2f}")
    formatar_portifolio_para_print(portifolio_max_retorno, nomes_ativos, "Máximo Retorno")
    # Gráfico de barras removido daqui

    # ANÁLISE 3: Portfólio de MELHOR CUSTO-BENEFÍCIO (Sharpe Máx)
    portifolio_max_sharpe = df_resultados.loc[df_resultados['Sharpe_Ratio'].idxmax()]

    print("\n====================================================================")
    print("       ANÁLISE 3: PORTFÓLIO DE MELHOR CUSTO-BENEFÍCIO (SHARPE)")
    print("       (Onde o retorno justifica melhor o risco assumido)")
    print("====================================================================")
    print(f"  Retorno Esperado:   {portifolio_max_sharpe['Retorno_Anual']:.2%}")
    print(f"  Risco (Variância):  {portifolio_max_sharpe['Risco_Anual']:.4f}")
    print(f"  Volatilidade (Desvio Padrão): {portifolio_max_sharpe['Risco_StDev']:.2%}")
    print(f"  Índice Sharpe:      {portifolio_max_sharpe['Sharpe_Ratio']:.2f} (O MAIOR)")
    formatar_portifolio_para_print(portifolio_max_sharpe, nomes_ativos, "Máximo Sharpe")
    # --- NOVO: Chamada para o gráfico de pizza ---
    plotar_distribuicao_pizza(portifolio_max_sharpe, "Melhor Custo-Benefício (Sharpe)", ARQUIVO_PIZZA_FINAL_PNG)
    print("====================================================================")

    # --- PASSO 5: Plotar o Gráfico da Fronteira de Pareto ---
    print("\nGerando gráfico da Fronteira de Pareto...")
    
    volatilidades = df_resultados['Risco_StDev']
    retornos = df_resultados['Retorno_Anual']
    
    plt.figure(figsize=(12, 8))
    plt.scatter(volatilidades, retornos, s=15, facecolors='none', edgecolors='blue', label='Portfólios Ótimos')
    
    plt.scatter(portifolio_min_risco['Risco_StDev'], portifolio_min_risco['Retorno_Anual'], 
                c='red', s=70, label='Mínimo Risco (PMV)', zorder=5)
    
    plt.scatter(portifolio_max_retorno['Risco_StDev'], portifolio_max_retorno['Retorno_Anual'], 
                c='green', s=70, label='Máximo Retorno', zorder=5)
    
    plt.scatter(portifolio_max_sharpe['Risco_StDev'], portifolio_max_sharpe['Retorno_Anual'], 
                c='gold', s=150, label='Melhor Custo-Benefício (Sharpe)', marker='*', zorder=5, edgecolors='black')
    
    plt.title("Fronteira de Pareto: Otimização de Portfólio (NSGA-II)", fontsize=16)
    plt.xlabel("Risco (Volatilidade Anualizada - Desvio Padrão)", fontsize=12)
    plt.ylabel("Retorno Esperado (Anualizado)", fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    plt.text(0.98, 0.02, f"Valor Total Investido: R$ {config.VALOR_TOTAL_INVESTIMENTO:,.2f}",
             transform=plt.gca().transAxes,
             horizontalalignment='right',
             verticalalignment='bottom',
             fontsize=10,
             bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7))
             
    plt.savefig(ARQUIVO_FRONTEIRA_PNG, dpi=300) # Salva o gráfico principal!
    print(f"Gráfico da Fronteira de Pareto salvo como '{ARQUIVO_FRONTEIRA_PNG}'")
    
    # --- ALTERAÇÃO: 'plt.show()' foi removido ---
    # plt.show() 
    
    print("\n--- ANÁLISE E VISUALIZAÇÃO CONCLUÍDAS ---")
    print("Dois arquivos PNG foram gerados na pasta do projeto.")