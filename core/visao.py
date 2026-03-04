"""
Módulo de Visão Computacional para RPAs

Este módulo contém funções para:
- Encontrar imagens na tela
- Clicar em elementos
- Digitar texto
- Controlar janelas
"""

import subprocess
import time
import pyautogui
import pyperclip
from pathlib import Path

from core.logger import logger
from core.config import config


# =============================================================================
# EXCEÇÕES
# =============================================================================

class RPAException(Exception):
    """Erro genérico do RPA"""
    pass


class ElementoNaoEncontrado(RPAException):
    """Erro quando não encontra um elemento obrigatório na tela"""
    pass


# =============================================================================
# CONFIGURAÇÃO INICIAL
# =============================================================================

# Configurações de segurança do PyAutoGUI
pyautogui.FAILSAFE = True  # Move o mouse pro canto para cancelar
pyautogui.PAUSE = config.get("pyautogui_pause", 0.1)  # Pausa entre ações


# =============================================================================
# FUNÇÕES AUXILIARES (USO INTERNO)
# =============================================================================

def _obter_imagens_da_pasta(nome_pasta: str) -> list:
    """
    Busca todas as imagens dentro de uma pasta em ocr/

    Exemplo: _obter_imagens_da_pasta("botao_ok")
    Retorna: ["ocr/botao_ok/img1.png", "ocr/botao_ok/img2.png"]
    """
    pasta = Path("ocr") / nome_pasta

    if not pasta.exists():
        logger.warning(f"Pasta não encontrada: {pasta}")
        return []

    # Extensões de imagem aceitas
    extensoes = (".png", ".jpg", ".jpeg", ".bmp")

    # Lista todas as imagens da pasta
    imagens = []
    for arquivo in pasta.iterdir():
        if arquivo.suffix.lower() in extensoes:
            imagens.append(arquivo)

    if not imagens:
        logger.warning(f"Nenhuma imagem em: {pasta}")

    return sorted(imagens)


def _salvar_screenshot_erro(nome: str):
    """Salva screenshot quando ocorre um erro"""
    if not config.get("salvar_screenshots_erro", True):
        return

    try:
        pasta = Path("screenshots")
        pasta.mkdir(parents=True, exist_ok=True)

        arquivo = pasta / f"erro_{nome}_{int(time.time())}.png"
        pyautogui.screenshot().save(str(arquivo))
        logger.debug(f"Screenshot de erro salvo: {arquivo}")
    except Exception:
        pass  # Ignora erros ao salvar screenshot


def _parse_coordenadas(texto: str):
    """
    Converte texto "x,y" em tupla (x, y)

    Exemplo: _parse_coordenadas("100,200") -> (100, 200)
    """
    try:
        partes = texto.split(",")
        x = int(partes[0].strip())
        y = int(partes[1].strip())
        return (x, y)
    except (ValueError, IndexError):
        return None


# =============================================================================
# FUNÇÕES PRINCIPAIS
# =============================================================================

def screenshot(nome: str = None):
    """
    Tira um screenshot da tela.

    Argumentos:
        nome: Nome do arquivo (opcional). Se não passar, usa timestamp.

    Retorna:
        Caminho do arquivo salvo

    Exemplo:
        screenshot("tela_inicial")
        screenshot()  # Salva com timestamp
    """
    if nome is None:
        nome = f"screenshot_{int(time.time())}"

    pasta = Path("screenshots")
    pasta.mkdir(parents=True, exist_ok=True)

    arquivo = pasta / f"{nome}.png"
    pyautogui.screenshot().save(str(arquivo))

    logger.info(f"Screenshot salvo: {arquivo}")
    return arquivo


