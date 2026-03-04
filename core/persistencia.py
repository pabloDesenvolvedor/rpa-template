"""
Sistema de Persistência para RPA

Este módulo permite salvar e carregar dados em arquivos JSON.
Útil para retomar processamento de onde parou após uma falha.

Uso básico:
    from core.persistencia import salvar, carregar, foi_processado, marcar_processado

    # Salvar dados
    salvar("config", {"usuario": "admin", "tentativas": 3})

    # Carregar dados
    dados = carregar("config")

    # Verificar se item já foi processado
    if not foi_processado("empresa_001"):
        # processar...
        marcar_processado("empresa_001")
"""

import json
from datetime import datetime
from pathlib import Path


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

# Pasta onde os dados são salvos
PASTA_DADOS = Path("dados")
PASTA_DADOS.mkdir(exist_ok=True)

# Arquivo que guarda os itens processados
ARQUIVO_PROCESSADOS = PASTA_DADOS / "processados.json"


# =============================================================================
# FUNÇÕES DE DADOS GERAIS
# =============================================================================

def salvar(nome: str, dados) -> bool:
    """
    Salva dados em um arquivo JSON.

    Args:
        nome: Nome do arquivo (sem extensão .json)
        dados: Qualquer dado que possa virar JSON (dict, list, str, etc)

    Returns:
        True se salvou com sucesso, False se deu erro

    Exemplo:
        salvar("config", {"usuario": "admin"})
        salvar("lista", [1, 2, 3])
    """
    arquivo = PASTA_DADOS / f"{nome}.json"

    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception:
        return False


def carregar(nome: str, padrao=None):
    """
    Carrega dados de um arquivo JSON.

    Args:
        nome: Nome do arquivo (sem extensão .json)
        padrao: Valor retornado se arquivo não existir

    Returns:
        Dados do arquivo ou valor padrão

    Exemplo:
        config = carregar("config", {})
        lista = carregar("lista", [])
    """
    arquivo = PASTA_DADOS / f"{nome}.json"

    if not arquivo.exists():
        return padrao

    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return padrao


def excluir(nome: str) -> bool:
    """
    Exclui um arquivo de dados.

    Args:
        nome: Nome do arquivo (sem extensão .json)

    Returns:
        True se excluiu, False se não existia ou deu erro

    Exemplo:
        excluir("config")
    """
    arquivo = PASTA_DADOS / f"{nome}.json"

    try:
        if arquivo.exists():
            arquivo.unlink()
            return True
        return False
    except Exception:
        return False


# =============================================================================
# CONTROLE DE ITENS PROCESSADOS
# =============================================================================

# Cache dos itens processados (carregado do arquivo)
_processados: set = set()
_processados_carregados = False


def _carregar_processados():
    """Carrega a lista de processados do arquivo (uso interno)"""
    global _processados, _processados_carregados

    if _processados_carregados:
        return

    if ARQUIVO_PROCESSADOS.exists():
        try:
            with open(ARQUIVO_PROCESSADOS, "r", encoding="utf-8") as f:
                dados = json.load(f)
                _processados = set(dados.get("itens", []))
        except Exception:
            _processados = set()

    _processados_carregados = True


