from __future__ import annotations

import os.path
from pathlib import Path

from gpt_all_star.core.agents.agents import Agents
from gpt_all_star.core.agents.architect import Architect
from gpt_all_star.core.agents.copilot import Copilot
from gpt_all_star.core.agents.designer import Designer
from gpt_all_star.core.agents.engineer import Engineer
from gpt_all_star.core.steps.steps import StepType, STEPS
from gpt_all_star.core.storage import Storage, Storages
from gpt_all_star.core.agents.product_owner import ProductOwner
from gpt_all_star.logger.logger import logger


class Project:
    def __init__(
        self,
        step: StepType = StepType.DEFAULT,
        project_name: str = None,
        japanese_mode: bool = False,
    ) -> None:
        self.japanese_mode = japanese_mode
        self.name = (
            project_name
            or Copilot(
                storages=None, name="copilot", profile="this is copilot"
            ).ask_project_name()
        )

        project_path = Path(os.path.abspath(f"projects/{self.name}")).absolute()
        self.storages = Storages(
            origin=Storage(project_path),
            docs=Storage(project_path / "docs"),
            archive=Storage(project_path / ".archive"),
        )

        self.agents = Agents(
            copilot=Copilot(storages=self.storages),
            product_owner=ProductOwner(storages=self.storages),
            engineer=Engineer(storages=self.storages),
            architect=Architect(storages=self.storages),
            designer=Designer(storages=self.storages),
        )

        self.step_type = step or StepType.DEFAULT
        if self.step_type is StepType.DEFAULT:
            logger.info("archive previous storages")
            Storages.archive_storage(self.storages)

    def start(self) -> None:
        self.agents.copilot.start(self.name)
        try:
            for step in STEPS[self.step_type]:
                try:
                    step(self.agents, self.japanese_mode).run()
                except Exception as e:
                    logger.error(f"Failed to execute step {step}. Reason: {str(e)}")
                    raise e
        except KeyboardInterrupt:
            logger.info("Interrupt received! Stopping...")
            pass

    def finish(self) -> None:
        self.agents.copilot.finish()
        pass