"""
================================================
ARQUIVO "CÉREBRO": EXECUTOR DA OTIMIZAÇÃO (Req. 3 e 4)
================================================

Este script é o "orquestrador" principal do projeto.
Ele não define o problema nem plota gráficos.

Seu trabalho é:
1. Importar os dados de 'preparar_dados.py'.
2. Importar o modelo matemático de 'modelo_problema.py'.
3. Configurar e EXECUTAR o algoritmo de otimização (NSGA-II).
4. Salvar os resultados (a Fronteira de Pareto completa)
   em um arquivo CSV para análise posterior.
"""

import pandas as pd
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize

# --- 1. IMPORTAR NOSSOS MÓDULOS ---
import preparar_dados
import modelo_problema

# --- 2. CONSTANTES DE EXECUÇÃO ---
ARQUIVO_SAIDA_CSV = 'resultados_otimizacao.csv'

# Parâmetros do Algoritmo Genético
POPULACAO_SIZE = 150 # Nº de portfólios testados por geração
NUM_GERACOES = 200   # Nº de gerações (iterações)


# --- 3. BLOCO DE EXECUÇÃO PRINCIPAL ---
if __name__ == '__main__':
    
    print("--- INICIANDO EXECUTOR DE OTIMIZAÇÃO ---")
    
    # --- PASSO 1: Obter Dados ---
    print("\n[PASSO 1/4] Carregando e preparando dados de entrada...")
    # Chama a função principal do nosso outro arquivo
    inputs = preparar_dados.calcular_inputs_otimizacao()
    
    if inputs is None:
        print("Erro fatal: Falha ao carregar os dados. Encerrando.")
    else:
        # Desempacotar os inputs
        retornos_medios = inputs['retornos_medios']
        matriz_cov = inputs['matriz_cov']
        nomes_dos_ativos = inputs['nomes_dos_ativos']
        
        # --- PASSO 2: Instanciar o Problema ---
        print("\n[PASSO 2/4] Instanciando o modelo matemático (Fórmulas)...")
        # Instancia a classe que definimos no 'modelo_problema.py'
        problema = modelo_problema.OtimizacaoPortfolio(
            retornos_medios,
            matriz_cov
        )
        
        # --- PASSO 3: Configurar o Algoritmo ---
        print("\n[PASSO 3/4] Configurando o algoritmo de otimização (NSGA-II)...")
        algoritmo = NSGA2(
            pop_size=POPULACAO_SIZE,
            eliminate_duplicates=True
        )
        
        # --- PASSO 4: Executar a Otimização ---
        print(f"\n[PASSO 4/4] Executando a otimização... ({NUM_GERACOES} gerações)")
        # Esta é a linha que faz o "trabalho pesado"
        res = minimize(
            problema,
            algoritmo,
            ('n_gen', NUM_GERACOES), # Critério de parada
            seed=1,                 # Para resultados reprodutíveis
            verbose=True            # Mostrar o progresso (gen: 1, 2, ...)
        )
        
        print("\n--- Otimização Concluída ---")
        
        # --- PASSO 5: Salvar Resultados (Req. 4) ---
        if res.F is not None and res.X is not None:
            print(f"Otimização encontrou {len(res.F)} soluções ótimas.")
            print(f"Processando e salvando resultados em '{ARQUIVO_SAIDA_CSV}'...")
            
            # res.F -> Contém os OBJETIVOS (Coluna 0: Risco, Coluna 1: -Retorno)
            # res.X -> Contém as VARIÁVEIS (Os pesos 'w' de cada portfólio)
            
            # Obter objetivos e inverter o retorno para positivo
            riscos = res.F[:, 0]
            retornos = -res.F[:, 1]
            
            # Obter os pesos
            pesos_matrix = res.X
            
            # Criar DataFrames
            df_objetivos = pd.DataFrame({
                'Risco_Anual': riscos,
                'Retorno_Anual': retornos
            })
            
            # Criar colunas de pesos com nomes (ex: 'w_PETR4.SA')
            colunas_pesos = [f'w_{nome}' for nome in nomes_dos_ativos]
            df_pesos = pd.DataFrame(pesos_matrix, columns=colunas_pesos)
            
            # Combinar tudo em um único DataFrame
            df_resultados = pd.concat([df_objetivos, df_pesos], axis=1)
            
            # Ordenar do menor risco para o maior
            df_resultados = df_resultados.sort_values(by='Risco_Anual').reset_index(drop=True)
            
            # Salvar em CSV (formato ; para compatibilidade com Excel-BR)
            try:
                df_resultados.to_csv(ARQUIVO_SAIDA_CSV, index=False, sep=';', decimal=',')
                print(f"Sucesso! Resultados salvos em '{ARQUIVO_SAIDA_CSV}'.")
                print("\nPróximo passo: execute 'visualizar.py' para ver os gráficos.")
            except Exception as e:
                print(f"Erro ao salvar o arquivo CSV: {e}")
                
        else:
            print("Otimização falhou e não encontrou soluções viáveis.")