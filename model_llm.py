from langchain_community.llms import Ollama
import requests
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelLLM(Ollama):
    """
    Custom LLM class untuk memanggil API Ollama, dengan support system prompt.
    """
    model: str = "gemma3"
    base_url: str = "http://localhost:11434"
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1024, gt=0)
    db_type: Optional[str] = Field(default=None, description="Tipe database (Oracle, MySQL, PostgreSQL, SQLServer)")

    def _call(self, prompt: str, stop: Optional[list] = None) -> str:
        """
        Mengirim request ke LLM API dan mengembalikan respon.
        """
        try:
            logger.info(f"Sending request to LLM API with prompt length {len(prompt)} chars")
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stop": stop or [],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                },
                timeout=30  # lebih panjang timeout agar lebih stabil
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error while calling LLM API: {e}")
            raise RuntimeError("Gagal menghubungi LLM API.") from e

    def invoke(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Invoke LLM dengan input data (dan system prompt jika diberikan).
        """
        prompt = input_data.get("input", "")
        system_prompt = input_data.get("system_prompt", "")

        if not prompt:
            raise ValueError("Input prompt tidak boleh kosong.")

        final_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        response = self._call(final_prompt, stop=kwargs.get("stop", []))
        return {"output": response}

    @property
    def _llm_type(self) -> str:
        """
        Return type model.
        """
        return self.model
