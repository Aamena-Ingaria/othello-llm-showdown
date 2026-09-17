from abc import ABC

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from groq import Groq
except ImportError:
    Groq = None

import logging
from typing import Dict, Type, Self, List
import os
import time
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass


logger = logging.getLogger(__name__)


class LLMException(Exception):
    pass


class LLM(ABC):
    """
    An abstract superclass for interacting with LLMs - subclass for Claude and GPT
    """

    model_names = []

    def __init__(self, model_name: str, temperature: float):
        self.model_name = model_name
        self.client = None
        self.temperature = temperature
        self.reasoning_effort = None

    def send(self, system: str, user: str, max_tokens: int = 3000) -> str:
        """
        Send a message
        :param system: the context in which this message is to be taken
        :param user: the prompt
        :param max_tokens: max number of tokens to generate
        :return: the response from the AI
        """

        result = self.protected_send(system, user, max_tokens)
        left = result.find("{")
        right = result.rfind("}")
        if left > -1 and right > -1:
            result = result[left : right + 1]
        return result

    def protected_send(self, system: str, user: str, max_tokens: int = 3000) -> str:
        """
        Wrap the send call in an exception handler, giving the LLM 3 chances in total, in case
        of overload errors. If it fails 3 times, then it forfeits!
        """
        retries = 3
        while retries:
            retries -= 1
            try:
                return self._send(system, user, max_tokens)
            except Exception as e:
                logging.error(f"Exception on calling LLM of {e}")
                if retries:
                    logging.warning("Waiting 2s and retrying")
                    time.sleep(2)
        return "{}"

    def _send(self, system: str, user: str, max_tokens: int = 3000) -> str:
        """
        Send a message to the model - this default implementation follows the OpenAI API structure
        :param system: the context in which this message is to be taken
        :param user: the prompt
        :param max_tokens: max number of tokens to generate
        :return: the response from the AI
        """
        if self.reasoning_effort:
            response = self.client.chat.completions.create(
                model=self.api_model_name(),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                reasoning_effort=self.reasoning_effort,
            )
        else:
            response = self.client.chat.completions.create(
                model=self.api_model_name(),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
            )
        return response.choices[0].message.content

    def api_model_name(self) -> str:
        """
        Return the actual model_name to be used in the call to the API; strip out anything after a space
        """
        if " " in self.model_name:
            return self.model_name.split(" ")[0]
        else:
            return self.model_name

    @classmethod
    def model_map(cls) -> Dict[str, Type[Self]]:
        """
        Generate a mapping of Model Names to LLM classes, by looking at all subclasses of this one
        :return: a mapping dictionary from model name to LLM subclass
        """
        mapping = {}
        for llm in cls.__subclasses__():
            for model_name in llm.model_names:
                mapping[model_name] = llm
        return mapping

    @classmethod
    def all_supported_model_names(cls) -> List[str]:
        """
        Return a list of all the model names supported by all subclasses of this one.
        """
        return list(cls.model_map().keys())

    @classmethod
    def all_model_names(cls) -> List[str]:
        """
        Return a list of all model names supported.
        Returns only the requested local Ollama models (no paid API models).
        """
        allowed = os.getenv("MODELS")
        if allowed:
            allowed_models = [m.strip() for m in allowed.split(",")]
            return allowed_models
        return ["llama3.2:3b", "llama3.2:1b", "qwen2.5-coder:7b", "qwen2.3-coder:7b"]

    @classmethod
    def create(cls, model_name: str, temperature: float = 0.5) -> Self:
        """
        Return an instance of a subclass that corresponds to this model_name
        :param model_name: a string to describe this model
        :param temperature: the creativity setting
        :return: a new instance of a subclass of LLM
        """
        subclass = cls.model_map().get(model_name)
        if not subclass:
            raise LLMException(f"Unrecognized LLM model name specified: {model_name}")
        return subclass(model_name, temperature)


class Claude(LLM):
    """
    Claude interface (disabled: paid API)
    """

    model_names = []

    def __init__(self, model_name: str, temperature: float):
        """
        Create a new instance of the Anthropic client
        """
        super().__init__(model_name, temperature)
        self.client = Anthropic()

    def _send(self, system: str, user: str, max_tokens: int = 3000) -> str:
        """
        Send a message to Claude
        :param system: the context in which this message is to be taken
        :param user: the prompt
        :param max_tokens: max number of tokens to generate
        :return: the response from the AI
        """
        response = self.client.messages.create(
            model=self.api_model_name(),
            max_tokens=max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[
                {"role": "user", "content": user},
            ],
        )
        return response.content[0].text


class GPT(LLM):
    """
    GPT interface (disabled: paid API)
    """

    model_names = []

    def __init__(self, model_name: str, temperature: float):
        """
        Create a new instance of the OpenAI client
        """
        super().__init__(model_name, temperature)
        self.client = OpenAI()
        if "gpt-5" in model_name:
            self.reasoning_effort = "low"