def encontrar(
    elemento: str,
    precisao: float = None,
    tempo_maximo: float = None,
    critico: bool = False,
    screenshot_antes: bool = False
):
    """
    Encontra um elemento na tela.

    Argumentos:
        elemento: Nome da pasta em ocr/ (ex: "botao_ok")
        precisao: Quanto precisa ser parecido (0.0 a 1.0). Padrão: 0.8
        tempo_maximo: Quantos segundos tentar antes de desistir. Padrão: 10
        critico: Se True e não encontrar, para o RPA com erro
        screenshot_antes: Se True, tira screenshot antes de procurar

    Retorna:
        Tupla (x, y) com a posição central do elemento, ou None se não encontrar

    Exemplos:
        # Procura o botão OK por até 10 segundos
        posicao = encontrar("botao_ok")

        # Procura por 5 segundos, com 90% de precisão
        posicao = encontrar("icone", precisao=0.9, tempo_maximo=5)

        # Se não encontrar, para o RPA
        posicao = encontrar("campo_obrigatorio", critico=True)
    """

    # Usa valores do config.json se não foram passados
    if precisao is None:
        precisao = config.get("precisao_padrao", 0.8)
    if tempo_maximo is None:
        tempo_maximo = config.get("tempo_maximo_padrao", 10)

    intervalo_busca = config.get("intervalo_busca", 0.5)

    # Se passou coordenadas diretas (ex: "100,200")
    coords = _parse_coordenadas(elemento)
    if coords:
        logger.debug(f"Usando coordenadas diretas: {coords}")
        return coords

    # Busca as imagens na pasta
    imagens = _obter_imagens_da_pasta(elemento)

    if not imagens:
        msg = f"Nenhuma imagem para: {elemento}"
        logger.error(msg)
        _salvar_screenshot_erro(f"sem_imagem_{elemento}")

        if critico:
            raise ElementoNaoEncontrado(msg)
        return None

    # Screenshot antes de procurar (se pedido)
    if screenshot_antes:
        screenshot(f"antes_encontrar_{elemento}")

    # Tenta encontrar por X segundos
    tempo_inicio = time.time()
    tentativa = 0

    while (time.time() - tempo_inicio) < tempo_maximo:
        tentativa += 1

        # Tenta cada imagem da pasta
        for imagem in imagens:
            try:
                resultado = pyautogui.locateOnScreen(
                    str(imagem),
                    confidence=precisao
                )

                if resultado:
                    # Calcula o centro do elemento
                    centro_x = resultado.left + resultado.width // 2
                    centro_y = resultado.top + resultado.height // 2

                    logger.info(f"'{elemento}' encontrado em ({centro_x}, {centro_y})")
                    return (centro_x, centro_y)

            except Exception as e:
                logger.debug(f"Erro ao buscar {imagem.name}: {e}")

        # Espera antes de tentar novamente
        time.sleep(intervalo_busca)

    # Não encontrou
    msg = f"'{elemento}' não encontrado após {tempo_maximo}s"
    logger.warning(msg)
    _salvar_screenshot_erro(f"nao_encontrado_{elemento}")

    if critico:
        raise ElementoNaoEncontrado(msg)

    return None


def clicar(
    posicao=None,
    botao: str = "left",
    cliques: int = 1,
    screenshot_antes: bool = False
):
    """
    Clica em uma posição da tela.

    Argumentos:
        posicao: Onde clicar. Pode ser:
                 - Tupla (x, y): clicar("100,200") ou clicar((100, 200))
                 - None: usa a última posição encontrada (não implementado)
        botao: "left" (esquerdo), "right" (direito) ou "middle" (meio)
        cliques: Quantos cliques (1 = simples, 2 = duplo)
        screenshot_antes: Se True, tira screenshot antes de clicar

    Retorna:
        True se clicou, False se deu erro

    Exemplos:
        clicar((500, 300))           # Clique simples
        clicar("500,300")            # Mesmo que acima
        clicar((500, 300), cliques=2)  # Duplo clique
        clicar((500, 300), botao="right")  # Clique direito
    """

    # Converte string "x,y" para tupla
    if isinstance(posicao, str):
        posicao = _parse_coordenadas(posicao)

    if posicao is None:
        logger.error("Posição não informada para clicar")
        _salvar_screenshot_erro("clicar_sem_posicao")
        return False

    x, y = posicao

    try:
        if screenshot_antes:
            screenshot(f"antes_clicar_{x}_{y}")

        pyautogui.click(x, y, clicks=cliques, button=botao)
        logger.info(f"Clique em ({x}, {y}) - botão: {botao}, cliques: {cliques}")
        return True

    except Exception as e:
        logger.error(f"Erro ao clicar em ({x}, {y}): {e}")
        _salvar_screenshot_erro(f"erro_clicar_{x}_{y}")
        return False


