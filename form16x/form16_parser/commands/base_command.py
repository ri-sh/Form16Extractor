"""
Base Command Interface - Common functionality for all commands.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class BaseCommand(ABC):
    """Abstract base class for all CLI commands."""
    
    def __init__(self):
        """Initialize base command with common dependencies."""
        self.verbose = False
        self.dummy_mode = False
    
    @abstractmethod
    def execute(self, args) -> int:
        """Execute the command with given arguments.
        
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        pass
    
    def setup_common_args(self, args) -> None:
        """Setup common arguments used across commands."""
        self.verbose = getattr(args, 'verbose', False)
        self.dummy_mode = getattr(args, 'dummy', False)
    
    def should_use_dummy_mode(self, file_path: Path, explicit_dummy: bool = False) -> bool:
        """Determine if dummy mode should be used."""
        return explicit_dummy or not file_path.exists()
    
    def log_verbose(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[VERBOSE] {message}")