class Operacao:
    def __init__(self, tipo_operacao: str, id_transacao: str, status: str = None, variavel: str = None, valor: str = None):
        self.tipo_operacao = tipo_operacao
        self.id_transacao = id_transacao
        self.variavel = variavel
        self.valor = valor
        self.status = status
        self.tentativas = 0

    def __str__(self):
        if self.tipo_operacao in ['s', 'c']:
            return f"{self.tipo_operacao}{self.id_transacao}"
        elif self.tipo_operacao == 'r':
            return f"{self.tipo_operacao}{self.id_transacao}[{self.variavel}]"
        elif self.tipo_operacao == 'w':
            return f"{self.tipo_operacao}{self.id_transacao}[{self.variavel},{self.valor}]"
        elif self.tipo_operacao in ['l', 'u']:
            return f"{self.tipo_operacao}{self.valor}{self.id_transacao}[{self.variavel}]"