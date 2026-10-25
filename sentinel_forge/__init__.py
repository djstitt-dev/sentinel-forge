"""Repository-local Sentinel Forge logical contract implementation.

This package is deliberately transport-, credential-, and deployment-neutral.
It implements only offline logical validation authorized for Forge repository work.
"""

from .contract import ContractBundle, ValidationIssue, ValidationResult

__all__ = ["ContractBundle", "ValidationIssue", "ValidationResult"]
