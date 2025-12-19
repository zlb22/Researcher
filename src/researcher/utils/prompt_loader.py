"""Prompt loading utilities for the Researcher system.

This module provides utilities for loading and managing system prompts.
"""

from pathlib import Path

from loguru import logger


class PromptLoader:
    """Loads system prompts from files.

    Prompts are stored in the prompts/ directory as .txt files.
    This allows easy editing and version control of prompts.

    Example:
        >>> loader = PromptLoader()
        >>> prompt = loader.load("orchestrator")
        >>> print(prompt[:50])
        "You are a research orchestrator..."
    """

    def __init__(self, prompts_dir: str | Path | None = None):
        """Initialize the prompt loader.

        Args:
            prompts_dir: Directory containing prompt files.
                        If None, uses src/researcher/prompts/
        """
        if prompts_dir is None:
            # Default to src/researcher/prompts/
            this_file = Path(__file__).resolve()
            researcher_root = this_file.parent.parent
            prompts_dir = researcher_root / "prompts"

        self.prompts_dir = Path(prompts_dir).resolve()
        logger.debug(f"PromptLoader initialized: {self.prompts_dir}")

    def load(self, prompt_name: str) -> str:
        """Load a prompt from file.

        Args:
            prompt_name: Name of the prompt (without .txt extension)
                        e.g., "orchestrator", "searcher", "analyzer"

        Returns:
            Prompt content as string

        Raises:
            FileNotFoundError: If prompt file doesn't exist
            Exception: If file cannot be read

        Example:
            >>> loader = PromptLoader()
            >>> orchestrator_prompt = loader.load("orchestrator")
        """
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"

        if not prompt_file.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_file}\n"
                f"Expected location: {self.prompts_dir}/{prompt_name}.txt"
            )

        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                content = f.read().strip()

            logger.debug(f"Loaded prompt '{prompt_name}' ({len(content)} chars)")
            return content

        except Exception as e:
            logger.error(f"Error loading prompt '{prompt_name}': {e}")
            raise

    def save(self, prompt_name: str, content: str) -> None:
        """Save a prompt to file.

        Args:
            prompt_name: Name of the prompt (without .txt extension)
            content: Prompt content to save

        Raises:
            Exception: If file cannot be written

        Example:
            >>> loader = PromptLoader()
            >>> loader.save("my_agent", "You are a helpful assistant.")
        """
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"

        try:
            # Create prompts directory if it doesn't exist
            self.prompts_dir.mkdir(parents=True, exist_ok=True)

            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Saved prompt '{prompt_name}' to {prompt_file} ({len(content)} chars)")

        except Exception as e:
            logger.error(f"Error saving prompt '{prompt_name}': {e}")
            raise

    def list_prompts(self) -> list[str]:
        """List all available prompt names.

        Returns:
            List of prompt names (without .txt extension)

        Example:
            >>> loader = PromptLoader()
            >>> prompts = loader.list_prompts()
            >>> print(prompts)
            ['orchestrator', 'searcher', 'analyzer', 'writer']
        """
        if not self.prompts_dir.exists():
            return []

        prompt_files = self.prompts_dir.glob("*.txt")
        return sorted([f.stem for f in prompt_files])

    def exists(self, prompt_name: str) -> bool:
        """Check if a prompt file exists.

        Args:
            prompt_name: Name of the prompt (without .txt extension)

        Returns:
            True if prompt file exists, False otherwise

        Example:
            >>> loader = PromptLoader()
            >>> if loader.exists("orchestrator"):
            ...     prompt = loader.load("orchestrator")
        """
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        return prompt_file.exists()
