# batalha_naval_final.py
# RA: 11202521628
# Versao Final - Agua some com navio/explosao + Menu de pausa + X vermelho na agua + Sons Game Over e Vitoria
# CORRIGIDO: Usa caminhos relativos para funcionar em qualquer dispositivo

import pygame
import sys
import random
import math
import os
from enum import Enum
from typing import List, Tuple, Optional

# Inicializacao do Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

# ============================================================================
# CONFIGURACOES
# ============================================================================

class Config:
    # Tela
    LARGURA = 1300
    ALTURA = 750
    FPS = 60
    
    # Cores tema naval
    AZUL_PROFUNDO = (5, 15, 30)
    AZUL_MARINHO = (10, 30, 50)
    AZUL_MEDIO = (25, 60, 100)
    AZUL_CLARO = (64, 164, 223)
    BRANCO = (255, 255, 255)
    CINZA_CLARO = (200, 200, 200)
    CINZA = (128, 128, 128)
    CINZA_ESCURO = (60, 60, 60)
    VERMELHO = (255, 50, 50)
    VERMELHO_ESCURO = (180, 30, 30)
    VERDE = (50, 255, 50)
    VERDE_ESCURO = (30, 180, 30)
    AMARELO = (255, 255, 50)
    LARANJA = (255, 150, 50)
    PRETO = (0, 0, 0)
    ROXO = (150, 50, 255)
    DOURADO = (255, 215, 0)
    
    # Tabuleiro
    CELULA_TAMANHO = 42
    TABULEIRO_X = 60
    TABULEIRO_Y = 220
    TABULEIRO_INIMIGO_X = 730
    
    # Posicionamento do tabuleiro no menu (centralizado)
    POSICIONAMENTO_Y = 250
    
    # Espaçamentos (em pixels)
    ESPACO_TITULO_TURNO = 75
    TITULO_Y = 25
    TITULO_Y_AJUSTADO = TITULO_Y + 10
    
    # Cores das celulas (fallback)
    COR_AGUA = (64, 164, 223)
    COR_NAVIO = (80, 80, 100)
    COR_ACERTO = (255, 80, 80)
    COR_ERRO = (100, 150, 200)
    COR_DESCONHECIDO = (30, 80, 120)


# ============================================================================
# FUNCOES AUXILIARES PARA CAMINHOS RELATIVOS
# ============================================================================

def get_base_path() -> str:
    """Retorna o caminho base do script (funciona em qualquer computador)"""
    if getattr(sys, 'frozen', False):
        # Se for um executável compilado
        return os.path.dirname(sys.executable)
    else:
        # Se for script Python normal
        return os.path.dirname(os.path.abspath(__file__))

# Caminho base do jogo
BASE_DIR = get_base_path()


# ============================================================================
# CLASSES DO JOGO
# ============================================================================

class EstadoJogo(Enum):
    MENU = "menu"
    POSICIONANDO = "posicionando"
    JOGANDO = "jogando"
    GAME_OVER = "game_over"
    VITORIA = "vitoria"
    PAUSA = "pausa"

class Celula:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.tem_navio = False
        self.foi_atingida = False
        self.navio_ref = None
    
    def reset(self):
        self.tem_navio = False
        self.foi_atingida = False
        self.navio_ref = None

class Navio:
    def __init__(self, tamanho: int):
        self.tamanho = tamanho
        self.posicoes: List[Tuple[int, int]] = []
        self.impactos = [False] * tamanho
        self.afundado = False
    
    def adicionar_posicao(self, x: int, y: int):
        self.posicoes.append((x, y))
    
    def receber_tiro(self, x: int, y: int) -> bool:
        if (x, y) in self.posicoes:
            idx = self.posicoes.index((x, y))
            self.impactos[idx] = True
            self.afundado = all(self.impactos)
            return True
        return False
    
    def esta_afundado(self) -> bool:
        return self.afundado

class Tabuleiro:
    def __init__(self):
        self.celulas = [[Celula(i, j) for j in range(10)] for i in range(10)]
        self.navios: List[Navio] = []
    
    def reset(self):
        for i in range(10):
            for j in range(10):
                self.celulas[i][j].reset()
        self.navios.clear()
    
    def pode_posicionar(self, x: int, y: int, tamanho: int, horizontal: bool) -> bool:
        if horizontal:
            if y + tamanho > 10:
                return False
        else:
            if x + tamanho > 10:
                return False
        
        for i in range(-1, (tamanho + 1 if not horizontal else 1) + 1):
            for j in range(-1, (tamanho + 1 if horizontal else 1) + 1):
                nx = x + (i if not horizontal else 0)
                ny = y + (j if horizontal else 0)
                if 0 <= nx < 10 and 0 <= ny < 10:
                    if self.celulas[nx][ny].tem_navio:
                        return False
        return True
    
    def posicionar_navio(self, x: int, y: int, tamanho: int, horizontal: bool) -> bool:
        if not self.pode_posicionar(x, y, tamanho, horizontal):
            return False
        
        navio = Navio(tamanho)
        for i in range(tamanho):
            nx = x + (0 if horizontal else i)
            ny = y + (i if horizontal else 0)
            self.celulas[nx][ny].tem_navio = True
            self.celulas[nx][ny].navio_ref = navio
            navio.adicionar_posicao(nx, ny)
        
        self.navios.append(navio)
        return True
    
    def receber_tiro(self, x: int, y: int) -> Tuple[bool, bool]:
        if self.celulas[x][y].foi_atingida:
            return False, False
        self.celulas[x][y].foi_atingida = True
        if self.celulas[x][y].tem_navio:
            navio = self.celulas[x][y].navio_ref
            navio.receber_tiro(x, y)
            return True, navio.esta_afundado()
        return False, False
    
    def todos_afundados(self) -> bool:
        return all(navio.esta_afundado() for navio in self.navios)

