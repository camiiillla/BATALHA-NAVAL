# jogador11202521628.py
# RA: 11202521628

import random
from copy import deepcopy

# ============================================================================
# CLASSES E FUNÇÕES AUXILIARES (copiadas da API para tornar o arquivo independente)
# ============================================================================

# Tipos
Coordenada = tuple[int, int]
Direcao = tuple[int, int]

def next_coordenada(coordenada: Coordenada, direcao: Direcao) -> Coordenada:
    """Retorna a próxima coordenada na direção especificada."""
    return (coordenada[0] + direcao[0], coordenada[1] + direcao[1])


class Navio:
    """Representa um navio no jogo."""
    
    def __init__(self, comprimento: int, coordenada: Coordenada, direcao: Direcao):
        self.lista_impacto = ['I'] * comprimento
        self.coordenada = coordenada
        self.direcao = direcao


def navio_afundado(navio: Navio) -> str:
    """Retorna '*' se o navio estiver completamente destruído, 'N' caso contrário."""
    return '*' if all(impacto == 'A' for impacto in navio.lista_impacto) else 'N'


def navio_impacto(navio: Navio, coordenada_do_tiro: Coordenada) -> str:
    """Verifica se o tiro acertou o navio e atualiza seu estado."""
    coordenada_atual = navio.coordenada
    indice = 0
    while indice < len(navio.lista_impacto):
        if coordenada_atual == coordenada_do_tiro:
            navio.lista_impacto[indice] = 'A'
            return navio_afundado(navio)
        indice += 1
        coordenada_atual = next_coordenada(coordenada_atual, navio.direcao)
    return 'A'


class Frota:
    """Representa uma coleção de navios."""
    
    def __init__(self):
        self.navios = []
    
    def recebe_tiro(self, coordenada: Coordenada) -> str:
        """Processa um tiro recebido, verificando se acertou algum navio."""
        for navio in self.navios:
            resultado = navio_impacto(navio, coordenada)
            if resultado != 'A':
                return resultado
        return 'A'
    
    def frota_afundou(self) -> bool:
        """Verifica se todos os navios da frota foram afundados."""
        return all(navio_afundado(navio) == '*' for navio in self.navios)
    
    def zera_frota(self):
        """Remove todos os navios da frota."""
        self.navios.clear()
    
    def adiciona_navio(self, coordenada: Coordenada, comprimento: int, direcao: Direcao):
        """Adiciona um novo navio à frota."""
        self.navios.append(Navio(comprimento, coordenada, direcao))


# ============================================================================
# CLASSE JOGADOR (implementação principal)
# ============================================================================

