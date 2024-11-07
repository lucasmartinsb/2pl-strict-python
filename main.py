from Escalonador import Escalonador        
import os 

if __name__ == '__main__':
    escolha = None
    personaliada = ""
    while not escolha:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Selecione uma transação de exemplo")
        print("""               0. Personalizar
               1. Sem conflitos:  s1 r1[x] s2 r1[y] w1[x,20] r2[y] c1 w2[x,10] c2
               2. Com delay:      s1 r1[x] w1[x,10] s2 w2[x,15] c1 c2
               3. Com deadlock:   s1 s2 r1[x] w2[y,10] r1[y] w2[x,20] c1 c2
               4. Erro de commit: s1 s2 r1[x] r2[y] r1[y] c1 r1[x] w2[x,10] c2
               5. Erro de start:  r1[x]""")
        escolha = input("               ")
        if escolha not in ['0', '1', '2', '3', '4', '5']:
            escolha = None
            print("Opção inválida")
        if escolha == '0':
            personaliada = input("Digite sua HI: ")
    
    opcoes_historia = {
        '0' : personaliada,
        '1' : "s1 r1[x] s2 r1[y] w1[x,20] r2[y] c1 w2[x,10] c2",
        '2' : "s1 r1[x] w1[x,10] s2 w2[x,15] c1 c2",
        '3' : "s1 s2 r1[x] w2[y,10] r1[y] w2[x,20] c1 c2",
        '4' : "s1 s2 r1[x] r2[y] r1[y] c1 r1[x] w2[x,10] c2",
        '5' : "r1[x]"
    }

    esclaonador = Escalonador(opcoes_historia[escolha])
    esclaonador.executor()