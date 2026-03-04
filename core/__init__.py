"""
Core do RPA Template

Importações rápidas para usar no seu RPA:

    from core import (
        # Visão
        encontrar, clicar, encontrar_e_clicar, digitar,
        pressionar_tecla, atalho, focar_janela,
        aguardar_elemento, aguardar_desaparecer, aguardar, screenshot,
        ElementoNaoEncontrado,

        # Logger
        logger, configurar_logger,

        # Persistência
        salvar, carregar, foi_processado, marcar_processado,
        registrar_erro, total_processados, total_erros
    )
"""

# Funções de visão computacional
from core.visao import (
    encontrar,
    clicar,
    encontrar_e_clicar,
    digitar,
    pressionar_tecla,
    atalho,
    focar_janela,
    aguardar_elemento,
    aguardar_desaparecer,
    aguardar,
    mover_mouse,
    screenshot,
    ElementoNaoEncontrado
)

# Sistema de logs
from core.logger import (
    logger,
    configurar_logger
)

# Persistência de dados
from core.persistencia import (
    salvar,
    carregar,
    excluir,
    foi_processado,
    marcar_processado,
    desmarcar_processado,
    listar_processados,
    total_processados,
    limpar_processados,
    registrar_erro,
    listar_erros,
    itens_com_erro,
    total_erros,
    limpar_erros
)
