from abc import ABC, abstractmethod


class BaseCommand(ABC):
    action: str = ""

    @abstractmethod
    def execute(self, params: dict, context: dict) -> dict:
        ...
