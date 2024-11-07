from Operacao import Operacao
from tabulate import tabulate
import os

class Escalonador:
    def __init__(self, HI: str):
        self.HI = HI
        self.tabela_lock = []
        self.transacoes_status = {}
        self.operacoes = []
        self.operacoes_final = []
        self.processa_operacoes()

    def processa_operacoes(self):
        operacoes = self.HI.split()
        variaveis = set()
        transacoes = set()

        # Cria tabela de operações
        for operacao in operacoes:
            variavel = None
            valor = None
            tipo_operacao = operacao[0]  # r, w, c ou s
            id_transacao = operacao[1]   # ID da transação
            transacoes.add(id_transacao)
            
            if tipo_operacao == 'r':
                variavel = operacao[3:-1]
                variaveis.add(variavel)

            if tipo_operacao == 'w':
                variavel, valor = operacao[3:-1].split(",")
                variaveis.add(variavel) 
            
            self.operacoes.append(Operacao(tipo_operacao=tipo_operacao, id_transacao=id_transacao, status="Pendente", variavel=variavel, valor=valor))
        
        for variavel in variaveis:
            self.tabela_lock.append({'var': variavel, 'valor': 0, 'ls': [], 'lx': None}) 
        
        for transacao in transacoes:
            self.transacoes_status[transacao] = 'Não iniciada'
    
    def executor(self):
        while self.mais_operacoes():
            for i in range(len(self.operacoes)):
                # Só precisa clicar se não foi uma operação que já foi executada (casos delayed)
                if self.operacoes[i].status != 'Ok' and i>0:
                    input()
                try:
                    self.executa_operacao(operacao_index=i)
                except Exception as e:
                    print(e)
                    return
                self.print_tabelas()
                operacoes_deadlock = self.operacoes_deadlock()
                if len(operacoes_deadlock)>1:
                    print(f"DEADLOCK: {' '.join(str(operacao) for operacao in operacoes_deadlock)}")
                    self.trata_deadlock(operacoes_deadlock=operacoes_deadlock)
                    break

    def executa_operacao(self, operacao_index: int):
        operacao = self.operacoes[operacao_index]

        if operacao.status == 'Ok':
            return
        
        if self.transacoes_status[operacao.id_transacao] == 'Não iniciada':
            if operacao.tipo_operacao == 's':
                self.operacoes[operacao_index].status = 'Ok'
                self.transacoes_status[operacao.id_transacao] = 'Iniciada'
                self.operacoes_final.append(operacao)
                return
            else:
                raise Exception(f"Erro de input: Transação {operacao.id_transacao} não iniciada")
        
        if self.transacoes_status[operacao.id_transacao] == 'Finalizada':
            raise Exception(f"Erro de input: Transação {operacao.id_transacao} já finalizada")

        elif self.transacoes_status[operacao.id_transacao] == 'Iniciada' or self.transacoes_status[operacao.id_transacao] == 'Delayed':
            if operacao.tipo_operacao == 'c' and self.transacoes_status[operacao.id_transacao] != 'Delayed':
                self.operacoes[operacao_index].status = 'Ok'
                self.transacoes_status[operacao.id_transacao] = 'Finalizada'
                self.operacoes_final.append(operacao)
                self.desbloqueia_por_transacao(operacao.id_transacao)
                return
            
            elif operacao.tipo_operacao == 'r':
                lock_variavel_index = self.localiza_variavel_tabela_lock(variavel_buscada=operacao.variavel)
                lock_variavel = self.tabela_lock[lock_variavel_index]
                if lock_variavel['lx'] is None:
                    self.operacoes[operacao_index].status = 'Ok'
                    self.lock_transacao(variavel_index=lock_variavel_index, tipo_lock='s', id_transacao=operacao.id_transacao, valor=None)
                    self.operacoes_final.append(operacao)
                    self.transacoes_status[operacao.id_transacao] = 'Iniciada'
                    return
                else:
                    self.delay_operacao(operacao_index=operacao_index, id_transacao=operacao.id_transacao)
            
            elif operacao.tipo_operacao == 'w':
                lock_variavel_index = self.localiza_variavel_tabela_lock(variavel_buscada=operacao.variavel)
                lock_variavel = self.tabela_lock[lock_variavel_index]
                
                # Nenhum lock ou somente ele já estava no lx
                if     (lock_variavel['lx'] is None and len(lock_variavel['ls']) == 0) \
                    or (lock_variavel['lx'] == operacao.id_transacao):
                    self.operacoes[operacao_index].status = 'Ok'
                    self.lock_transacao(variavel_index=lock_variavel_index, tipo_lock='x', id_transacao=operacao.id_transacao, valor=operacao.valor)
                    self.operacoes_final.append(operacao)
                    self.transacoes_status[operacao.id_transacao] = 'Iniciada'
                    return
                
                # Upgrade (somente ele no ls)
                elif (lock_variavel['ls'] == [operacao.id_transacao]):
                    self.operacoes[operacao_index].status = 'Ok'
                    self.updgrade_lock(transacao=operacao.id_transacao, variavel_index=lock_variavel_index, id_transacao=operacao.id_transacao, valor=operacao.valor )
                    self.operacoes_final.append(operacao)
                
                else:
                    self.delay_operacao(operacao_index=operacao_index, id_transacao=operacao.id_transacao)
                    
    def delay_operacao(self, operacao_index : str, id_transacao : str):
        self.operacoes[operacao_index].status = 'Delayed'
        self.operacoes[operacao_index].tentativas += 1
        self.transacoes_status[id_transacao] = 'Delayed'

    def localiza_variavel_tabela_lock(self, variavel_buscada: str) -> int:
        for i in range(0, len(self.tabela_lock)):
            if self.tabela_lock[i]['var'] == variavel_buscada:
                return i
    
    def lock_transacao(self, variavel_index : str, tipo_lock : str, id_transacao : str, valor : str = None):
        lock_variavel = self.tabela_lock[variavel_index]
        if tipo_lock == 's':
            self.tabela_lock[variavel_index][f'l{tipo_lock}'].append(id_transacao)
        elif tipo_lock == 'x':
            self.tabela_lock[variavel_index][f'l{tipo_lock}'] = id_transacao
        self.operacoes_final.append(Operacao(tipo_operacao='l', id_transacao=id_transacao, variavel=lock_variavel['var'], valor=tipo_lock))
        if tipo_lock == 'x':
            # Se é lx tem valor
            self.tabela_lock[variavel_index]['valor'] = valor
    
    def updgrade_lock(self, transacao : str, variavel_index : str, id_transacao : str, valor : str):
        self.tabela_lock[variavel_index]['lx'] = id_transacao
        self.tabela_lock[variavel_index]['ls'].remove(id_transacao)
        for i in range(0, len(self.operacoes_final)):
            if self.operacoes_final[i].tipo_operacao == 'l' and self.operacoes_final[i].id_transacao == transacao and self.operacoes_final[i].valor == 's':
                self.operacoes_final[i].valor = 'x'
        self.tabela_lock[variavel_index]['valor'] = valor

    def desbloqueia_por_transacao(self, transacao_buscada : str):
        for i in range(0, len(self.tabela_lock)):
            if transacao_buscada in self.tabela_lock[i]['ls']:
                self.operacoes_final.append(Operacao(tipo_operacao='u',id_transacao=transacao_buscada, variavel=self.tabela_lock[i]['var'], valor='s'))
                self.tabela_lock[i]['ls'].remove(transacao_buscada)
            elif self.tabela_lock[i]['lx'] == transacao_buscada:
                self.operacoes_final.append(Operacao(tipo_operacao='u',id_transacao=transacao_buscada, variavel=self.tabela_lock[i]['var'], valor='x'))
                self.tabela_lock[i]['lx'] = None
    
    def mais_operacoes(self) -> bool:
        for operacao in self.operacoes:
            if operacao.status != 'Ok':
                return True
        return False

    def operacoes_deadlock(self) -> list:
        operacoes_deadlock = []
        for operacao in self.operacoes:
            if operacao.tentativas > 2:
                operacoes_deadlock.append(operacao)
        return operacoes_deadlock
    
    def trata_deadlock(self, operacoes_deadlock : list):
        input()
        transacao_movida = operacoes_deadlock[1].id_transacao # Pega segunda transação do deadlock
        self.move_transacoes_fim(transacao_movida=transacao_movida)
        self.desbloqueia_por_transacao(transacao_buscada=transacao_movida)
        self.remove_transacao_hf(transacao_removida=transacao_movida)
        self.reinicia_operacoes(transacao_reiniciada=transacao_movida)       
        self.transacoes_status[transacao_movida] = 'Não iniciada' 

    def move_transacoes_fim(self, transacao_movida : str):
        # Move todas operações dessa transação pro final
        operacoes_movidas = [op for op in self.operacoes if op.id_transacao == transacao_movida]
        operacoes_restantes = [op for op in self.operacoes if op.id_transacao != transacao_movida]
        self.operacoes[:] = operacoes_restantes + operacoes_movidas 
    
    def reinicia_operacoes(self, transacao_reiniciada : str):
        for i in range(0, len(self.operacoes)):
            if self.operacoes[i].id_transacao == transacao_reiniciada:
                self.operacoes[i].status = 'Pendente'
                self.operacoes[i].tentativas = 0
                if self.operacoes[i].tipo_operacao == 'w':
                    porcao_operacoes = self.operacoes[:i-1]
                    self.reseta_valor_variavel(porcao_operacoes=porcao_operacoes, id_transacao=self.operacoes[i].id_transacao, variavel=self.operacoes[i].variavel)

    def reseta_valor_variavel(self, porcao_operacoes: list, id_transacao : str, variavel : str):
        operacoes_invertida = list(reversed(porcao_operacoes))
        valor_revertido = None
        for operacao in operacoes_invertida:
            # Se é uma operação de escrita na mesma variável, de outra transação e antes da operação que deve ser revertida 
            if operacao.tipo_operacao == 'w' and operacao.variavel == variavel and operacao.id_transacao != id_transacao:
                valor_revertido = operacao.valor
                break
        index_variavel_tabela_lock = self.localiza_variavel_tabela_lock(variavel_buscada=variavel)
        if valor_revertido:
            self.tabela_lock[index_variavel_tabela_lock] = valor_revertido
        else:
            self.tabela_lock[index_variavel_tabela_lock]['valor'] = 0

    def remove_transacao_hf(self, transacao_removida : str):
        self.operacoes_final = [op for op in self.operacoes_final if op.id_transacao != transacao_removida]

    def print_tabelas(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        # Convertendo dados de locks e operações para tabelas
        lock_table = tabulate(self.tabela_lock, headers="keys", tablefmt="pretty")
        operacoes_dict = [operacao.__dict__ for operacao in self.operacoes]
        operacoes_table = tabulate(operacoes_dict, headers="keys", tablefmt="pretty")
        transacoes_format = [[transacao, status] for transacao, status in self.transacoes_status.items()]
        transacoes_table = tabulate(transacoes_format, headers=["Transação", "Status"], tablefmt="pretty")
        # Imprimindo as tabelas na tela
        print(f"Tabela de transações\n{transacoes_table}\n\n")
        print(f"Tabela de locks\n{lock_table}\n\n")
        print(f"Tabela de operações\n{operacoes_table}\n\n")
        print(f"HI: {self.HI} \nHF: {' '.join(str(operacao) for operacao in self.operacoes_final)}")