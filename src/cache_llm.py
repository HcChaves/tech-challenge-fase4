"""Cache em disco das respostas da LLM: repetir uma entrada idêntica não gasta cota."""

import hashlib
import json
from pathlib import Path

from langchain_core.caches import RETURN_VAL_TYPE, BaseCache
from langchain_core.load import dumps, loads

RAIZ = Path(__file__).resolve().parent.parent
CACHE_DIR = RAIZ / "data" / "cache_llm"


class CacheEmDisco(BaseCache):
    """Um arquivo JSON por entrada. A chave inclui o modelo e seus parâmetros (llm_string)."""

    def __init__(self, diretorio: Path = CACHE_DIR) -> None:
        self.diretorio = diretorio
        self.diretorio.mkdir(parents=True, exist_ok=True)

    def _arquivo(self, prompt: str, llm_string: str) -> Path:
        chave = hashlib.sha256((llm_string + "\x00" + prompt).encode("utf-8")).hexdigest()
        return self.diretorio / f"{chave}.json"

    def lookup(self, prompt: str, llm_string: str) -> RETURN_VAL_TYPE | None:
        arquivo = self._arquivo(prompt, llm_string)
        if not arquivo.exists():
            return None
        try:
            return [loads(item) for item in json.loads(arquivo.read_text(encoding="utf-8"))]
        except Exception:
            return None  # arquivo corrompido: trata como se não existisse

    def update(self, prompt: str, llm_string: str, return_val: RETURN_VAL_TYPE) -> None:
        itens = [dumps(geracao) for geracao in return_val]
        self._arquivo(prompt, llm_string).write_text(json.dumps(itens), encoding="utf-8")

    def clear(self, **kwargs) -> None:
        for arquivo in self.diretorio.glob("*.json"):
            arquivo.unlink()