def encontrar_e_clicar(
    elemento: str,
    precisao: float = None,
    tempo_maximo: float = None,
    critico: bool = False,
    botao: str = "left",
    cliques: int = 1,
    screenshot_antes: bool = False
):
    """
    Encontra um elemento e clica nele.

    É a combinação de encontrar() + clicar().

    Argumentos:
        elemento: Nome da pasta em ocr/
        precisao: Quanto precisa ser parecido (0.0 a 1.0)
        tempo_maximo: Quantos segundos tentar
        critico: Se True e não encontrar, para o RPA
        botao: "left", "right" ou "middle"
        cliques: Quantos cliques
        screenshot_antes: Se True, tira screenshot antes de clicar

    Retorna:
        True se encontrou e clicou, False se não encontrou

    Exemplos:
        # Clica no botão OK
        encontrar_e_clicar("botao_ok")

        # Duplo clique no ícone
        encontrar_e_clicar("icone_arquivo", cliques=2)

        # Clique direito no item
        encontrar_e_clicar("item_lista", botao="right")

        # Obrigatório encontrar
        encontrar_e_clicar("campo_login", critico=True)
    """

    posicao = encontrar(
        elemento=elemento,
        precisao=precisao,
        tempo_maximo=tempo_maximo,
        critico=critico
    )

    if posicao:
        if screenshot_antes:
            screenshot(f"antes_clicar_{elemento}")
        return clicar(posicao, botao=botao, cliques=cliques)

    return False


def digitar(
    texto: str,
    usar_clipboard: bool = True,
    pressionar_enter: bool = False
):
    """
    Digita um texto.

    Argumentos:
        texto: O texto a ser digitado
        usar_clipboard: Se True, usa Ctrl+V (suporta acentos). Padrão: True
        pressionar_enter: Se True, pressiona Enter no final

    Retorna:
        True se digitou, False se deu erro

    Exemplos:
        digitar("usuario@email.com")
        digitar("senha123", pressionar_enter=True)
        digitar("texto simples", usar_clipboard=False)  # Sem acentos
    """

    try:
        if usar_clipboard:
            # Usa clipboard para suportar caracteres especiais
            pyperclip.copy(texto)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.3)
        else:
            # Digita caractere por caractere (só ASCII)
            pyautogui.write(texto, interval=0.05)

        # Mostra no log (esconde se for muito grande)
        texto_log = texto if len(texto) <= 20 else texto[:20] + "..."
        logger.info(f"Digitado: '{texto_log}'")

        if pressionar_enter:
            pyautogui.press("enter")
            logger.debug("Enter pressionado")

        return True

    except Exception as e:
        logger.error(f"Erro ao digitar: {e}")
        _salvar_screenshot_erro("erro_digitar")
        return False


def pressionar_tecla(tecla: str, vezes: int = 1):
    """
    Pressiona uma tecla do teclado.

    Argumentos:
        tecla: Nome da tecla (enter, tab, escape, f1, etc.)
        vezes: Quantas vezes pressionar

    Retorna:
        True se pressionou, False se deu erro

    Exemplos:
        pressionar_tecla("enter")
        pressionar_tecla("tab", vezes=3)  # 3x Tab
        pressionar_tecla("escape")
        pressionar_tecla("f5")
    """

    try:
        for _ in range(vezes):
            pyautogui.press(tecla)

        logger.debug(f"Tecla '{tecla}' pressionada {vezes}x")
        return True

    except Exception as e:
        logger.error(f"Erro ao pressionar '{tecla}': {e}")
        return False


def atalho(*teclas):
    """
    Executa um atalho de teclado.

    Argumentos:
        *teclas: As teclas do atalho

    Retorna:
        True se executou, False se deu erro

    Exemplos:
        atalho("ctrl", "c")        # Copiar
        atalho("ctrl", "v")        # Colar
        atalho("ctrl", "s")        # Salvar
        atalho("alt", "f4")        # Fechar janela
        atalho("ctrl", "shift", "s")  # Salvar como
    """

    try:
        pyautogui.hotkey(*teclas)
        time.sleep(0.3)

        logger.debug(f"Atalho: {'+'.join(teclas)}")
        return True

    except Exception as e:
        logger.error(f"Erro no atalho {'+'.join(teclas)}: {e}")
        return False