class Jogador:
    def __init__(self, nome: str):
        self.nome = nome
        self.tabuleiro = Tabuleiro()
        self.tiros_dados: List[Tuple[int, int]] = []
        self.pontuacao = 0
    
    def reset(self):
        self.tabuleiro.reset()
        self.tiros_dados.clear()

class InimigoIA:
    def __init__(self):
        self.tabuleiro = Tabuleiro()
        self.tiros_dados: List[Tuple[int, int]] = []
        self.modo_caca = True
        self.alvos_pendentes: List[Tuple[int, int]] = []
    
    def reset(self):
        self.tabuleiro.reset()
        self.tiros_dados.clear()
        self.modo_caca = True
        self.alvos_pendentes.clear()
    
    def posicionar_navios_automatico(self) -> bool:
        tamanhos = [5, 4, 3, 3, 2]
        for tamanho in tamanhos:
            for _ in range(500):
                x = random.randint(0, 9)
                y = random.randint(0, 9)
                horizontal = random.choice([True, False])
                if self.tabuleiro.posicionar_navio(x, y, tamanho, horizontal):
                    break
        return True
    
    def escolher_alvo(self, tabuleiro_jogador: Tabuleiro) -> Tuple[int, int]:
        if self.alvos_pendentes:
            return self.alvos_pendentes.pop(0)
        for i in range(10):
            for j in range(10):
                if (i + j) % 2 == 0 and not tabuleiro_jogador.celulas[i][j].foi_atingida:
                    return (i, j)
        for i in range(10):
            for j in range(10):
                if not tabuleiro_jogador.celulas[i][j].foi_atingida:
                    return (i, j)
        return (0, 0)
    
    def registrar_resultado(self, x: int, y: int, acertou: bool, afundou: bool):
        if acertou:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.tiros_dados:
                    self.alvos_pendentes.append((nx, ny))
            if afundou:
                self.alvos_pendentes.clear()

# ============================================================================
# CLASSE PRINCIPAL DO JOGO
# ============================================================================

