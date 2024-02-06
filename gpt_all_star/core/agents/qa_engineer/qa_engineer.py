from __future__ import annotations
import time
import requests
import subprocess
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from gpt_all_star.core.message import Message
from gpt_all_star.core.storage import Storages
from gpt_all_star.core.agents.agent import Agent, AgentRole
from gpt_all_star.core.agents.qa_engineer.planning_healing_prompt import (
    planning_healing_template,
)
from gpt_all_star.core.agents.qa_engineer.implement_planning_prompt import (
    implement_planning_template,
)
from gpt_all_star.tool.text_parser import TextParser


class QAEngineer(Agent):
    def __init__(
        self,
        storages: Storages,
        debug_mode: bool = False,
        name: str | None = None,
        profile: str | None = None,
    ) -> None:
        super().__init__(AgentRole.QA_ENGINEER, storages, debug_mode, name, profile)

    def execute_code(self, review_mode: bool = False) -> None:
        command = self.storages.root["run.sh"]
        self._confirm_execution(review_mode, command)
        self._run_command()

    def _confirm_execution(self, review_mode: bool, command: str) -> None:
        if review_mode:
            self.console.new_lines()
            CONFIRM_CHOICES = ["yes", "no"]
            choice = self.present_choices(
                "Do you want to execute this code?",
                CONFIRM_CHOICES,
                default=1,
            )
            self.console.new_lines()
            self.console.print(command)
            self.console.new_lines()
            if choice == CONFIRM_CHOICES[1]:
                print("Ok, not executing the code.")
                return []

        self.state("Executing the code...")
        self.console.new_lines()
        self.state(
            "If it does not work as expected, please consider running the code"
            + " in another way than above."
        )
        self.console.new_lines()
        self.console.print(
            "You can press ctrl+c *once* to stop the execution.", style="red"
        )
        self.console.new_lines()

    def _run_command(self) -> None:
        command = "bash run.sh"
        MAX_ATTEMPTS = 5
        for attempt in range(MAX_ATTEMPTS):
            self.state(f"Attempt {attempt + 1}/{MAX_ATTEMPTS}")
            try:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=self.storages.root.path,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                stdout_lines = []
                stderr_lines = []

                def read_stdout():
                    for line in iter(process.stdout.readline, ""):
                        stdout_lines.append(line.strip())
                        self.console.print(f"{line.strip()}", style="green")

                def read_stderr():
                    for line in iter(process.stderr.readline, ""):
                        stderr_lines.append(line.strip())
                        self.console.print(f"{line.strip()}", style="red")

                stdout_thread = threading.Thread(target=read_stdout)
                stderr_thread = threading.Thread(target=read_stderr)
                stdout_thread.start()
                stderr_thread.start()

                if self.wait_for_server():
                    self.check_browser_errors()
                    return

                stdout_thread.join()
                stderr_thread.join()

                return_code = process.wait()
                if return_code != 0:
                    self._handle_error(
                        {
                            "stdout": "\n".join(stdout_lines),
                            "stderr": "\n".join(stderr_lines),
                        }
                    )
                process.terminate()
            except KeyboardInterrupt:
                self._handle_keyboard_interrupt()
                break

    def wait_for_server(self) -> bool:
        MAX_ATTEMPTS = 30
        for attempt in range(MAX_ATTEMPTS):
            try:
                response = requests.get("http://localhost:3000")
                if response.status_code == 200:
                    return True
            except requests.ConnectionError:
                pass
            time.sleep(1)
        self.state("Unable to confirm server startup")
        return False

    def check_browser_errors(self):
        """Access the site with a headless browser and catch console errors"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("http://localhost:3000")

        errors = ""
        for entry in driver.get_log("browser"):
            if entry["level"] == "SEVERE":
                self.console.print(f"Error: {entry['message']}", style="red")
                errors += f"{entry['message']}\n"
        driver.quit()
        if errors:
            self._handle_error({"browser errors": errors})

    def _handle_error(self, e: dict) -> None:
        self.state("Initiating source code correction process.")

        self.messages.append(
            Message.create_system_message(
                planning_healing_template.format(
                    errors=e,
                    codes=self.current_source_code(),
                    json_format="""
{
    "plan": {
        "type": "array",
        "description": "List of tasks to fix the errors.",
        "items": {
            "type": "object",
            "description": "Task to fix the errors.",
            "properties": {
                "todo": {
                    "type": "string",
                    "description": "Very detailed description of the actual TODO to be performed to accomplish the entire plan.",
                },
                "goal": {
                    "type": "string",
                    "description": "Very detailed description of the goals to be achieved for the TODO to be executed to accomplish the entire plan",
                }
            },
            "required": ["todo", "goal"],
        },
    }
}
""",
                    example="""
------------------------example_1---------------------------
```
{
    "plan": [
        {
            "todo": "",
            "goal": "",
        },
        {
            "todo": "",
            "goal": "",
        }
    ]
}
```
------------------------example_1---------------------------
""",
                )
            )
        )
        self.invoke()
        self.console.new_lines(2)

        todo_list = TextParser.to_json(self.latest_message_content())

        for i, task in enumerate(todo_list["plan"]):
            self.state(
                f"""
TODO {i + 1}: {task['todo']}")
GOAL: {task['goal']}
---
"""
            )

            previous_finished_task_message = f"""The information given to you is as follows.
There are the specifications to build the application:
```
{self.storages.docs["specifications.md"]}
```

There are the source codes generated so far:
```
{self.current_source_code()}
```
"""
            self.messages.append(
                Message.create_system_message(
                    implement_planning_template.format(
                        todo_description=task["todo"],
                        finished_todo_message=previous_finished_task_message,
                        todo_goal=task["goal"],
                    )
                )
            )
            self.invoke()
            self.console.new_lines(2)
            files = TextParser.parse_code_from_text(self.latest_message_content())
            for file_name, file_content in files:
                self.storages.root[file_name] = file_content

    def _handle_keyboard_interrupt(self) -> None:
        self.console.new_lines()
        self.console.print("Stopping execution.", style="bold yellow")
        self.console.print("Execution stopped.", style="bold red")
        self.console.new_lines()
