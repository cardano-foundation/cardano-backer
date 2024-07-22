from enum import Enum


class TraitCodex(Enum):
    EstOnly: str = "EO"  # Only allow establishment events
    DoNotDelegate: str = "DND"  # Dot not allow delegated identifiers
    NoBackers: str = "NB"  # Do not allow any backers for registry
    RegistryBackers: str = "RB"  # Do not allow any backers for registry
