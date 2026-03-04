"""
Sistema de Logs para RPA

Este módulo cria 2 arquivos de log:
1. logs/terminal.log - Tudo que aparece no terminal (debug incluso)
2. logs/api.log - Log limpo que é enviado para a API de monitoramento

Uso básico:
    from core.logger import logger

    logger.info("Mensagem informativa")
    logger.warning("Aviso")
    logger.error("Erro")
"""

import os
import sys
import uuid
import shutil
import requests
from datetime import datetime, timezone
from pathlib import Path


# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

# URL da API de monitoramento (pode ser alterada via variável de ambiente)
API_URL = os.getenv(
    "API_URL",
    "https://monitoramento.redeespecialistas.com.br/logging/salvar/RPA"
)

# Token de autenticação da API
API_TOKEN = os.getenv("API_TOKEN", "")


# =============================================================================
# CLASSE PRINCIPAL
# =============================================================================

class Logger:
    """
    Sistema de logs do RPA.

    Atributos:
        nome_rpa: Nome do RPA (aparece nos logs)
        exec_id: ID único desta execução
        empresa_atual: Código da empresa sendo processada
        etapa_atual: Etapa do processo

    Contadores:
        total_empresas: Total de empresas a processar
        empresas_processadas: Quantas já foram processadas
        empresas_com_erro: Quantas deram erro
        empresas_puladas: Quantas foram puladas
    """

    def __init__(self, nome_rpa: str = "RPA"):
        # Identificação
        self.nome_rpa = nome_rpa
        self.exec_id = str(uuid.uuid4())
        self.data_inicio = datetime.now(timezone.utc)

        # Contexto atual
        self.empresa_atual = None
        self.etapa_atual = None

        # Contadores
        self.total_empresas = 0
        self.empresas_processadas = 0
        self.empresas_com_erro = 0
        self.empresas_puladas = 0

        self.total_itens = 0
        self.itens_processados = 0
        self.itens_com_erro = 0

        # Arquivos de log
        self._pasta_logs = Path("logs")
        self._pasta_logs.mkdir(exist_ok=True)

        self._arquivo_terminal = self._pasta_logs / "terminal.log"
        self._arquivo_api = self._pasta_logs / "api.log"

        # Inicia os arquivos de log
        self._iniciar_logs()

    def _iniciar_logs(self):
        """Prepara os arquivos de log"""

        # Rotaciona logs anteriores (salva como .old)
        self._rotacionar(self._arquivo_terminal)
        self._rotacionar(self._arquivo_api)

        # Cabeçalho inicial
        cabecalho = f"""{'='*60}
RPA: {self.nome_rpa}
Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Exec ID: {self.exec_id}
{'='*60}

"""
        # Escreve cabeçalho nos arquivos
        with open(self._arquivo_terminal, "w", encoding="utf-8") as f:
            f.write(cabecalho)

        with open(self._arquivo_api, "w", encoding="utf-8") as f:
            f.write(cabecalho)

    def _rotacionar(self, arquivo: Path):
        """Move o arquivo atual para .old"""
        if arquivo.exists():
            arquivo_old = arquivo.with_suffix(".old.log")
            if arquivo_old.exists():
                arquivo_old.unlink()
            shutil.move(str(arquivo), str(arquivo_old))

    def _timestamp(self) -> str:
        """Retorna a hora atual formatada"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _escrever_terminal(self, nivel: str, mensagem: str):
        """Escreve no terminal e no arquivo terminal.log"""

        # Monta a linha do log
        partes = [self._timestamp(), nivel]

        if self.empresa_atual:
            partes.append(f"[{self.empresa_atual}]")

        if self.etapa_atual:
            partes.append(f"[{self.etapa_atual}]")

        partes.append(mensagem)

        linha = " | ".join(partes)

        # Mostra no terminal
        print(linha)

        # Salva no arquivo
        try:
            with open(self._arquivo_terminal, "a", encoding="utf-8") as f:
                f.write(linha + "\n")
        except Exception:
            pass

    def _escrever_api(self, nivel: str, mensagem: str):
        """Escreve no arquivo api.log"""

        partes = [self._timestamp()]

        if self.empresa_atual:
            partes.append(f"CODI_EMP: {self.empresa_atual}")

        if self.etapa_atual:
            partes.append(f"ETAPA: {self.etapa_atual}")

        partes.append(nivel)
        partes.append(mensagem)

        linha = " - ".join(partes)

        try:
            with open(self._arquivo_api, "a", encoding="utf-8") as f:
                f.write(linha + "\n")
        except Exception:
            pass

    def _enviar_para_api(self, nivel: str, mensagem: str, dados: dict = None):
        """Envia o log para a API de monitoramento"""

        if not API_URL or not API_TOKEN:
            return

        payload = {
            "bot_name": self.nome_rpa,
            "exec_id": self.exec_id,
            "bot_flag": "RPA",
            "flag": nivel,
            "content_line": mensagem,
            "codi_emp": self.empresa_atual,
            "step": self.etapa_atual,
            "data": dados,
            "date_init": self.data_inicio.isoformat()
        }

        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            requests.post(API_URL, json=payload, headers=headers, timeout=30)
        except Exception:
            pass  # Ignora erros de envio

    # =========================================================================
    # MÉTODOS DE LOG
    # =========================================================================

    def debug(self, mensagem: str):
        """
        Log de debug (só aparece no terminal, não vai para API).

        Exemplo:
            logger.debug("Valor da variável: 123")
        """
        self._escrever_terminal("DEBUG", mensagem)

    def info(self, mensagem: str):
        """
        Log informativo.

        Exemplo:
            logger.info("Processamento iniciado")
        """
        self._escrever_terminal("INFO", mensagem)
        self._escrever_api("INFO", mensagem)
        self._enviar_para_api("INFO", mensagem)

    def warning(self, mensagem: str):
        """
        Log de aviso (algo inesperado mas não crítico).

        Exemplo:
            logger.warning("Arquivo não encontrado, usando padrão")
        """
        self._escrever_terminal("WARNING", mensagem)
        self._escrever_api("WARNING", mensagem)
        self._enviar_para_api("WARNING", mensagem)

    def error(self, mensagem: str):
        """
        Log de erro.

        Exemplo:
            logger.error("Falha ao conectar no banco de dados")
        """
        self._escrever_terminal("ERROR", mensagem)
        self._escrever_api("ERROR", mensagem)
        self._enviar_para_api("ERROR", mensagem)

    # =========================================================================
    # CONTEXTO
    # =========================================================================

    def set_empresa(self, codigo: str):
        """
        Define a empresa atual (aparece nos logs).

        Exemplo:
            logger.set_empresa("1234")
            logger.info("Processando")  # Vai mostrar [1234]
        """
        self.empresa_atual = str(codigo) if codigo else None

    def set_etapa(self, etapa: str):
        """
        Define a etapa atual (aparece nos logs).

        Exemplo:
            logger.set_etapa("Login")
            logger.info("Fazendo login")  # Vai mostrar [Login]
        """
        self.etapa_atual = etapa

    def limpar_contexto(self):
        """Remove empresa e etapa atuais"""
        self.empresa_atual = None
        self.etapa_atual = None

    # =========================================================================
    # CONTADORES
    # =========================================================================

    def set_total_empresas(self, total: int):
        """Define quantas empresas serão processadas"""
        self.total_empresas = total

    def set_total_itens(self, total: int):
        """Define quantos itens serão processados"""
        self.total_itens = total

    def incrementar_processada(self):
        """Marca mais uma empresa como processada"""
        self.empresas_processadas += 1

    def incrementar_erro(self):
        """Marca mais uma empresa como erro"""
        self.empresas_com_erro += 1

    def incrementar_pulada(self):
        """Marca mais uma empresa como pulada"""
        self.empresas_puladas += 1

    def incrementar_item_processado(self):
        """Marca mais um item como processado"""
        self.itens_processados += 1

    def incrementar_item_erro(self):
        """Marca mais um item como erro"""
        self.itens_com_erro += 1

    # =========================================================================
    # LOGS ESPECIAIS
    # =========================================================================

    def inicio(self, mensagem: str = None):
        """
        Log de início do RPA.

        Exemplo:
            logger.inicio()
            logger.inicio("Versão 1.0")
        """
        print("=" * 60)
        self.info(f"INICIANDO {self.nome_rpa}")
        if mensagem:
            self.info(mensagem)
        print("=" * 60)

    def fim(self, sucesso: bool = True):
        """
        Log de fim do RPA com resumo.

        Exemplo:
            logger.fim(sucesso=True)
            logger.fim(sucesso=False)
        """
        # Calcula duração
        data_fim = datetime.now(timezone.utc)
        duracao = (data_fim - self.data_inicio).total_seconds()
        duracao_min = duracao / 60

        status = "SUCESSO" if sucesso else "ERRO"

        print("=" * 60)
        self.info(f"{self.nome_rpa} FINALIZADO - {status}")

        # Mostra totais se tiver
        if self.total_empresas > 0:
            self.info(f"Empresas: {self.empresas_processadas}/{self.total_empresas}")
            if self.empresas_com_erro > 0:
                self.info(f"Com erro: {self.empresas_com_erro}")
            if self.empresas_puladas > 0:
                self.info(f"Puladas: {self.empresas_puladas}")

        if self.total_itens > 0:
            self.info(f"Itens: {self.itens_processados}/{self.total_itens}")
            if self.itens_com_erro > 0:
                self.info(f"Itens com erro: {self.itens_com_erro}")

        self.info(f"Duração: {duracao_min:.1f} minutos")
        print("=" * 60)

        # Envia resumo final para API
        resumo = {
            "status": status.lower(),
            "duracao_segundos": duracao,
            "empresas_processadas": self.empresas_processadas,
            "empresas_com_erro": self.empresas_com_erro,
            "empresas_puladas": self.empresas_puladas
        }
        self._enviar_para_api("INFO" if sucesso else "ERROR", f"FIM - {status}", resumo)

    def progresso(self, atual: int, total: int, mensagem: str = ""):
        """
        Log de progresso.

        Exemplo:
            logger.progresso(5, 100, "Processando empresa")
            # Mostra: [5/100] (5%) Processando empresa
        """
        percentual = (atual / total * 100) if total > 0 else 0
        texto = f"[{atual}/{total}] ({percentual:.0f}%)"
        if mensagem:
            texto += f" {mensagem}"
        self.info(texto)


# =============================================================================
# INSTÂNCIA GLOBAL
# =============================================================================

# Logger padrão (pode ser reconfigurado com configurar_logger)
logger = Logger()


def configurar_logger(nome_rpa: str) -> Logger:
    """
    Configura o logger com o nome do RPA.

    Deve ser chamado no início do main.py.

    Exemplo:
        from core.logger import configurar_logger, logger

        configurar_logger("MeuRPA")
        logger.inicio()
    """
    global logger
    logger = Logger(nome_rpa=nome_rpa)
    return logger
