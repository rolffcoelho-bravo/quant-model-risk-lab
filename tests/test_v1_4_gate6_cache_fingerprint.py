from __future__ import annotations

import json

from qmrl.operations import (
    FileCache,
    canonical_json,
    content_hash,
    deterministic_cache_key,
)


def test_canonical_hash_is_mapping_order_invariant():
    left = {"b": [2, 3], "a": 1}
    right = {"a": 1, "b": [2, 3]}
    assert canonical_json(left) == canonical_json(right)
    assert content_hash(left) == content_hash(right)


def test_cache_key_changes_when_quantitative_input_changes():
    common = {
        "node_id": "exposure",
        "dependency_hashes": {"fx": content_hash({"x": 1})},
        "policy_hash": content_hash({"p": 1}),
        "engine_version": "1.4-gate6",
        "seed": 7,
    }
    first = deterministic_cache_key(external_input={"v": 1.0}, scope="netting_set", **common)
    second = deterministic_cache_key(external_input={"v": 2.0}, scope="netting_set", **common)
    assert first != second


def test_file_cache_round_trip_is_hash_verified(tmp_path):
    cache = FileCache(tmp_path)
    key = content_hash({"key": 1})
    metadata = {"node_id": "x", "input_hash": content_hash({"i": 1})}
    output_hash = cache.put(key, {"value": 3.5}, metadata)
    lookup = cache.get(key, expected_metadata=metadata)
    assert lookup.status == "HIT"
    assert lookup.value == {"value": 3.5}
    assert lookup.output_hash == output_hash


def test_file_cache_detects_stale_metadata(tmp_path):
    cache = FileCache(tmp_path)
    key = content_hash({"key": 2})
    cache.put(key, {"value": 1.0}, {"engine_version": "old"})
    lookup = cache.get(key, expected_metadata={"engine_version": "new"})
    assert lookup.status == "STALE"
    assert lookup.value is None


def test_file_cache_detects_corruption(tmp_path):
    cache = FileCache(tmp_path)
    key = content_hash({"key": 3})
    cache.put(key, {"value": 1.0}, {"node": "x"})
    path = next(tmp_path.rglob(f"{key}.json"))
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["value"]["value"] = 999.0
    path.write_text(json.dumps(envelope), encoding="utf-8")
    assert cache.get(key).status == "CORRUPT"


def test_file_cache_invalidation_removes_only_requested_keys(tmp_path):
    cache = FileCache(tmp_path)
    keys = [content_hash({"key": index}) for index in range(3)]
    for index, key in enumerate(keys):
        cache.put(key, {"value": index}, {"index": index})
    assert cache.invalidate((keys[0], keys[2])) == 2
    assert cache.keys() == (keys[1],)
