"""Atomic checkpoints and restartable execution state."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Mapping

from .fingerprint import canonical_json, content_hash


@dataclass(frozen=True)
class CheckpointState:
    run_id: str
    plan_hash: str
    node_status: Mapping[str, str]
    chunk_status: Mapping[str, str]
    node_output_hashes: Mapping[str, str]
    failures: Mapping[str, str]

    @property
    def pending_nodes(self) -> tuple[str, ...]:
        return tuple(sorted(key for key, value in self.node_status.items() if value != "COMPLETE"))

    @property
    def pending_chunks(self) -> tuple[str, ...]:
        return tuple(sorted(key for key, value in self.chunk_status.items() if value != "COMPLETE"))


class CheckpointStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, run_id: str) -> Path:
        value = run_id.strip()
        if not value or any(char in value for char in "/\\"):
            raise ValueError("run_id must be a safe non-empty identifier.")
        return self.root / f"{value}.json"

    def initialize(
        self,
        run_id: str,
        plan_hash: str,
        node_ids: tuple[str, ...],
        chunk_ids: tuple[str, ...] = (),
    ) -> CheckpointState:
        state = CheckpointState(
            run_id=run_id,
            plan_hash=plan_hash,
            node_status={node_id: "PENDING" for node_id in node_ids},
            chunk_status={chunk_id: "PENDING" for chunk_id in chunk_ids},
            node_output_hashes={},
            failures={},
        )
        self._write(state)
        return state

    def _write(self, state: CheckpointState) -> None:
        payload = {
            "run_id": state.run_id,
            "plan_hash": state.plan_hash,
            "node_status": dict(sorted(state.node_status.items())),
            "chunk_status": dict(sorted(state.chunk_status.items())),
            "node_output_hashes": dict(sorted(state.node_output_hashes.items())),
            "failures": dict(sorted(state.failures.items())),
        }
        envelope = {"payload": payload, "payload_hash": content_hash(payload)}
        path = self._path(state.run_id)
        temporary = path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(envelope))
            handle.write("\n")
        os.replace(temporary, path)

    def load(self, run_id: str) -> CheckpointState:
        path = self._path(run_id)
        if not path.exists():
            raise FileNotFoundError(path)
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            payload = envelope["payload"]
            if content_hash(payload) != envelope["payload_hash"]:
                raise ValueError("Checkpoint content hash mismatch.")
            return CheckpointState(
                run_id=payload["run_id"],
                plan_hash=payload["plan_hash"],
                node_status=payload["node_status"],
                chunk_status=payload["chunk_status"],
                node_output_hashes=payload["node_output_hashes"],
                failures=payload["failures"],
            )
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Checkpoint is unreadable.") from exc

    def mark_node(
        self,
        run_id: str,
        node_id: str,
        status: str,
        *,
        output_hash: str = "",
        failure: str = "",
    ) -> CheckpointState:
        state = self.load(run_id)
        if node_id not in state.node_status:
            raise KeyError(f"Unknown checkpoint node: {node_id}.")
        statuses = dict(state.node_status)
        outputs = dict(state.node_output_hashes)
        failures = dict(state.failures)
        statuses[node_id] = status
        if status == "COMPLETE":
            if not output_hash:
                raise ValueError("Completed nodes require output_hash.")
            outputs[node_id] = output_hash
            failures.pop(node_id, None)
        elif status == "FAILED":
            failures[node_id] = failure or "unspecified_failure"
        updated = CheckpointState(
            run_id=state.run_id,
            plan_hash=state.plan_hash,
            node_status=statuses,
            chunk_status=state.chunk_status,
            node_output_hashes=outputs,
            failures=failures,
        )
        self._write(updated)
        return updated

    def mark_chunk(self, run_id: str, chunk_id: str, status: str) -> CheckpointState:
        state = self.load(run_id)
        if chunk_id not in state.chunk_status:
            raise KeyError(f"Unknown checkpoint chunk: {chunk_id}.")
        statuses = dict(state.chunk_status)
        statuses[chunk_id] = status
        updated = CheckpointState(
            run_id=state.run_id,
            plan_hash=state.plan_hash,
            node_status=state.node_status,
            chunk_status=statuses,
            node_output_hashes=state.node_output_hashes,
            failures=state.failures,
        )
        self._write(updated)
        return updated