def _salvar_processados():
    """Salva a lista de processados no arquivo (uso interno)"""
    dados = {
        "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(_processados),
        "itens": list(_processados)
    }

    try:
        with open(ARQUIVO_PROCESSADOS, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def foi_processado(item_id: str) -> bool:
    """
    Verifica se um item já foi processado.

    Args:
        item_id: Identificador único do item (ex: código da empresa)

    Returns:
        True se já foi processado, False se não

    Exemplo:
        if foi_processado("1001"):
            print("Empresa 1001 já foi processada")
        else:
            # processa empresa 1001...
            marcar_processado("1001")
    """
    _carregar_processados()
    return str(item_id) in _processados


def marcar_processado(item_id: str):
    """
    Marca um item como processado.

    Args:
        item_id: Identificador único do item

    Exemplo:
        marcar_processado("1001")
    """
    _carregar_processados()
    _processados.add(str(item_id))
    _salvar_processados()


def desmarcar_processado(item_id: str):
    """
    Remove um item da lista de processados.

    Args:
        item_id: Identificador único do item

    Exemplo:
        desmarcar_processado("1001")  # Vai processar de novo
    """
    _carregar_processados()
    _processados.discard(str(item_id))
    _salvar_processados()


def listar_processados() -> list:
    """
    Retorna lista de todos os itens processados.

    Returns:
        Lista de IDs dos itens processados

    Exemplo:
        processados = listar_processados()
        print(f"Total processados: {len(processados)}")
    """
    _carregar_processados()
    return list(_processados)


def total_processados() -> int:
    """
    Retorna quantos itens foram processados.

    Returns:
        Número de itens processados

    Exemplo:
        print(f"Já processamos {total_processados()} empresas")
    """
    _carregar_processados()
    return len(_processados)


def limpar_processados():
    """
    Remove todos os itens da lista de processados.
    Use com cuidado! Isso fará o RPA reprocessar tudo.

    Exemplo:
        limpar_processados()  # Vai começar do zero
    """
    global _processados
    _processados = set()
    _salvar_processados()


# =============================================================================
# REGISTRO DE ERROS
# =============================================================================

# Cache dos erros
_erros: list = []
_erros_carregados = False
ARQUIVO_ERROS = PASTA_DADOS / "erros.json"


def _carregar_erros():
    """Carrega a lista de erros do arquivo (uso interno)"""
    global _erros, _erros_carregados

    if _erros_carregados:
        return

    if ARQUIVO_ERROS.exists():
        try:
            with open(ARQUIVO_ERROS, "r", encoding="utf-8") as f:
                dados = json.load(f)
                _erros = dados.get("erros", [])
        except Exception:
            _erros = []

    _erros_carregados = True


def _salvar_erros():
    """Salva a lista de erros no arquivo (uso interno)"""
    dados = {
        "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(_erros),
        "erros": _erros
    }

    try:
        with open(ARQUIVO_ERROS, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def registrar_erro(item_id: str, motivo: str, detalhes: dict = None):
    """
    Registra um erro ocorrido no processamento.

    Args:
        item_id: Identificador do item que deu erro
        motivo: Descrição do erro
        detalhes: Informações extras (opcional)

    Exemplo:
        registrar_erro("1001", "Timeout ao clicar no botão")
        registrar_erro("1002", "Campo não encontrado", {"tela": "login"})
    """
    _carregar_erros()

    erro = {
        "item_id": str(item_id),
        "motivo": motivo,
        "quando": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if detalhes:
        erro["detalhes"] = detalhes

    _erros.append(erro)
    _salvar_erros()


def listar_erros() -> list:
    """
    Retorna lista de todos os erros registrados.

    Returns:
        Lista de erros (cada erro é um dicionário)

    Exemplo:
        erros = listar_erros()
        for erro in erros:
            print(f"{erro['item_id']}: {erro['motivo']}")
    """
    _carregar_erros()
    return _erros.copy()


def itens_com_erro() -> list:
    """
    Retorna lista de IDs dos itens que tiveram erro.

    Returns:
        Lista de IDs

    Exemplo:
        com_erro = itens_com_erro()
        print(f"Empresas com erro: {com_erro}")
    """
    _carregar_erros()
    return [erro["item_id"] for erro in _erros]


def total_erros() -> int:
    """
    Retorna quantos erros ocorreram.

    Returns:
        Número de erros

    Exemplo:
        print(f"Total de erros: {total_erros()}")
    """
    _carregar_erros()
    return len(_erros)


def limpar_erros():
    """
    Remove todos os erros registrados.

    Exemplo:
        limpar_erros()
    """
    global _erros
    _erros = []
    _salvar_erros()
