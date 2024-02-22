import random
import string

from gpt_all_star.core.agents.agent import Agent, AgentRole
from gpt_all_star.core.storage import Storages
from gpt_all_star.helper.config_loader import load_configuration

APP_TYPES = ["Client-Side Web Application", "Full-Stack Web Application"]


class Copilot(Agent):
    def __init__(
        self,
        storages: Storages | None = None,
        debug_mode: bool = False,
        name: str | None = None,
        profile: str | None = None,
    ) -> None:
        super().__init__(AgentRole.COPILOT, storages, debug_mode, name, profile)

    def start(self, project_name: str) -> None:
        self.state(f"Let's start the project! ({project_name})")

    def finish(self, project_name: str) -> None:
        self.state(f"Completed the project! ({project_name})")

    def ask_project_name(self) -> str:
        default_project_name = "".join(
            random.choice(string.ascii_letters + string.digits) for i in range(15)
        )
        project_name = self.ask(
            "What is the name of the project?",
            is_required=False,
            default=default_project_name,
        )
        return project_name

    def confirm(self, confirmation: str) -> bool:
        CONFIRM_CHOICES = ["yes", "no"]
        choice = self.present_choices(
            confirmation,
            CONFIRM_CHOICES,
            default=1,
        )
        return choice == CONFIRM_CHOICES[0]

    def confirm_push(self) -> bool:
        return self.confirm("Proceed with commit and push to repository?")

    def load_instructions(
        self, file_path: str = "./gpt_all_star/instructions.yml"
    ) -> dict:
        return load_configuration(file_path)

    def get_instructions(self) -> str:
        instructions = self.load_instructions()
        instruction = instructions.get("instruction")
        if instruction:
            return instruction
        return self.ask(
            "What application do you want to build? Please describe it in as much detail as possible."
        )

    def get_app_type(self) -> str:
        instructions = self.load_instructions()
        app_type = instructions.get("app_type")
        if app_type:
            return app_type
        return self.present_choices(
            "What type of application do you want to build?",
            APP_TYPES,
            default=1,
        )

    def caution(self) -> None:
        self.state("Executing the code...")
        self.state(
            "If it does not work as expected, please consider running the code"
            + " in another way than above."
        )
        self.console.print(
            "You can press ctrl+c *once* to stop the execution.", style="red"
        )