def focar_janela(titulo: str):
    """
    Foca em uma janela pelo título (Windows).

    Argumentos:
        titulo: Parte do título da janela

    Retorna:
        True se focou, False se não encontrou

    Exemplos:
        focar_janela("Chrome")
        focar_janela("Domínio")
        focar_janela("Excel")
    """

    # Script PowerShell para focar a janela
    script = f'''
    Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    public class Win32 {{
        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);
    }}
"@
    $proc = Get-Process | Where-Object {{$_.MainWindowTitle -like "*{titulo}*"}} | Select-Object -First 1
    if ($proc) {{
        [Win32]::SetForegroundWindow($proc.MainWindowHandle)
        return $true
    }}
    return $false
    '''

    try:
        resultado = subprocess.run(
            ["powershell", "-Command", script],
            capture_output=True,
            text=True,
            timeout=10
        )

        if "True" in resultado.stdout:
            logger.info(f"Janela '{titulo}' focada")
            return True
        else:
            logger.warning(f"Janela '{titulo}' não encontrada")
            return False

    except Exception as e:
        logger.error(f"Erro ao focar janela: {e}")
        return False


def aguardar_elemento(
    elemento: str,
    precisao: float = None,
    tempo_maximo: float = 30,
    critico: bool = True
):
    """
    Aguarda um elemento aparecer na tela.

    Argumentos:
        elemento: Nome da pasta em ocr/
        precisao: Quanto precisa ser parecido
        tempo_maximo: Quantos segundos esperar
        critico: Se True e não aparecer, para o RPA

    Retorna:
        True se apareceu, False se não

    Exemplos:
        aguardar_elemento("tela_carregada")
        aguardar_elemento("popup", tempo_maximo=60)
    """

    resultado = encontrar(
        elemento=elemento,
        precisao=precisao,
        tempo_maximo=tempo_maximo,
        critico=critico
    )

    return resultado is not None


def aguardar_desaparecer(
    elemento: str,
    precisao: float = None,
    tempo_maximo: float = 30
):
    """
    Aguarda um elemento desaparecer da tela.

    Útil para esperar loadings e processamentos.

    Argumentos:
        elemento: Nome da pasta em ocr/
        precisao: Quanto precisa ser parecido
        tempo_maximo: Quantos segundos esperar

    Retorna:
        True se desapareceu, False se ainda está lá

    Exemplos:
        aguardar_desaparecer("loading")
        aguardar_desaparecer("processando", tempo_maximo=120)
    """

    intervalo_busca = config.get("intervalo_busca", 0.5)
    tempo_inicio = time.time()

    while (time.time() - tempo_inicio) < tempo_maximo:
        # Procura rapidamente
        resultado = encontrar(
            elemento=elemento,
            precisao=precisao,
            tempo_maximo=intervalo_busca,
            critico=False
        )

        if resultado is None:
            logger.info(f"'{elemento}' desapareceu")
            return True

        time.sleep(intervalo_busca)

    logger.warning(f"'{elemento}' não desapareceu após {tempo_maximo}s")
    _salvar_screenshot_erro(f"nao_desapareceu_{elemento}")
    return False


def aguardar(segundos: float, motivo: str = ""):
    """
    Espera um tempo.

    Argumentos:
        segundos: Quantos segundos esperar
        motivo: Descrição do motivo (para o log)

    Exemplos:
        aguardar(2)
        aguardar(5, "carregamento do sistema")
    """

    if motivo:
        logger.debug(f"Aguardando {segundos}s - {motivo}")

    time.sleep(segundos)


def mover_mouse(x: int, y: int):
    """
    Move o mouse para uma posição.

    Argumentos:
        x: Posição horizontal
        y: Posição vertical

    Exemplos:
        mover_mouse(500, 300)
    """

    pyautogui.moveTo(x, y, duration=0.3)
    logger.debug(f"Mouse movido para ({x}, {y})")