class BatalhaNavalGUI:
    def __init__(self):
        self.tela = pygame.display.set_mode((Config.LARGURA, Config.ALTURA))
        pygame.display.set_caption("BATALHA NAVAL - RA: 11202521628")
        
        # Tenta carregar o ícone da janela (caminho relativo)
        self.carregar_icone_janela()
        
        self.clock = pygame.time.Clock()
        self.fonte_titulo = self.carregar_fonte(64)
        self.fonte_grande = self.carregar_fonte(40)
        self.fonte_media = self.carregar_fonte(30)
        self.fonte_pequena = self.carregar_fonte(22)
        self.fonte_muito_pequena = self.carregar_fonte(18)
        
        self.estado = EstadoJogo.MENU
        self.jogador = Jogador("Capitao")
        self.inimigo = InimigoIA()
        
        self.navio_selecionado = 0
        self.navios_para_posicionar = [5, 4, 3, 3, 2]
        self.posicionamento_horizontal = True
        
        self.turno_do_jogador = True
        self.mensagem_status = ""
        self.tempo_mensagem = 0
        
        self.particulas: List[List] = []
        self.explosoes: List[Tuple[int, int, float]] = []
        
        self.icones = {}
        self.carregar_icones()
        
        self.sons = {}
        self.carregar_sons()
        self.musica_tocando = False
        self.som_game_over_tocando = False
        self.som_vitoria_tocando = False
        
        self.onda_offset = 0
        self.volume_musica = 0.3
        self.volume_efeitos = 0.5
        
        self.botoes_pausa = []
        self.tempo_ultimo_som = 0
    
    def carregar_icone_janela(self):
        """Carrega o ícone da janela usando caminho relativo"""
        caminhos_icone = [
            os.path.join(BASE_DIR, "assets", "images", "icon.ico"),
            os.path.join(BASE_DIR, "assets", "images", "icon.png"),
            os.path.join(BASE_DIR, "icon.ico"),
            os.path.join(BASE_DIR, "icon.png")
        ]
        
        for caminho in caminhos_icone:
            if os.path.exists(caminho):
                try:
                    icon = pygame.image.load(caminho)
                    pygame.display.set_icon(icon)
                    print(f"✓ Icone da janela carregado: {caminho}")
                    return
                except:
                    pass
        
        print("! Icone da janela nao encontrado, usando padrao")
    
    def carregar_fonte(self, tamanho: int) -> pygame.font.Font:
        """Carrega fonte usando caminho relativo"""
        caminhos_fonte = [
            os.path.join(BASE_DIR, "fonts", "Monocraft.ttc"),
            os.path.join(BASE_DIR, "assets", "fonts", "Monocraft.ttc"),
            os.path.join(BASE_DIR, "fonts", "monocraft.ttf"),
            os.path.join(BASE_DIR, "assets", "fonts", "monocraft.ttf")
        ]
        
        for caminho in caminhos_fonte:
            if os.path.exists(caminho):
                try:
                    return pygame.font.Font(caminho, tamanho)
                except:
                    pass
        
        # Fallback para fonte padrão
        return pygame.font.Font(None, tamanho)
    
    def carregar_sons(self):
        """Carrega todos os sons do jogo usando caminhos relativos"""
        base_sons = os.path.join(BASE_DIR, "assets", "sons")
        
        # Se a pasta não existir, tenta criar
        if not os.path.exists(base_sons):
            os.makedirs(base_sons, exist_ok=True)
            print(f"! Pasta de sons criada: {base_sons}")
            print("! Coloque os arquivos de som na pasta assets/sons/")
        
        # Configuração dos sons
        sons_config = {
            'background': 'background.mp3',
            'canhao': 'canhao.mp3',
            'onda': 'onda.mp3',
            'game_over': 'game over.mp3',
            'vitoria': 'vitoria.mp3'
        }
        
        for nome, arquivo in sons_config.items():
            caminho = os.path.join(base_sons, arquivo)
            if os.path.exists(caminho):
                try:
                    if nome == 'background':
                        self.sons[nome] = caminho
                        print(f"✓ Musica de fundo carregada: {arquivo}")
                    else:
                        self.sons[nome] = pygame.mixer.Sound(caminho)
                        self.sons[nome].set_volume(self.volume_efeitos)
                        print(f"✓ Som carregado: {arquivo}")
                except Exception as e:
                    print(f"✗ Erro ao carregar {arquivo}: {e}")
            else:
                print(f"! Arquivo nao encontrado: {caminho}")
    
    def carregar_icones(self):
        """Carrega as imagens usando caminhos relativos"""
        base_imagens = os.path.join(BASE_DIR, "assets", "images")
        
        # Se a pasta não existir, tenta criar
        if not os.path.exists(base_imagens):
            os.makedirs(base_imagens, exist_ok=True)
            print(f"! Pasta de imagens criada: {base_imagens}")
            print("! Coloque as imagens na pasta assets/images/")
        
        arquivos = {
            'navio': ['navio.png', 'navio.png.png'],
            'agua': ['agua.png.png', 'agua.png'],
            'explosao': ['explosao.png.png', 'explosao.png']
        }
        
        for nome, opcoes in arquivos.items():
            carregado = False
            for arquivo in opcoes:
                caminho = os.path.join(base_imagens, arquivo)
                if os.path.exists(caminho):
                    try:
                        img = pygame.image.load(caminho)
                        self.icones[nome] = pygame.transform.scale(img, (Config.CELULA_TAMANHO, Config.CELULA_TAMANHO))
                        print(f"✓ Imagem carregada: {arquivo}")
                        carregado = True
                        break
                    except Exception as e:
                        print(f"✗ Erro ao carregar {arquivo}: {e}")
            
            if not carregado:
                print(f"! Criando icone padrao para: {nome}")
                self.icones[nome] = self.criar_icone(nome)
        
        self.icones['tiro_agua'] = self.criar_icone_tiro_agua()
        self.icones['tiro_navio'] = self.criar_icone_tiro_navio()
        self.icones['x_vermelho'] = self.criar_icone_x_vermelho()
    
    def criar_icone(self, nome: str) -> pygame.Surface:
        surf = pygame.Surface((Config.CELULA_TAMANHO, Config.CELULA_TAMANHO))
        if nome == 'navio':
            surf.fill((100, 100, 120))
            pygame.draw.rect(surf, (70, 70, 90), (4, 10, 34, 22))
        elif nome == 'agua':
            surf.fill(Config.COR_AGUA)
            for i in range(2):
                y = 12 + i * 12
                pygame.draw.line(surf, (100, 200, 255), (6, y), (36, y-4), 2)
        elif nome == 'explosao':
            surf = pygame.Surface((Config.CELULA_TAMANHO, Config.CELULA_TAMANHO), pygame.SRCALPHA)
            c = Config.CELULA_TAMANHO // 2
            pygame.draw.circle(surf, (255, 150, 0, 200), (c, c), 14)
            pygame.draw.circle(surf, (255, 255, 0, 200), (c, c), 9)
        return surf
    
    def criar_icone_tiro_agua(self) -> pygame.Surface:
        surf = pygame.Surface((Config.CELULA_TAMANHO, Config.CELULA_TAMANHO), pygame.SRCALPHA)
        c = Config.CELULA_TAMANHO // 2
        pygame.draw.circle(surf, (255, 255, 255, 180), (c, c), 10, 2)
        return surf
    
    def criar_icone_tiro_navio(self) -> pygame.Surface:
        surf = pygame.Surface((Config.CELULA_TAMANHO, Config.CELULA_TAMANHO), pygame.SRCALPHA)
        offset = Config.CELULA_TAMANHO // 5
        fim = Config.CELULA_TAMANHO - offset
        pygame.draw.line(surf, (255, 0, 0, 200), (offset, offset), (fim, fim), 4)
        pygame.draw.line(surf, (255, 0, 0, 200), (fim, offset), (offset, fim), 4)
        return surf
    
    def criar_icone_x_vermelho(self) -> pygame.Surface:
        """Cria um X vermelho grande para indicar tiro na agua"""
        surf = pygame.Surface((Config.CELULA_TAMANHO, Config.CELULA_TAMANHO), pygame.SRCALPHA)
        margin = Config.CELULA_TAMANHO // 4
        fim = Config.CELULA_TAMANHO - margin
        
        for offset in [-2, -1, 0, 1, 2]:
            pygame.draw.line(surf, (255, 0, 0, 220), (margin + offset, margin), (fim + offset, fim), 3)
            pygame.draw.line(surf, (255, 0, 0, 220), (margin + offset, fim), (fim + offset, margin), 3)
            pygame.draw.line(surf, (255, 0, 0, 220), (margin, margin + offset), (fim, fim + offset), 3)
            pygame.draw.line(surf, (255, 0, 0, 220), (margin, fim + offset), (fim, margin + offset), 3)
        
        pygame.draw.line(surf, (255, 50, 50, 255), (margin, margin), (fim, fim), 4)
        pygame.draw.line(surf, (255, 50, 50, 255), (fim, margin), (margin, fim), 4)
        
        return surf
    
    def tocar_musica_fundo(self):
        """Toca a música de fundo"""
        if 'background' in self.sons and not self.musica_tocando:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(self.sons['background'])
                pygame.mixer.music.set_volume(self.volume_musica)
                pygame.mixer.music.play(-1)
                self.musica_tocando = True
                print("✓ Musica de fundo iniciada")
            except Exception as e:
                print(f"✗ Erro ao tocar musica de fundo: {e}")
    
    def parar_musica_fundo(self):
        """Para a música de fundo"""
        pygame.mixer.music.stop()
        self.musica_tocando = False
    
    def tocar_som_game_over(self):
        """Toca o som de game over"""
        if 'game_over' in self.sons and not self.som_game_over_tocando:
            try:
                self.parar_som_vitoria()
                self.parar_musica_fundo()
                pygame.time.wait(50)
                self.sons['game_over'].play()
                self.som_game_over_tocando = True
                self.tempo_ultimo_som = pygame.time.get_ticks()
                print("✓ SOM DE GAME OVER INICIADO!")
            except Exception as e:
                print(f"✗ Erro ao tocar game over: {e}")
    
    def parar_som_game_over(self):
        """Para o som de game over"""
        if 'game_over' in self.sons:
            try:
                self.sons['game_over'].stop()
                self.som_game_over_tocando = False
            except:
                pass
    
    def tocar_som_vitoria(self):
        """Toca o som de vitoria"""
        if 'vitoria' in self.sons and not self.som_vitoria_tocando:
            try:
                self.parar_som_game_over()
                self.parar_musica_fundo()
                pygame.time.wait(50)
                self.sons['vitoria'].play()
                self.som_vitoria_tocando = True
                self.tempo_ultimo_som = pygame.time.get_ticks()
                print("✓ SOM DE VITORIA INICIADO!")
            except Exception as e:
                print(f"✗ Erro ao tocar vitoria: {e}")
    
    def parar_som_vitoria(self):
        """Para o som de vitoria"""
        if 'vitoria' in self.sons:
            try:
                self.sons['vitoria'].stop()
                self.som_vitoria_tocando = False
            except:
                pass
    
    def tocar_som_canhao(self):
        """Toca o som do canhão"""
        if 'canhao' in self.sons:
            try:
                self.sons['canhao'].play()
            except:
                pass
    
    def tocar_som_onda(self):
        """Toca o som da onda"""
        if 'onda' in self.sons:
            try:
                self.sons['onda'].play()
            except:
                pass
    
    def adicionar_explosao(self, x: int, y: int):
        self.explosoes.append((x, y, 20))
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            cor = random.choice([Config.VERMELHO, Config.LARANJA, Config.AMARELO])
            self.particulas.append([x, y, cor, 1.0, vx, vy])
    
    def atualizar_animacoes(self):
        for p in self.particulas[:]:
            p[3] -= 0.02
            p[0] += p[4]
            p[1] += p[5]
            p[5] += 0.15
            if p[3] <= 0 or p[0] < 0 or p[0] > Config.LARGURA:
                self.particulas.remove(p)
        
        for exp in self.explosoes[:]:
            exp_list = list(exp)
            exp_list[2] -= 1
            if exp_list[2] <= 0:
                self.explosoes.remove(exp)
        
        self.onda_offset = (self.onda_offset + 1) % 40
        if self.onda_offset == 0:
            self.tocar_som_onda()
    
    def desenhar_texto_com_sombra(self, texto: str, fonte, cor, x: int, y: int, centralizado=True, sombra_offset=2):
        sombra = fonte.render(texto, True, Config.PRETO)
        if centralizado:
            rect_sombra = sombra.get_rect(center=(x + sombra_offset, y + sombra_offset))
        else:
            rect_sombra = sombra.get_rect(topleft=(x + sombra_offset, y + sombra_offset))
        self.tela.blit(sombra, rect_sombra)
        
        render = fonte.render(texto, True, cor)
        if centralizado:
            rect = render.get_rect(center=(x, y))
        else:
            rect = render.get_rect(topleft=(x, y))
        self.tela.blit(render, rect)
    
    def desenhar_texto_com_legenda(self, texto: str, fonte, cor, x: int, y: int, centralizado=True):
        texto_render = fonte.render(texto, True, cor)
        rect_texto = texto_render.get_rect()
        if centralizado:
            rect_texto.center = (x, y)
        else:
            rect_texto.topleft = (x, y)
        
        fundo_rect = rect_texto.inflate(20, 10)
        fundo_surf = pygame.Surface((fundo_rect.width, fundo_rect.height), pygame.SRCALPHA)
        fundo_surf.fill((0, 0, 0, 180))
        self.tela.blit(fundo_surf, fundo_rect)
        
        pygame.draw.rect(self.tela, Config.DOURADO, fundo_rect, 2, border_radius=8)
        self.desenhar_texto_com_sombra(texto, fonte, cor, x, y, centralizado, 2)
    
    def desenhar_fundo(self):
        for i in range(Config.ALTURA):
            cor = (Config.AZUL_PROFUNDO[0] + i//15, Config.AZUL_PROFUNDO[1] + i//10, Config.AZUL_PROFUNDO[2] + i//8)
            pygame.draw.line(self.tela, cor, (0, i), (Config.LARGURA, i))
        
        for i in range(3):
            offset = self.onda_offset + i * 20
            y_base = Config.ALTURA - 60 + i * 15
            points = []
            for x in range(0, Config.LARGURA + 40, 40):
                y = y_base + math.sin((x + offset) * 0.02) * 10
                points.append((x, y))
            if len(points) > 1:
                pygame.draw.lines(self.tela, (*Config.AZUL_CLARO, 100), False, points, 3)
    
    def desenhar_tabuleiro(self, tabuleiro: Tabuleiro, x: int, y: int, 
                          mostrar_navios: bool = True, interativo: bool = False,
                          titulo: str = ""):
        
        largura = Config.CELULA_TAMANHO * 10
        
        if titulo:
            self.desenhar_texto_com_sombra(titulo, self.fonte_media, Config.BRANCO, x + largura//2, y - 49)
        
        pygame.draw.rect(self.tela, Config.AZUL_MARINHO, (x-3, y-3, largura+6, largura+6), border_radius=8)
        pygame.draw.rect(self.tela, Config.BRANCO, (x-3, y-3, largura+6, largura+6), 2, border_radius=8)
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        for i in range(10):
            for j in range(10):
                cx = x + j * Config.CELULA_TAMANHO
                cy = y + i * Config.CELULA_TAMANHO
                rect = pygame.Rect(cx, cy, Config.CELULA_TAMANHO, Config.CELULA_TAMANHO)
                celula = tabuleiro.celulas[i][j]
                
                if celula.foi_atingida:
                    if celula.tem_navio:
                        if 'explosao' in self.icones:
                            self.tela.blit(self.icones['explosao'], (cx, cy))
                        else:
                            pygame.draw.rect(self.tela, Config.COR_ACERTO, rect)
                    else:
                        if 'x_vermelho' in self.icones:
                            self.tela.blit(self.icones['x_vermelho'], (cx, cy))
                        else:
                            if 'tiro_agua' in self.icones:
                                self.tela.blit(self.icones['tiro_agua'], (cx, cy))
                            else:
                                pygame.draw.rect(self.tela, Config.COR_AGUA, rect)
                else:
                    if mostrar_navios and celula.tem_navio:
                        if 'navio' in self.icones:
                            self.tela.blit(self.icones['navio'], (cx, cy))
                        else:
                            pygame.draw.rect(self.tela, Config.COR_NAVIO, rect)
                    else:
                        if 'agua' in self.icones:
                            self.tela.blit(self.icones['agua'], (cx, cy))
                        else:
                            pygame.draw.rect(self.tela, Config.COR_DESCONHECIDO, rect)
                
                if interativo and rect.collidepoint(mouse_x, mouse_y):
                    hover_surf = pygame.Surface((Config.CELULA_TAMANHO, Config.CELULA_TAMANHO), pygame.SRCALPHA)
                    hover_surf.fill((255, 255, 255, 50))
                    self.tela.blit(hover_surf, (cx, cy))
                
                pygame.draw.rect(self.tela, Config.CINZA_CLARO, rect, 1, border_radius=3)
        
        for i in range(10):
            self.desenhar_texto_com_sombra(str(i), self.fonte_muito_pequena, Config.BRANCO, x-20, y + i*Config.CELULA_TAMANHO + 21)
            self.desenhar_texto_com_sombra(chr(65+i), self.fonte_muito_pequena, Config.BRANCO, x + i*Config.CELULA_TAMANHO + 21, y-18)
    
    def desenhar_botao_menu(self):
        rect = pygame.Rect(Config.LARGURA - 60, 10, 50, 50)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        cor = Config.AZUL_MEDIO
        if rect.collidepoint(mouse_x, mouse_y):
            cor = Config.AZUL_CLARO
        
        pygame.draw.rect(self.tela, cor, rect, border_radius=8)
        pygame.draw.rect(self.tela, Config.BRANCO, rect, 2, border_radius=8)
        
        for i in range(3):
            pygame.draw.rect(self.tela, Config.BRANCO, (rect.x + 12, rect.y + 12 + i * 10, 26, 4))
        
        return rect
    
    def desenhar_menu_pausa(self):
        overlay = pygame.Surface((Config.LARGURA, Config.ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.tela.blit(overlay, (0, 0))
        
        self.desenhar_texto_com_sombra("JOGO PAUSADO", self.fonte_grande, Config.AMARELO, Config.LARGURA//2, 250)
        
        botoes = [
            ("CONTINUAR", Config.LARGURA//2, 360, Config.VERDE),
            ("REINICIAR", Config.LARGURA//2, 440, Config.LARANJA),
            ("MENU PRINCIPAL", Config.LARGURA//2, 520, Config.VERMELHO)
        ]
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        clique = pygame.mouse.get_pressed()[0]
        acao = None
        
        for texto, bx, by, cor in botoes:
            rect = pygame.Rect(bx - 150, by - 25, 300, 50)
            cor_atual = cor
            if rect.collidepoint(mouse_x, mouse_y):
                cor_atual = tuple(min(255, c+40) for c in cor)
                if clique:
                    acao = texto
            
            pygame.draw.rect(self.tela, cor_atual, rect, border_radius=10)
            pygame.draw.rect(self.tela, Config.BRANCO, rect, 2, border_radius=10)
            self.desenhar_texto_com_sombra(texto, self.fonte_media, Config.BRANCO, bx, by)
        
        self.desenhar_texto_com_sombra(f"Pontução: {self.jogador.pontuacao}", self.fonte_media, Config.AMARELO, Config.LARGURA//2, 600)
        
        return acao
    
    def desenhar_menu_principal(self) -> Optional[str]:
        self.desenhar_fundo()
        self.tocar_musica_fundo()
        
        self.desenhar_texto_com_sombra("BATALHA NAVAL", self.fonte_titulo, Config.DOURADO, Config.LARGURA//2, 180)
        self.desenhar_texto_com_sombra("RA: 11202521628", self.fonte_media, Config.BRANCO, Config.LARGURA//2, 260)
        
        botoes = [("JOGAR", Config.LARGURA//2, 380, Config.VERDE), ("SAIR", Config.LARGURA//2, 470, Config.VERMELHO)]
        mouse_x, mouse_y = pygame.mouse.get_pos()
        clique = pygame.mouse.get_pressed()[0]
        acao = None
        
        for texto, bx, by, cor in botoes:
            rect = pygame.Rect(bx - 140, by - 30, 280, 60)
            cor_atual = cor
            if rect.collidepoint(mouse_x, mouse_y):
                cor_atual = tuple(min(255, c+40) for c in cor)
                if clique:
                    acao = texto
            
            pygame.draw.rect(self.tela, cor_atual, rect, border_radius=12)
            pygame.draw.rect(self.tela, Config.BRANCO, rect, 3, border_radius=12)
            self.desenhar_texto_com_sombra(texto, self.fonte_media, Config.BRANCO, bx, by)
        
        return acao
    
    def desenhar_posicionamento(self):
        self.desenhar_fundo()
        
        self.desenhar_texto_com_sombra("POSICIONE SUA FROTA", self.fonte_grande, Config.BRANCO, Config.LARGURA//2, 50)
        
        if self.navio_selecionado < len(self.navios_para_posicionar):
            tam = self.navios_para_posicionar[self.navio_selecionado]
            orient = "HORIZONTAL" if self.posicionamento_horizontal else "VERTICAL"
            self.desenhar_texto_com_sombra(f"Navio {self.navio_selecionado+1}/5 - Tamanho: {tam} - {orient}", 
                               self.fonte_media, Config.AMARELO, Config.LARGURA//2, 100)
        
        self.desenhar_texto_com_sombra("[R] Girar  |  [ESC] Cancelar", self.fonte_pequena, Config.CINZA_CLARO, Config.LARGURA//2, 145)
        
        tx = (Config.LARGURA - Config.CELULA_TAMANHO * 10) // 2
        ty = Config.POSICIONAMENTO_Y
        
        self.desenhar_tabuleiro(self.jogador.tabuleiro, tx, ty, True, True, "SUA FROTA")
        
        mx, my = pygame.mouse.get_pos()
        if tx <= mx <= tx + 420 and ty <= my <= ty + 420 and self.navio_selecionado < 5:
            gx = (my - ty) // Config.CELULA_TAMANHO
            gy = (mx - tx) // Config.CELULA_TAMANHO
            if 0 <= gx < 10 and 0 <= gy < 10:
                tam = self.navios_para_posicionar[self.navio_selecionado]
                pode = self.jogador.tabuleiro.pode_posicionar(gx, gy, tam, self.posicionamento_horizontal)
                cor = (0, 255, 0, 80) if pode else (255, 0, 0, 80)
                s = pygame.Surface((Config.CELULA_TAMANHO, Config.CELULA_TAMANHO), pygame.SRCALPHA)
                for i in range(tam):
                    nx = gx + (0 if self.posicionamento_horizontal else i)
                    ny = gy + (i if self.posicionamento_horizontal else 0)
                    if 0 <= nx < 10 and 0 <= ny < 10:
                        s.fill(cor)
                        self.tela.blit(s, (tx + ny * Config.CELULA_TAMANHO, ty + nx * Config.CELULA_TAMANHO))
    
    def desenhar_jogo(self):
        self.desenhar_fundo()
        
        pygame.draw.rect(self.tela, Config.AZUL_MARINHO, (0, 0, Config.LARGURA, 70))
        self.desenhar_texto_com_sombra("BATALHA NAVAL", self.fonte_grande, Config.DOURADO, Config.LARGURA//2, Config.TITULO_Y_AJUSTADO)
        
        turno = "SEU TURNO - ATAQUE!" if self.turno_do_jogador else "TURNO DO INIMIGO..."
        cor = Config.VERDE if self.turno_do_jogador else Config.VERMELHO
        self.desenhar_texto_com_sombra(turno, self.fonte_media, cor, Config.LARGURA//2, Config.TITULO_Y_AJUSTADO + Config.ESPACO_TITULO_TURNO)
        
        self.desenhar_tabuleiro(self.jogador.tabuleiro, Config.TABULEIRO_X, Config.TABULEIRO_Y, True, False, "SUA FROTA")
        self.desenhar_tabuleiro(self.inimigo.tabuleiro, Config.TABULEIRO_INIMIGO_X, Config.TABULEIRO_Y, False, self.turno_do_jogador, "FROTA INIMIGA")
        
        nav_j = sum(1 for n in self.jogador.tabuleiro.navios if not n.afundado)
        nav_i = sum(1 for n in self.inimigo.tabuleiro.navios if not n.afundado)
        
        self.desenhar_texto_com_sombra(f"Navios: {nav_j}/5", self.fonte_pequena, Config.BRANCO, Config.TABULEIRO_X + 210, Config.TABULEIRO_Y + 440)
        self.desenhar_texto_com_sombra(f"Inimigos: {nav_i}/5", self.fonte_pequena, Config.BRANCO, Config.TABULEIRO_INIMIGO_X + 210, Config.TABULEIRO_Y + 440)
        
        self.desenhar_texto_com_sombra(f"Pontos: {self.jogador.pontuacao}", self.fonte_media, Config.AMARELO, 20, 15, False)
        
        if self.mensagem_status and pygame.time.get_ticks() - self.tempo_mensagem < 2500:
            self.desenhar_texto_com_legenda(self.mensagem_status, self.fonte_media, Config.AMARELO, Config.LARGURA//2, Config.ALTURA - 50)
        
        for p in self.particulas:
            pygame.draw.circle(self.tela, p[2], (int(p[0]), int(p[1])), 3)
        
        self.desenhar_botao_menu()
    
    def desenhar_game_over(self):
        overlay = pygame.Surface((Config.LARGURA, Config.ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.tela.blit(overlay, (0, 0))
        
        self.desenhar_texto_com_sombra("GAME OVER", self.fonte_titulo, Config.VERMELHO, Config.LARGURA//2, 280)
        self.desenhar_texto_com_sombra("Sua frota foi destruída!", self.fonte_media, Config.BRANCO, Config.LARGURA//2, 360)
        self.desenhar_texto_com_sombra(f" Pontuação final: {self.jogador.pontuacao}", self.fonte_media, Config.AMARELO, Config.LARGURA//2, 420)
        self.desenhar_texto_com_sombra("[ESPACO] Jogar novamente  |  [ESC] Menu", self.fonte_pequena, Config.CINZA_CLARO, Config.LARGURA//2, 490)
    
    def desenhar_vitoria(self):
        overlay = pygame.Surface((Config.LARGURA, Config.ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.tela.blit(overlay, (0, 0))
        
        self.desenhar_texto_com_sombra("VITÓRIA!", self.fonte_titulo, Config.DOURADO, Config.LARGURA//2, 280)
        self.desenhar_texto_com_sombra("Voce derrotou a frota inimiga!", self.fonte_media, Config.BRANCO, Config.LARGURA//2, 360)
        self.desenhar_texto_com_sombra(f"Pontuação final: {self.jogador.pontuacao}", self.fonte_media, Config.AMARELO, Config.LARGURA//2, 420)
        self.desenhar_texto_com_sombra("[ESPACO] Jogar novamente  |  [ESC] Menu", self.fonte_pequena, Config.CINZA_CLARO, Config.LARGURA//2, 490)
    
    def processar_clique_posicionamento(self, mx, my):
        tx = (Config.LARGURA - Config.CELULA_TAMANHO * 10) // 2
        ty = Config.POSICIONAMENTO_Y
        if tx <= mx <= tx + 420 and ty <= my <= ty + 420 and self.navio_selecionado < 5:
            gx = (my - ty) // Config.CELULA_TAMANHO
            gy = (mx - tx) // Config.CELULA_TAMANHO
            if 0 <= gx < 10 and 0 <= gy < 10:
                if self.jogador.tabuleiro.posicionar_navio(gx, gy, self.navios_para_posicionar[self.navio_selecionado], self.posicionamento_horizontal):
                    self.navio_selecionado += 1
                    if self.navio_selecionado >= 5:
                        self.estado = EstadoJogo.JOGANDO
                        self.turno_do_jogador = True
                        self.mensagem_status = "Jogo iniciado! Seu turno!"
                        self.tempo_mensagem = pygame.time.get_ticks()
    
    def processar_clique_jogo(self, mx, my):
        menu_rect = pygame.Rect(Config.LARGURA - 60, 10, 50, 50)
        if menu_rect.collidepoint(mx, my):
            self.estado = EstadoJogo.PAUSA
            return
        
        if not self.turno_do_jogador:
            return
        
        if Config.TABULEIRO_INIMIGO_X <= mx <= Config.TABULEIRO_INIMIGO_X + 420 and Config.TABULEIRO_Y <= my <= Config.TABULEIRO_Y + 420:
            gx = (my - Config.TABULEIRO_Y) // Config.CELULA_TAMANHO
            gy = (mx - Config.TABULEIRO_INIMIGO_X) // Config.CELULA_TAMANHO
            if 0 <= gx < 10 and 0 <= gy < 10 and not self.inimigo.tabuleiro.celulas[gx][gy].foi_atingida:
                acertou, afundou = self.inimigo.tabuleiro.receber_tiro(gx, gy)
                
                cx = Config.TABULEIRO_INIMIGO_X + gy * Config.CELULA_TAMANHO + 21
                cy = Config.TABULEIRO_Y + gx * Config.CELULA_TAMANHO + 21
                self.adicionar_explosao(cx, cy)
                self.tocar_som_canhao()
                
                if acertou:
                    self.mensagem_status = "NAVIO INIMIGO AFUNDADO!" if afundou else "ACERTOU!"
                    self.jogador.pontuacao += 100 if afundou else 50
                    self.turno_do_jogador = True
                else:
                    self.mensagem_status =  "AGUA... Vez do inimigo!"
                    self.turno_do_jogador = False
                
                self.tempo_mensagem = pygame.time.get_ticks()
                
                if self.inimigo.tabuleiro.todos_afundados():
                    self.estado = EstadoJogo.VITORIA
                    self.tocar_som_vitoria()
    
    def turno_inimigo(self):
        if not self.turno_do_jogador and self.estado == EstadoJogo.JOGANDO:
            pygame.time.wait(700)
            x, y = self.inimigo.escolher_alvo(self.jogador.tabuleiro)
            self.inimigo.tiros_dados.append((x, y))
            acertou, afundou = self.jogador.tabuleiro.receber_tiro(x, y)
            self.inimigo.registrar_resultado(x, y, acertou, afundou)
            
            cx = Config.TABULEIRO_X + y * Config.CELULA_TAMANHO + 21
            cy = Config.TABULEIRO_Y + x * Config.CELULA_TAMANHO + 21
            self.adicionar_explosao(cx, cy)
            self.tocar_som_canhao()
            
            coord = f"{chr(65+y)}{x}"
            if acertou:
                self.mensagem_status = f"INIMIGO AFUNDOU em {coord}!" if afundou else f"INIMIGO ACERTOU em {coord}!"
                self.turno_do_jogador = False
            else:
                self.mensagem_status = f"INIMIGO ERROU em {coord}! Seu turno!"
                self.turno_do_jogador = True
            
            self.tempo_mensagem = pygame.time.get_ticks()
            
            if self.jogador.tabuleiro.todos_afundados():
                self.estado = EstadoJogo.GAME_OVER
                self.tocar_som_game_over()
    
    def reiniciar_jogo(self):
        self.jogador.reset()
        self.inimigo.reset()
        self.navio_selecionado = 0
        self.estado = EstadoJogo.POSICIONANDO
        self.turno_do_jogador = True
        self.particulas.clear()
        self.explosoes.clear()
        self.inimigo.posicionar_navios_automatico()
        self.mensagem_status = "Posicione seus navios!"
        self.tempo_mensagem = pygame.time.get_ticks()
        
        self.parar_som_game_over()
        self.parar_som_vitoria()
    
    def executar(self):
        rodando = True
        while rodando:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    rodando = False
                elif ev.type == pygame.KEYDOWN:
                    if self.estado == EstadoJogo.POSICIONANDO:
                        if ev.key == pygame.K_r:
                            self.posicionamento_horizontal = not self.posicionamento_horizontal
                        elif ev.key == pygame.K_ESCAPE:
                            self.estado = EstadoJogo.MENU
                            self.parar_som_game_over()
                            self.parar_som_vitoria()
                    elif self.estado in [EstadoJogo.GAME_OVER, EstadoJogo.VITORIA]:
                        if ev.key == pygame.K_SPACE:
                            self.reiniciar_jogo()
                        elif ev.key == pygame.K_ESCAPE:
                            self.estado = EstadoJogo.MENU
                            self.parar_som_game_over()
                            self.parar_som_vitoria()
                    elif self.estado == EstadoJogo.PAUSA:
                        if ev.key == pygame.K_ESCAPE:
                            self.estado = EstadoJogo.JOGANDO
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    
                    if self.estado == EstadoJogo.MENU:
                        acao = self.desenhar_menu_principal()
                        if acao == "JOGAR":
                            self.reiniciar_jogo()
                        elif acao == "SAIR":
                            rodando = False
                    
                    elif self.estado == EstadoJogo.POSICIONANDO:
                        self.processar_clique_posicionamento(mx, my)
                    
                    elif self.estado == EstadoJogo.JOGANDO:
                        self.processar_clique_jogo(mx, my)
                    
                    elif self.estado == EstadoJogo.PAUSA:
                        acao = self.desenhar_menu_pausa()
                        if acao == "CONTINUAR":
                            self.estado = EstadoJogo.JOGANDO
                        elif acao == "REINICIAR":
                            self.reiniciar_jogo()
                        elif acao == "MENU PRINCIPAL":
                            self.estado = EstadoJogo.MENU
                            self.parar_som_game_over()
                            self.parar_som_vitoria()
            
            if self.estado == EstadoJogo.MENU:
                self.desenhar_menu_principal()
            elif self.estado == EstadoJogo.POSICIONANDO:
                self.desenhar_posicionamento()
            elif self.estado == EstadoJogo.JOGANDO:
                self.desenhar_jogo()
                self.turno_inimigo()
                self.atualizar_animacoes()
            elif self.estado == EstadoJogo.GAME_OVER:
                self.desenhar_game_over()
                self.atualizar_animacoes()
            elif self.estado == EstadoJogo.VITORIA:
                self.desenhar_vitoria()
                self.atualizar_animacoes()
            elif self.estado == EstadoJogo.PAUSA:
                self.desenhar_jogo()
                self.desenhar_menu_pausa()
            
            pygame.display.flip()
            self.clock.tick(Config.FPS)
        
        self.parar_musica_fundo()
        self.parar_som_game_over()
        self.parar_som_vitoria()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    print("=" * 60)
    print("BATALHA NAVAL - VERSAO FINAL")
    print("RA: 11202521628")
    print("=" * 60)
    print(f"Diretorio do jogo: {BASE_DIR}")
    print("=" * 60)
    jogo = BatalhaNavalGUI()
    jogo.executar()