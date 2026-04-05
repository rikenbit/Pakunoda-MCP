"""Adapter layer: translates Pakunoda file outputs into domain objects.

Each adapter takes a ProjectReader and returns structured dicts
that are independent of file layout details.
"""

from pakunoda_mcp.adapters.candidates import CandidatesAdapter
from pakunoda_mcp.adapters.project import ProjectAdapter
from pakunoda_mcp.adapters.search import SearchAdapter

__all__ = ["CandidatesAdapter", "ProjectAdapter", "SearchAdapter"]
