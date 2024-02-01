from gpt_all_star.core.agents.agents import Agents
from gpt_all_star.core.steps.step import Step


class SystemDesign(Step):
    def __init__(
        self, agents: Agents, japanese_mode: bool, auto_mode: bool, debug_mode: bool
    ) -> None:
        super().__init__(agents, japanese_mode, auto_mode, debug_mode)

    def run(self) -> None:
        self.agents.architect.create_system_design(auto_mode=self.auto_mode)
        self.console.new_lines()