class Jogador:
    """
    Classe que representa um jogador de Batalha Naval.
    Atende à API especificada no projeto.
    RA: 11202521628
    """
    
    def __init__(self, apelido: str, nome: str, ra: str):
        self.minha_frota = Frota()
        self.apelido = apelido
        self.nome = nome
        self.ra = ra
        # Tabuleiro de controle dos tiros efetuados (para estratégia de tiro)
        self._tabuleiro_tiros = [['D' for _ in range(10)] for _ in range(10)]
        # Lista de tiros pendentes para quando acertamos um navio
        self._tiros_pendentes = []
    
    def atira(self) -> Coordenada:
        """
        Retorna uma coordenada para o próximo tiro.
        Estratégia melhorada: 
        1. Se há tiros pendentes (navio foi atingido), atira nas adjacências
        2. Caso contrário, atira em posições ainda não exploradas (padrão xadrez)
        """
        # Prioridade: completar navios já atingidos
        if self._tiros_pendentes:
            return self._tiros_pendentes.pop(0)
        
        # Estratégia de busca em padrão xadrez (mais eficiente)
        disponiveis = []
        for i in range(10):
            for j in range(10):
                if self._tabuleiro_tiros[i][j] == 'D':
                    # Padrão xadrez: atira apenas em (i+j) par ou ímpar
                    if (i + j) % 2 == 0:
                        disponiveis.append((i, j))
        
        # Se não houver disponíveis no padrão, pega todos os disponíveis
        if not disponiveis:
            disponiveis = [(i, j) for i in range(10) for j in range(10) 
                          if self._tabuleiro_tiros[i][j] == 'D']
        
        if disponiveis:
            return random.choice(disponiveis)
        else:
            return (random.randint(0, 9), random.randint(0, 9))
    
    def recebe_tiro(self, coordenada: Coordenada) -> str:
        """
        Recebe um tiro do adversário e retorna o resultado:
        'A' para água, 'N' para navio atingido, '*' para navio afundado.
        """
        return self.minha_frota.recebe_tiro(coordenada)
    
    def resultado_tiro(self, coordenada: Coordenada, resultado: str):
        """
        Informa ao jogador o resultado do tiro que ele efetuou.
        Atualiza o tabuleiro interno de controle de tiros e planeja próximos tiros.
        """
        i, j = coordenada
        
        if resultado == 'A':
            self._tabuleiro_tiros[i][j] = 'A'
        elif resultado == 'N':  # Navio atingido, mas não afundado
            self._tabuleiro_tiros[i][j] = 'N'
            # Adiciona posições adjacentes para investigar
            self._adicionar_adjacentes(i, j)
        elif resultado == '*':  # Navio afundado
            self._tabuleiro_tiros[i][j] = 'N'
            # Limpa tiros pendentes, pois o navio já foi destruído
            self._tiros_pendentes.clear()
            # Marca todas as casas ao redor do navio como água
            self._marcar_entorno_navio_afundado()
    
    def _adicionar_adjacentes(self, linha: int, coluna: int):
        """
        Adiciona coordenadas adjacentes (cima, baixo, esquerda, direita)
        à lista de tiros pendentes para continuar atirando no navio.
        """
        adjacentes = []
        for dl, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nl, nc = linha + dl, coluna + dc
            if (0 <= nl < 10 and 0 <= nc < 10 and 
                self._tabuleiro_tiros[nl][nc] == 'D'):
                adjacentes.append((nl, nc))
        
        # Adiciona ao início da lista para prioridade
        self._tiros_pendentes = adjacentes + self._tiros_pendentes
    
    def _marcar_entorno_navio_afundado(self):
        """
        Quando um navio é afundado, todas as casas adjacentes (incluindo diagonais)
        são água, pois navios não podem se tocar.
        """
        # Encontra todas as partes do navio recém-afundado
        for i in range(10):
            for j in range(10):
                if self._tabuleiro_tiros[i][j] == 'N':
                    # Verifica se há 'D's adjacentes que agora sabemos ser água
                    for dl in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            nl, nc = i + dl, j + dc
                            if (0 <= nl < 10 and 0 <= nc < 10 and 
                                self._tabuleiro_tiros[nl][nc] == 'D'):
                                # Não marcamos como 'A' para poder atirar se quiser,
                                # mas removemos dos pendentes
                                if (nl, nc) in self._tiros_pendentes:
                                    self._tiros_pendentes.remove((nl, nc))
    
    def inicio_de_jogo(self) -> Frota:
        """
        Prepara a frota para um novo jogo:
        - Remove todos os navios existentes.
        - Posiciona 3 navios de comprimento 2, 1 de 4 e 1 de 5.
        - Garante que navios não se tocam (nem ortogonal, nem diagonalmente).
        - Retorna uma cópia profunda da frota.
        """
        self.minha_frota.zera_frota()
        self._tabuleiro_tiros = [['D' for _ in range(10)] for _ in range(10)]
        self._tiros_pendentes = []
        
        comprimentos = [2, 2, 2, 4, 5]
        tentativas_max = 500
        
        for comp in comprimentos:
            posicionado = False
            for _ in range(tentativas_max):
                # Gera posição e direção aleatórias
                direcao = random.choice([(1, 0), (0, 1)])
                if direcao == (1, 0):  # vertical
                    linha = random.randint(0, 10 - comp)
                    coluna = random.randint(0, 9)
                else:  # horizontal
                    linha = random.randint(0, 9)
                    coluna = random.randint(0, 10 - comp)
                
                coordenada_inicial = (linha, coluna)
                
                if self._posicao_valida(comp, coordenada_inicial, direcao):
                    self.minha_frota.adiciona_navio(coordenada_inicial, comp, direcao)
                    posicionado = True
                    break
            
            if not posicionado:
                # Se não conseguiu posicionar, recomeça
                return self.inicio_de_jogo()
        
        # Garante que todos os navios tenham lista_impacto com 'I'
        for navio in self.minha_frota.navios:
            navio.lista_impacto = ['I'] * len(navio.lista_impacto)
        
        return deepcopy(self.minha_frota)
    
    def _posicao_valida(self, comprimento: int, coord: Coordenada, direcao: Direcao) -> bool:
        """
        Verifica se um navio pode ser posicionado sem sair do tabuleiro
        e sem encostar em nenhum navio já existente.
        """
        # 1. Verifica limites do tabuleiro
        partes = []
        linha, coluna = coord
        for i in range(comprimento):
            if not (0 <= linha < 10 and 0 <= coluna < 10):
                return False
            partes.append((linha, coluna))
            linha += direcao[0]
            coluna += direcao[1]
        
        # 2. Verifica vizinhança (incluindo diagonais)
        for l, c in partes:
            for dl in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nl, nc = l + dl, c + dc
                    if 0 <= nl < 10 and 0 <= nc < 10:
                        if self._existe_navio_em(nl, nc):
                            return False
        return True
    
    def _existe_navio_em(self, linha: int, coluna: int) -> bool:
        """
        Retorna True se a coordenada pertence a algum navio já posicionado.
        """
        for navio in self.minha_frota.navios:
            l, c = navio.coordenada
            for _ in range(len(navio.lista_impacto)):
                if (l, c) == (linha, coluna):
                    return True
                l += navio.direcao[0]
                c += navio.direcao[1]
        return False  