"""Project-level adapter: config, graph, validation status."""

from __future__ import annotations

from typing import Any

from pakunoda_mcp.reader import ProjectReader


class ProjectAdapter:
    """Read project config, relation graph, and validation state."""

    def __init__(self, reader: ProjectReader) -> None:
        self._reader = reader

    def project_id(self) -> str | None:
        """Return the current project id, or None if unavailable."""
        return self._reader.project_id()

    def config(self) -> dict[str, Any]:
        """Return the project configuration."""
        return self._reader.config()

    def relation_graph(self) -> dict[str, Any]:
        """Return the block-mode relation graph."""
        return self._reader.relation_graph()

    def summary(self) -> dict[str, Any]:
        """Return the project summary (summary.json)."""
        return self._reader.summary()

    def refresh(self) -> dict[str, Any]:
        """Re-read all project state and return a snapshot.

        Returns a dict with the current value (or None/error string)
        for each major output: config, graph, candidates, search summary.
        """
        snapshot: dict[str, Any] = {"project_id": self._reader.project_id()}
        for key, fn in [
            ("config", self._reader.config),
            ("relation_graph", self._reader.relation_graph),
            ("candidates", self._reader.candidates),
            ("summary", self._reader.summary),
        ]:
            try:
                snapshot[key] = fn()
            except FileNotFoundError:
                snapshot[key] = None
            except Exception as e:
                snapshot[key] = f"error: {e}"

        # Search is optional — wrap separately.
        try:
            snapshot["search_recommendation"] = self._reader.search_recommendation()
        except FileNotFoundError:
            snapshot["search_recommendation"] = None
        except Exception as e:
            snapshot["search_recommendation"] = f"error: {e}"

        return snapshot

    def file_status(self) -> dict[str, str]:
        """Check which output files are present and readable.

        Returns a dict mapping logical names to "ok", "missing",
        or "error: <message>".
        """
        checks: dict[str, Any] = {
            "config": self._reader.config,
            "relation_graph": self._reader.relation_graph,
            "candidates": self._reader.candidates,
            "validation_report": self._reader.validation_report,
            "summary": self._reader.summary,
            "search/recommendation": self._reader.search_recommendation,
            "search/best": self._reader.search_best,
            "search/trials": self._reader.search_trials,
        }
        status: dict[str, str] = {}
        for name, fn in checks.items():
            try:
                fn()
                status[name] = "ok"
            except FileNotFoundError:
                status[name] = "missing"
            except Exception as e:
                status[name] = f"error: {e}"
        return status
