"""
================================================
ARQUIVO DE MODELAGEM DO PROBLEMA (Req. 5)
================================================

Este arquivo é a tradução literal do modelo matemático
do trabalho para o Python.

As Funções Objetivo e Restrições são definidas
explicitamente abaixo para fins de clareza acadêmica.
"""

import numpy as np
from pymoo.core.problem import Problem

class OtimizacaoPortfolio(Problem):
    """
    Esta classe define o problema de Otimização Multiobjetivo
    de Portfólio (Média-Variância).
    """

    def __init__(self, retornos_medios, matriz_cov):
        """
        Inicializa o problema de otimização, definindo os
        limites e a dimensionalidade do problema.
        """
        
        # --- Parâmetros de Entrada ---
        # (μ e Σ recebidos do preparar_dados.py)
        self.retornos_medios = retornos_medios
        self.matriz_cov = matriz_cov
        
        # --- Variáveis de Decisão ---
        # O vetor 'w' (pesos), de tamanho N
        n_ativos = len(retornos_medios)
        
        
        # --- Definição Formal do Problema para o Pymoo ---
        super().__init__(
            
            # n_var = N (Número de variáveis de decisão)
            # (O algoritmo deve encontrar N pesos, w_1, w_2, ..., w_N)
            n_var=n_ativos,       
            
            # n_obj = 2 (Número de Funções Objetivo)
            # (OBJETIVO 1: Minimizar Risco)
            # (OBJETIVO 2: Maximizar Retorno)
            n_obj=2,              
            
            # n_eq_constr = 1 (Número de Restrições de IGUALDADE)
            # (Aqui definimos que teremos 1 restrição que deve ser = 0)
            # (Esta será a nossa RESTRICAO 1)
            n_eq_constr=1,        
            
            # --- Definição Direta de Restrições de Limite ---
            
            # RESTRICAO 2: Limite Inferior (w_i >= 0)
            # // NÃO PERMITIR VENDA A DESCOBERTO (SHORT SELLING)
            # Dizemos ao Pymoo que nenhuma variável w_i pode ser < 0.
            xl=0.0,               
            
            # Restrição Bônus: Limite Superior (w_i <= 1)
            # // NÃO INVESTIR MAIS DE 100% EM UM ÚNICO ATIVO
            xu=1.0                
        )

    def _evaluate(self, x, out, *args, **kwargs):
        """
        Esta é a função de avaliação.
        Aqui calculamos explicitamente os objetivos e restrições
        para cada portfólio 'w' (cada linha da matriz 'x').
        """
        
        # --- ================================== ---
        # --- DEFINIÇÃO DAS FUNÇÕES OBJETIVO ---
        # --- ================================== ---
        
        # OBJETIVO 1: Minimizar o Risco (Variância)
        # Fórmula: Minimizar V(w) = w^T * Σ * w
        obj_risco = np.einsum('ij,jk,ik->i', x, self.matriz_cov, x)
        
        
        # OBJETIVO 2: Maximizar o Retorno
        # Fórmula: Maximizar R(w) = w^T * μ
        #
        # O Pymoo, por padrão, só MINIMIZA.
        # A solução é minimizar o *negativo* do retorno.
        # (Maximizar X) == (Minimizar -X)
        retorno_calculado = x.dot(self.retornos_medios)
        obj_retorno_negativo = -retorno_calculado
        
        
        # --- ============================== ---
        # --- DEFINIÇÃO DAS RESTRIÇÕES ---
        # --- ============================== ---
        
        # RESTRICAO 1: Soma dos Pesos = 1
        # // INVESTIR TODO O CAPITAL, NEM MAIS, NEM MENOS
        #
        # O Pymoo espera que restrições de igualdade sejam = 0.
        # Fórmula: (Soma(w_i)) - 1 = 0
        restricao_soma_pesos = np.sum(x, axis=1) - 1.0
        
        
        # RESTRICAO 2: Não-Negatividade (w_i >= 0)
        # // NÃO PERMITIR VENDA A DESCOBERTO
        #
        # Como explicamos no __init__, esta restrição já foi
        # definida como um LIMITE (bound) 'xl=0.0'.
        # O Pymoo lida com ela automaticamente e de forma
        # muito eficiente, não sendo necessário calculá-la aqui.


        # --- ======================================== ---
        # --- Envio dos Resultados para o Otimizador ---
        # --- ======================================== ---
        
        # Envia os valores dos OBJETIVOS
        # Coluna 0: Risco
        # Coluna 1: Retorno (Negativo)
        out["F"] = np.column_stack([
            obj_risco, 
            obj_retorno_negativo
        ])
        
        # Envia os valores das RESTRIÇÕES DE IGUALDADE
        # (O Pymoo tentará forçar estes valores a zero)
        out["H"] = np.column_stack([
            restricao_soma_pesos
        ])

# --- Bloco de Teste ---
if __name__ == '__main__':
    print("Este arquivo ('modelo_problema.py') define a classe do problema.")
    print("Ele não deve ser executado diretamente.")