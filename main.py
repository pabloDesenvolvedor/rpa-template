"""
RPA Template - Exemplo de Uso

Este arquivo mostra como usar o template para criar automações.
Modifique conforme necessário para sua automação.
"""

import time
from core.visao import (
    encontrar_e_clicar,
    digitar,
    pressionar_tecla,
    atalho,
    focar_janela,
    aguardar_elemento,
    aguardar_desaparecer,
    aguardar,
    screenshot,
    ElementoNaoEncontrado
)
from core.logger import configurar_logger, logger
from core.persistencia import (
    foi_processado,
    marcar_processado,
    registrar_erro,
    total_processados,
    total_erros
)


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

NOME_RPA = "MeuRPA"  # Mude para o nome do seu RPA


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def executar():
    """
    Função principal do RPA.
    É aqui que você coloca sua automação.
    """

    # Configura o logger (aparece nos logs e no monitoramento)
    configurar_logger(NOME_RPA)
    logger.inicio()

    # Mostra quantos itens já foram processados anteriormente
    if total_processados() > 0:
        logger.info(f"Itens já processados: {total_processados()}")
    if total_erros() > 0:
        logger.warning(f"Itens com erro: {total_erros()}")

    try:
        # ==================================================================
        # EXEMPLO 1: Processar lista de empresas
        # ==================================================================
        #
        # empresas = ["1001", "1002", "1003"]
        # logger.set_total_empresas(len(empresas))
        #
        # for i, empresa in enumerate(empresas, 1):
        #
        #     # Pula se já foi processada antes
        #     if foi_processado(empresa):
        #         logger.set_empresa(empresa)
        #         logger.info("Já processada, pulando...")
        #         logger.incrementar_pulada()
        #         continue
        #
        #     # Mostra progresso
        #     logger.progresso(i, len(empresas))
        #     logger.set_empresa(empresa)
        #
        #     try:
        #         # Define etapa (aparece nos logs)
        #         logger.set_etapa("Login")
        #         encontrar_e_clicar("campo_usuario", critico=True)
        #         digitar("usuario@empresa.com")
        #         pressionar_tecla("tab")
        #         digitar("senha123", pressionar_enter=True)
        #
        #         logger.set_etapa("Processamento")
        #         # ... seu código aqui ...
        #
        #         # Marca como processada com sucesso
        #         marcar_processado(empresa)
        #         logger.incrementar_processada()
        #
        #     except Exception as e:
        #         logger.error(f"Erro: {e}")
        #         registrar_erro(empresa, str(e))
        #         logger.incrementar_erro()

        # ==================================================================
        # EXEMPLO 2: Clicar em elementos
        # ==================================================================
        #
        # # Clica em um elemento (procura imagens na pasta ocr/botao_ok/)
        # encontrar_e_clicar("botao_ok", critico=True)
        #
        # # Com mais opções
        # encontrar_e_clicar(
        #     "botao_salvar",
        #     precisao=0.9,       # 90% de certeza (padrão é 80%)
        #     tempo_maximo=15,    # Espera até 15 segundos
        #     critico=True,       # Para o RPA se não encontrar
        #     cliques=2           # Clique duplo
        # )

        # ==================================================================
        # EXEMPLO 3: Digitar texto
        # ==================================================================
        #
        # encontrar_e_clicar("campo_email", critico=True)
        # digitar("usuario@email.com")
        #
        # pressionar_tecla("tab")  # Pula para próximo campo
        #
        # digitar("Senha@123!", pressionar_enter=True)

        # ==================================================================
        # EXEMPLO 4: Atalhos de teclado
        # ==================================================================
        #
        # focar_janela("Sistema ERP")      # Traz janela para frente
        # atalho("ctrl", "n")              # Ctrl+N (novo)
        # atalho("ctrl", "shift", "s")     # Ctrl+Shift+S (salvar como)

        # ==================================================================
        # EXEMPLO 5: Aguardar elementos
        # ==================================================================
        #
        # # Espera elemento aparecer
        # aguardar_elemento("tela_principal", tempo_maximo=30, critico=True)
        #
        # # Espera elemento desaparecer (ex: loading)
        # aguardar_desaparecer("icone_loading", tempo_maximo=60)
        #
        # # Espera tempo fixo (em segundos)
        # aguardar(2)

        # ==================================================================
        # SEU CÓDIGO AQUI
        # ==================================================================

        logger.info("Automação executada com sucesso!")
        logger.fim(sucesso=True)
        return True

    except ElementoNaoEncontrado as e:
        # Screenshot já foi capturado automaticamente
        logger.error(f"Elemento não encontrado: {e}")
        logger.fim(sucesso=False)
        return False

    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        screenshot("erro_inesperado")
        logger.fim(sucesso=False)
        return False


# =============================================================================
# EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    # Tempo para você posicionar a tela antes de começar
    print("RPA iniciará em 5 segundos...")
    print("Posicione a tela do sistema que será automatizado.")
    time.sleep(5)

    # Executa o RPA
    sucesso = executar()

    # Retorna código de saída (0 = sucesso, 1 = erro)
    exit(0 if sucesso else 1)
