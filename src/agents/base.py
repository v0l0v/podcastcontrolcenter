from abc import ABC, abstractmethod
from typing import Any

class BaseAgent(ABC):
    """
    Clase base abstracta para todos los agentes del sistema.
    Define la interfaz común que deben implementar.
    """

    def __init__(self, name: str = "BaseAgent"):
        self.name = name

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        Método principal de ejecución del agente.
        Debe ser implementado por todas las subclases.
        """
        pass
