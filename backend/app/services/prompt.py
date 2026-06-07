import logging
import os
from typing import Any

import yaml
from jinja2 import Template

logger = logging.getLogger(__name__)


class PromptService:
    """Service for managing and formatting LLM prompt templates."""

    def __init__(self, prompts_dir: str = None):
        if prompts_dir is None:
            # Default to app/prompts
            base_dir = os.path.dirname(os.path.dirname(__file__))
            prompts_dir = os.path.join(base_dir, "prompts")

        self.prompts_dir = prompts_dir
        self._cache: dict[str, dict[str, Any]] = {}

    def _load_template(self, name: str) -> dict[str, Any]:
        """Load a prompt template from YAML file."""
        if name in self._cache:
            return self._cache[name]

        file_path = os.path.join(self.prompts_dir, f"{name}.yaml")
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"Prompt template '{name}' not found at {file_path}"
            )

        try:
            with open(file_path) as f:
                template_data = yaml.safe_load(f)
                self._cache[name] = template_data
                return template_data
        except Exception as e:
            logger.error(f"Error loading prompt template '{name}': {e}")
            raise

    def format_prompt(
        self, name: str, variables: dict[str, Any]
    ) -> list[dict[str, str]]:
        """
        Format a prompt template with provided variables.
        Returns a list of message objects for the LLM.
        """
        template_data = self._load_template(name)

        messages = []

        # Format System Message
        if "system_template" in template_data:
            system_tmpl = Template(template_data["system_template"])
            system_content = system_tmpl.render(**variables)
            messages.append({"role": "system", "content": system_content})

        # Format User Message
        if "user_template" in template_data:
            user_tmpl = Template(template_data["user_template"])
            user_content = user_tmpl.render(**variables)
            messages.append({"role": "user", "content": user_content})

        return messages


prompt_service = PromptService()
