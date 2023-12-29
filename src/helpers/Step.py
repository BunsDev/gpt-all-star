from rich.console import Console

from helpers.Agents import Agents
from helpers.Storage import Storages

NEXT_COMMAND = "next"


class Step:
    def __init__(self, agents: Agents, storages: Storages) -> None:
        self.agents = agents
        self.storages = storages
        self.console = Console()

        self.console.rule(f"STEP: {self.__class__.__name__}")