class O1(LLM):
    """
    A class to act as an interface to the remote AI, in this case O1
    """

    model_names = []

    def __init__(self, model_name: str, temperature: float):
        """
        Create a new instance of the OpenAI client
        """
        super().__init__(model_name, temperature)
        self.client = OpenAI()

    def _send(self, system: str, user: str, max_tokens: int = 3000) -> str:
        """
        Send a message to O1
        :param system: the context in which this message is to be taken
        :param user: the prompt
        :param max_tokens: max number of tokens to generate
        :return: the response from the AI
        """
        message = system + "\n\n" + user
        response = self.client.chat.completions.create(
            model=self.api_model_name(),
            messages=[
                {"role": "user", "content": message},
            ],
        )
        return response.choices[0].message.content


class O3(LLM):
    """
    A class to act as an interface to the remote AI, in this case O3
    """

    model_names = []

    def __init__(self, model_name: str, temperature: float):
        """
        Create a new instance of the OpenAI client
        """
        super().__init__(model_name, temperature)
        override = os.getenv("OPENAI_API_KEY_O3")
        if override:
            print("Using special key with o3 access")
            self.client = OpenAI(api_key=override)
        else:
            self.client = OpenAI()

    def _send(self, system: str, user: str, max_tokens: int = 3000) -> str:
        """
        Send a message to O3
        :param system: the context in which this message is to be taken
        :param user: the prompt
        :param max_tokens: max number of tokens to generate
        :return: the response from the AI
        """
        message = system + "\n\n" + user
        response = self.client.chat.completions.create(
            model=self.api_model_name(),
            messages=[
                {"role": "user", "content": message},
            ],
        )
        return response.choices[0].message.content


class Gemini(LLM):
    """
    Gemini interface (disabled: paid API)
    """

    model_names = []

    def __init__(self, model_name: str, temperature: float):
        """
        Create a new instance of the OpenAI client
        """
        super().__init__(model_name, temperature)
        google_api_key = os.getenv("GOOGLE_API_KEY")
        self.client = OpenAI(
            api_key=google_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )


class Ollama(LLM):
    """
    A class to act as an interface to local Ollama models (100% free, private & offline)
    """

    model_names = [
        "llama3.2:3b",
        "llama3.2:1b",
        "qwen2.5-coder:7b",
        "qwen2.3-coder:7b",
    ]

    def __init__(self, model_name: str, temperature: float = 0.2):
        """
        Create a new instance of the client for Ollama
        """
        super().__init__(model_name, temperature)
        if OpenAI is not None:
            self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        else:
            self.client = None

    def api_model_name(self) -> str:
        name = self.model_name.split(" ")[0] if " " in self.model_name else self.model_name
        # Seamlessly map user typo qwen2.3-coder to installed qwen2.5-coder
        if name == "qwen2.3-coder:7b":
            return "qwen2.5-coder:7b"
        return name

    def _send(self, system: str, user: str, max_tokens: int = 3000) -> str:
        """
        Send a message to Ollama
        """
        model = self.api_model_name()
        if self.client is not None:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
            )
            reply = response.choices[0].message.content
        else:
            import urllib.request
            import json
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "response_format": {"type": "json_object"},
            }
            req = urllib.request.Request(
                "http://localhost:11434/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data["choices"][0]["message"]["content"]

        if "</think>" in reply:
            logging.info("Thoughts:\n" + reply.split("</think>")[0].replace("<think>", ""))
            reply = reply.split("</think>")[1]
        return reply


class DeepSeekAPI(LLM):
    """
    DeepSeek API interface (disabled: paid API)
    """

    model_names = []

    def __init__(self, model_name: str, temperature: float):
        """
        Create a new instance of the OpenAI client
        """
        super().__init__(model_name, temperature)
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")


class DeepSeekLocal(LLM):
    """
    A class to act as an interface to the remote AI, in this case Ollama via the OpenAI client
    """

    model_names = []

    def __init__(self, model_name: str, temperature: float):
        """
        Create a new instance of the OpenAI client
        """
        super().__init__(model_name, temperature)
        self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    def _send(self, system: str, user: str, max_tokens: int = 3000) -> str:
        """
        Send a message to Ollama
        :param system: the context in which this message is to be taken
        :param user: the prompt
        :param max_tokens: max number of tokens to generate
        :return: the response from the AI
        """
        system += "\nImportant: avoid overthinking. Think briefly and decisively. The final response must follow the given json format or you forfeit the game. Do not overthink. Respond with json."
        user += "\nImportant: avoid overthinking. Think briefly and decisively. The final response must follow the given json format or you forfeit the game. Do not overthink. Respond with json."
        response = self.client.chat.completions.create(
            model=self.api_model_name(),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        reply = response.choices[0].message.content
        if "</think>" in reply:
            logging.info("Thoughts:\n" + reply.split("</think>")[0].replace("<think>", ""))
            reply = reply.split("</think>")[1]
        return reply


class GroqAPI(LLM):
    """
    Groq API interface (disabled: paid API)
    """

    model_names = []

    def __init__(self, model_name: str, temperature: float):
        """
        Create a new instance of the Groq client
        """
        super().__init__(model_name, temperature)
        self.client = Groq()
