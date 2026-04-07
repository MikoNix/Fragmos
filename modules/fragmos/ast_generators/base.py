from abc import ABC, abstractmethod


class ASTGenerator(ABC):
    """Base class for language-specific AST generators."""

    @abstractmethod
    def generate(self, code: str) -> dict:
        """
        Parse source code into unified AST dict.

        Returns:
            {
                "type": "program",
                "body": [...],
                "metadata": {"language": "python|csharp|cpp"}
            }

        Raises:
            SyntaxError: if source code has parse errors.
        """
        pass
