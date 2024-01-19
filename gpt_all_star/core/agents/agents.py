from dataclasses import dataclass

from gpt_all_star.core.agents.architect import Architect
from gpt_all_star.core.agents.copilot import Copilot
from gpt_all_star.core.agents.designer import Designer
from gpt_all_star.core.agents.engineer import Engineer
from gpt_all_star.core.agents.product_owner import ProductOwner


@dataclass
class Agents:
    copilot: Copilot
    product_owner: ProductOwner
    engineer: Engineer
    architect: Architect
    designer: Designer