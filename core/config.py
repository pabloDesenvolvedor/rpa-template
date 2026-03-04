"""
Módulo de Configuração do RPA
Gerencia configurações do sistema através de arquivo JSON
"""

import json
from pathlib import Path
from typing import Any, Dict


class Config:
    """Gerenciador de configurações"""

    DEFAULTS = {
        "precisao_padrao": 0.8,
        "tempo_maximo_padrao": 10,
        "intervalo_busca": 0.5,
        "pyautogui_pause": 0.1,
        "nivel_log": "INFO",
        "salvar_screenshots_erro": True,
    }

    def __init__(self, arquivo: str = "config.json"):
        self.arquivo = Path(arquivo)
        self._config: Dict[str, Any] = {}
        self._carregar()

    def _carregar(self):
        """Carrega configurações do arquivo ou usa defaults"""
        if self.arquivo.exists():
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception:
                self._config = {}

        # Aplica defaults para valores não definidos
        for chave, valor in self.DEFAULTS.items():
            if chave not in self._config:
                self._config[chave] = valor

    def salvar(self):
        """Salva configurações no arquivo"""
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    def get(self, chave: str, padrao: Any = None) -> Any:
        """Obtém um valor de configuração"""
        return self._config.get(chave, padrao)

    def set(self, chave: str, valor: Any):
        """Define um valor de configuração"""
        self._config[chave] = valor

    def __getitem__(self, chave: str) -> Any:
        return self._config[chave]

    def __setitem__(self, chave: str, valor: Any):
        self._config[chave] = valor


# Instância global
config = Config()
