"""
Pytest test suite for the Day 3 reference implementation.

Run the FastAPI server first:
    uv run fastapi dev main.py

Then run the tests:
    uv run pytest test_main.py -v
"""

from datetime import datetime, timedelta

import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture(scope="session", autouse=True)
def _require_server():
    """Skip the entire suite if the API is not reachable."""
    try:
        requests.get(f"{BASE_URL}/", timeout=2)
    except requests.exceptions.RequestException as exc:
        pytest.skip(f"API not reachable at {BASE_URL}: {exc}")


def _create_note(**overrides) -> dict:
    payload = {
        "title": "Sample Note",
        "content": "Sample content",
        "category": "work",
        "tags": ["sample", "test"],
    }
    payload.update(overrides)
    response = requests.post(f"{BASE_URL}/notes", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def note() -> dict:
    """A fresh note created via the API."""
    return _create_note()


@pytest.fixture
def note_id(note) -> int:
    return note["id"]


@pytest.fixture
def seeded_notes() -> list[dict]:
    """Create a small varied set of notes to support filtering/stats tests."""
    seeds = [
        {
            "title": "Team Meeting",
            "content": "Discuss Q2 goals and project timeline",
            "category": "work",
            "tags": ["urgent", "meeting", "Q2"],
        },
        {
            "title": "Shopping List",
            "content": "Milk, eggs, bread, coffee",
            "category": "personal",
            "tags": ["urgent", "shopping"],
        },
        {
            "title": "Study Session",
            "content": "Review chapters 5-7 for exam",
            "category": "school",
            "tags": ["exam", "study"],
        },
        {
            "title": "Dentist Appointment",
            "content": "Annual checkup at 2pm",
            "category": "personal",
            "tags": ["health", "appointment"],
        },
        {
            "title": "Project Deadline",
            "content": "Submit final report",
            "category": "work",
            "tags": ["urgent", "deadline", "project"],
        },
    ]
    return [_create_note(**seed) for seed in seeds]


# ===========================================================================
# Root
# ===========================================================================

def test_root_returns_metadata():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


# ===========================================================================
# Create / Read
# ===========================================================================

def test_create_note_returns_201_and_payload():
    payload = {
        "title": "Team Meeting",
        "content": "Discuss Q2 goals",
        "category": "work",
        "tags": ["urgent", "meeting"],
    }
    response = requests.post(f"{BASE_URL}/notes", json=payload)
    assert response.status_code == 201, response.text

    body = response.json()
    assert body["title"] == payload["title"]
    assert body["content"] == payload["content"]
    assert body["category"] == payload["category"]
    assert sorted(body["tags"]) == sorted(payload["tags"])
    assert isinstance(body["id"], int)
    assert "created_at" in body


def test_create_note_normalizes_tags():
    """Tags should be lowercased and deduplicated."""
    response = requests.post(
        f"{BASE_URL}/notes",
        json={
            "title": "Tag Test",
            "content": "Check tag normalization",
            "category": "work",
            "tags": ["URGENT", "urgent", "Meeting"],
        },
    )
    assert response.status_code == 201, response.text
    tags = response.json()["tags"]
    assert sorted(tags) == ["meeting", "urgent"]


def test_list_notes_returns_a_list(note):
    response = requests.get(f"{BASE_URL}/notes")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert any(item["id"] == note["id"] for item in body)


def test_get_single_note(note_id):
    response = requests.get(f"{BASE_URL}/notes/{note_id}")
    assert response.status_code == 200
    assert response.json()["id"] == note_id


def test_get_missing_note_returns_404():
    response = requests.get(f"{BASE_URL}/notes/99999999999")
    assert response.status_code == 404


# ===========================================================================
# Task 1: Combined filters
# ===========================================================================

def test_filter_by_category(seeded_notes):
    response = requests.get(f"{BASE_URL}/notes", params={"category": "work"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) > 0
    assert all(n["category"] == "work" for n in body)


def test_filter_by_search(seeded_notes):
    response = requests.get(f"{BASE_URL}/notes", params={"search": "meeting"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) > 0
    assert all(
        "meeting" in n["title"].lower() or "meeting" in n["content"].lower()
        for n in body
    )


def test_filter_by_tag(seeded_notes):
    response = requests.get(f"{BASE_URL}/notes", params={"tag": "urgent"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) > 0
    assert all("urgent" in n["tags"] for n in body)


def test_combined_filters(seeded_notes):
    response = requests.get(
        f"{BASE_URL}/notes",
        params={"category": "work", "tag": "urgent", "search": "meeting"},
    )
    assert response.status_code == 200
    for n in response.json():
        assert n["category"] == "work"
        assert "urgent" in n["tags"]
        assert (
            "meeting" in n["title"].lower() or "meeting" in n["content"].lower()
        )


# ===========================================================================
# Task 2: Statistics
# ===========================================================================

def test_statistics_structure(seeded_notes):
    response = requests.get(f"{BASE_URL}/notes/stats")
    assert response.status_code == 200
    stats = response.json()

    assert "total_notes" in stats
    assert "by_category" in stats
    assert "top_tags" in stats
    assert "unique_tags_count" in stats

    assert isinstance(stats["total_notes"], int)
    assert isinstance(stats["by_category"], dict)
    assert isinstance(stats["top_tags"], list)
    assert isinstance(stats["unique_tags_count"], int)
    assert stats["total_notes"] >= len(seeded_notes)


# ===========================================================================
# Task 3: Categories resource
# ===========================================================================

def test_list_categories(seeded_notes):
    response = requests.get(f"{BASE_URL}/categories")
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    assert "work" in categories


def test_notes_by_category(seeded_notes):
    response = requests.get(f"{BASE_URL}/categories/work/notes")
    assert response.status_code == 200
    notes = response.json()
    assert isinstance(notes, list)
    assert len(notes) > 0
    assert all(n["category"] == "work" for n in notes)


# ===========================================================================
# Task 4: PATCH (partial update)
# ===========================================================================

def test_patch_updates_only_provided_fields(note):
    response = requests.patch(
        f"{BASE_URL}/notes/{note['id']}",
        json={"title": "UPDATED TITLE"},
    )
    assert response.status_code == 200, response.text
    updated = response.json()

    assert updated["title"] == "UPDATED TITLE"
    assert updated["content"] == note["content"]
    assert updated["category"] == note["category"]
    assert sorted(updated["tags"]) == sorted(note["tags"])


def test_patch_missing_note_returns_404():
    response = requests.patch(
        f"{BASE_URL}/notes/99999999",
        json={"title": "nope"}
    )
    assert response.status_code == 404


# ===========================================================================
# Task 5: Date-based filtering
# ===========================================================================

def test_filter_created_after(seeded_notes):
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    response = requests.get(
        f"{BASE_URL}/notes", params={"created_after": yesterday}
    )
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_filter_created_before(seeded_notes):
    tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
    response = requests.get(
        f"{BASE_URL}/notes", params={"created_before": tomorrow}
    )
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_filter_date_range(seeded_notes):
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
    response = requests.get(
        f"{BASE_URL}/notes",
        params={"created_after": yesterday, "created_before": tomorrow},
    )
    assert response.status_code == 200
    assert len(response.json()) > 0


# ===========================================================================
# Tags resource
# ===========================================================================

def test_list_tags(seeded_notes):
    response = requests.get(f"{BASE_URL}/tags")
    assert response.status_code == 200
    tags = response.json()
    assert isinstance(tags, list)
    assert "urgent" in tags


def test_notes_by_tag(seeded_notes):
    response = requests.get(f"{BASE_URL}/tags/urgent/notes")
    assert response.status_code == 200
    notes = response.json()
    assert isinstance(notes, list)
    assert len(notes) > 0
    assert all("urgent" in n["tags"] for n in notes)


# ===========================================================================
# PUT (full update)
# ===========================================================================

def test_put_replaces_all_fields(note_id):
    update = {
        "title": "Fully Updated Note",
        "content": "All fields replaced",
        "category": "personal",
        "tags": ["updated", "test"],
    }
    response = requests.put(f"{BASE_URL}/notes/{note_id}", json=update)
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["title"] == update["title"]
    assert updated["content"] == update["content"]
    assert updated["category"] == update["category"]
    assert sorted(updated["tags"]) == sorted(update["tags"])


def test_put_missing_note_returns_404():
    response = requests.put(
        f"{BASE_URL}/notes/99999999",
        json={
            "title": "xxx",
            "content": "xxxxx",
            "category": "work",
            "tags": [],
        },
    )
    assert response.status_code == 404


# ===========================================================================
# DELETE
# ===========================================================================

def test_delete_note(note_id):
    response = requests.delete(f"{BASE_URL}/notes/{note_id}")
    assert response.status_code == 204

    follow_up = requests.get(f"{BASE_URL}/notes/{note_id}")
    assert follow_up.status_code == 404


def test_delete_missing_note_returns_404():
    response = requests.delete(f"{BASE_URL}/notes/99999999")
    assert response.status_code == 404


def test_delete_is_idempotent_after_first_call(note_id):
    """A second DELETE on the same id returns 404, never succeeds twice."""
    first = requests.delete(f"{BASE_URL}/notes/{note_id}")
    assert first.status_code == 204
    second = requests.delete(f"{BASE_URL}/notes/{note_id}")
    assert second.status_code == 404


# ===========================================================================
# Validation: 422 on bad payloads
# ===========================================================================

@pytest.mark.parametrize(
    "payload",
    [
        {},  # everything missing
        {"title": "only title"},  # missing content + category
        {"title": "x", "content": "x"},  # missing category
        {"title": "x", "content": "x", "category": "x", "tags": "not-a-list"},
        {"title": 123, "content": "x", "category": "x"},  # wrong type
    ],
)
def test_create_note_validation_errors(payload):
    response = requests.post(f"{BASE_URL}/notes", json=payload)
    assert response.status_code == 422, response.text


def test_get_note_with_non_integer_id_returns_422():
    response = requests.get(f"{BASE_URL}/notes/not-a-number")
    assert response.status_code == 422


@pytest.mark.parametrize("bad_date", ["not-a-date", "2026-13-01", "2026/01/01"])
def test_invalid_created_after_returns_422(bad_date):
    response = requests.get(f"{BASE_URL}/notes", params={"created_after": bad_date})
    assert response.status_code == 422


@pytest.mark.parametrize("bad_date", ["not-a-date", "2026-99-99"])
def test_invalid_created_before_returns_422(bad_date):
    response = requests.get(f"{BASE_URL}/notes", params={"created_before": bad_date})
    assert response.status_code == 422


# ===========================================================================
# Tag normalization (deeper)
# ===========================================================================

def test_tag_whitespace_is_stripped():
    body = _create_note(tags=["  spaced  ", "spaced"])
    assert body["tags"] == ["spaced"]


def test_normalization_of_tags():
    body = _create_note(tags=["KEPT", "kept"])
    assert body["tags"] == ["kept"]


def test_tag_too_short_returns_422():
    payload = {"title": "short tag", "content": "x", "category": "work", "tags": ["a"]}
    response = requests.post(f"{BASE_URL}/notes", json=payload)
    assert response.status_code == 422


def test_create_note_with_10_tags():
    tags = [f"tag{i}" for i in range(10)]
    payload = {"title": "10 tags", "content": "test", "category": "work", "tags": tags}
    response = requests.post(f"{BASE_URL}/notes", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert sorted(body["tags"]) == sorted(tags)


def test_create_note_with_11_tags():
    tags = [f"tag{i}" for i in range(11)]
    payload = {"title": "11 tags", "content": "test", "category": "work", "tags": tags}
    response = requests.post(f"{BASE_URL}/notes", json=payload)
    assert response.status_code == 422


def test_tags_are_reused_across_notes():
    """Creating two notes with the same tag should not produce duplicates in /tags."""
    _create_note(tags=["shared-tag-xyz"])
    _create_note(tags=["shared-tag-xyz"])
    tags = requests.get(f"{BASE_URL}/tags").json()
    assert tags.count("shared-tag-xyz") == 1


def test_create_note_with_no_tags():
    body = _create_note(tags=[])
    assert body["tags"] == []


def test_tags_field_omitted_defaults_to_empty():
    response = requests.post(
        f"{BASE_URL}/notes",
        json={"title": "no tags", "content": "x", "category": "work"},
    )
    assert response.status_code == 201
    assert response.json()["tags"] == []


# ===========================================================================
# PATCH semantics
# ===========================================================================

def test_patch_with_empty_body_changes_nothing(note):
    response = requests.patch(f"{BASE_URL}/notes/{note['id']}", json={})
    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == note["title"]
    assert updated["content"] == note["content"]
    assert updated["category"] == note["category"]
    assert sorted(updated["tags"]) == sorted(note["tags"])


def test_patch_can_clear_tags(note):
    response = requests.patch(
        f"{BASE_URL}/notes/{note['id']}", json={"tags": []}
    )
    assert response.status_code == 200
    assert response.json()["tags"] == []


def test_patch_replaces_tags_not_appends(note):
    """PATCH on tags should replace the set, not merge."""
    response = requests.patch(
        f"{BASE_URL}/notes/{note['id']}", json={"tags": ["only-this"]}
    )
    assert response.status_code == 200
    assert response.json()["tags"] == ["only-this"]


def test_patch_each_field_individually(note):
    nid = note["id"]

    r = requests.patch(f"{BASE_URL}/notes/{nid}", json={"content": "new content"})
    assert r.status_code == 200 and r.json()["content"] == "new content"

    r = requests.patch(f"{BASE_URL}/notes/{nid}", json={"category": "personal"})
    assert r.status_code == 200 and r.json()["category"] == "personal"


def test_patch_preserves_id_and_created_at(note):
    response = requests.patch(
        f"{BASE_URL}/notes/{note['id']}", json={"title": "patched"}
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == note["id"]
    assert updated["created_at"] == note["created_at"]


# ===========================================================================
# PUT semantics
# ===========================================================================

def test_put_can_clear_tags(note_id):
    response = requests.put(
        f"{BASE_URL}/notes/{note_id}",
        json={"title": "title", "content": "content", "category": "work", "tags": []},
    )
    assert response.status_code == 200
    assert response.json()["tags"] == []


def test_put_with_partial_body_returns_422(note_id):
    """PUT requires all fields; missing ones must error."""
    response = requests.put(
        f"{BASE_URL}/notes/{note_id}", json={"title": "only"}
    )
    assert response.status_code == 422


# ===========================================================================
# Filtering edge cases
# ===========================================================================

def test_search_is_case_insensitive(seeded_notes):
    lower = requests.get(f"{BASE_URL}/notes", params={"search": "meeting"}).json()
    upper = requests.get(f"{BASE_URL}/notes", params={"search": "MEETING"}).json()
    assert {n["id"] for n in lower} == {n["id"] for n in upper}
    assert len(lower) > 0


def test_search_matches_content(seeded_notes):
    """Search should also look in content, not just titles."""
    response = requests.get(f"{BASE_URL}/notes", params={"search": "chapters"})
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_filter_by_unknown_category_returns_empty(seeded_notes):
    response = requests.get(
        f"{BASE_URL}/notes",
        params={"category": "definitely-not-a-category-xyz"}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_filter_by_unknown_tag_returns_empty(seeded_notes):
    response = requests.get(
        f"{BASE_URL}/notes", params={"tag": "definitely-not-a-tag-xyz"}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_search_unknown_term_returns_empty(seeded_notes):
    response = requests.get(
        f"{BASE_URL}/notes", params={"search": "qqqzzzxxx-no-match"}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_filter_created_after_in_future_returns_empty(seeded_notes):
    far_future = (datetime.now() + timedelta(days=365 * 5)).isoformat()
    response = requests.get(
        f"{BASE_URL}/notes", params={"created_after": far_future}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_filter_created_before_in_past_returns_empty(seeded_notes):
    far_past = (datetime.now() - timedelta(days=365 * 50)).isoformat()
    response = requests.get(
        f"{BASE_URL}/notes", params={"created_before": far_past}
    )
    assert response.status_code == 200
    assert response.json() == []


# ===========================================================================
# Statistics deeper checks
# ===========================================================================

def test_statistics_top_tags_shape(seeded_notes):
    stats = requests.get(f"{BASE_URL}/notes/stats").json()
    top = stats["top_tags"]
    assert len(top) <= 5
    for entry in top:
        assert set(entry.keys()) == {"tag", "count"}
        assert isinstance(entry["tag"], str)
        assert isinstance(entry["count"], int)
        assert entry["count"] >= 1


def test_statistics_top_tags_sorted_descending(seeded_notes):
    stats = requests.get(f"{BASE_URL}/notes/stats").json()
    counts = [t["count"] for t in stats["top_tags"]]
    assert counts == sorted(counts, reverse=True)


def test_statistics_unique_tag_count_matches_tags_endpoint(seeded_notes):
    stats = requests.get(f"{BASE_URL}/notes/stats").json()
    tags = requests.get(f"{BASE_URL}/tags").json()
    assert stats["unique_tags_count"] == len(tags)


def test_statistics_total_matches_list(seeded_notes):
    stats = requests.get(f"{BASE_URL}/notes/stats").json()
    notes = requests.get(f"{BASE_URL}/notes").json()
    assert stats["total_notes"] == len(notes)


def test_statistics_by_category_sums_to_total(seeded_notes):
    stats = requests.get(f"{BASE_URL}/notes/stats").json()
    assert sum(stats["by_category"].values()) == stats["total_notes"]


# ===========================================================================
# Resource navigation
# ===========================================================================

def test_unknown_tag_resource_returns_empty_list():
    """Requesting notes for a non-existent tag should return [], not 404."""
    response = requests.get(f"{BASE_URL}/tags/no-such-tag-xyz/notes")
    assert response.status_code == 200
    assert response.json() == []


def test_unknown_category_resource_returns_empty_list():
    response = requests.get(f"{BASE_URL}/categories/no-such-category-xyz/notes")
    assert response.status_code == 200
    assert response.json() == []


def test_tag_lookup_is_case_insensitive():
    _create_note(tags=["case-tag"])
    upper = requests.get(f"{BASE_URL}/tags/CASE-TAG/notes")
    assert upper.status_code == 200
    assert len(upper.json()) > 0


def test_categories_endpoint_is_sorted_and_unique(seeded_notes):
    categories = requests.get(f"{BASE_URL}/categories").json()
    assert categories == sorted(categories)
    assert len(categories) == len(set(categories))


def test_tags_endpoint_is_sorted_and_unique(seeded_notes):
    tags = requests.get(f"{BASE_URL}/tags").json()
    assert tags == sorted(tags)
    assert len(tags) == len(set(tags))


# ===========================================================================
# End-to-end flows
# ===========================================================================

def test_full_crud_lifecycle():
    """Create → read → patch → put → delete → verify gone."""
    created = _create_note(
        title="Lifecycle", content="initial", category="work", tags=["ab"]
    )
    nid = created["id"]

    # Read
    got = requests.get(f"{BASE_URL}/notes/{nid}").json()
    assert got["title"] == "Lifecycle"

    # Patch
    patched = requests.patch(
        f"{BASE_URL}/notes/{nid}", json={"content": "patched"}
    ).json()
    assert patched["content"] == "patched"
    assert patched["title"] == "Lifecycle"

    # Put
    put = requests.put(
        f"{BASE_URL}/notes/{nid}",
        json={
            "title": "Replaced",
            "content": "fully new",
            "category": "personal",
            "tags": ["bput"],
        },
    ).json()
    assert put["title"] == "Replaced"
    assert put["category"] == "personal"
    assert put["tags"] == ["bput"]

    # Delete
    assert requests.delete(f"{BASE_URL}/notes/{nid}").status_code == 204
    assert requests.get(f"{BASE_URL}/notes/{nid}").status_code == 404


def test_note_appears_in_tag_and_category_resources():
    tag_name = "cross-ref-tag"
    category_name = "work"
    created = _create_note(
        title="Cross-ref", category=category_name, tags=[tag_name]
    )

    by_tag = requests.get(f"{BASE_URL}/tags/{tag_name}/notes").json()
    by_cat = requests.get(f"{BASE_URL}/categories/{category_name}/notes").json()

    assert any(n["id"] == created["id"] for n in by_tag)
    assert any(n["id"] == created["id"] for n in by_cat)





# ===========================================================================
# Performance / smoke-load tests
# ---------------------------------------------------------------------------
# Lightweight latency checks. Thresholds are intentionally loose so the suite
# does not flake on slow CI runners or student laptops; they mostly guard
# against accidental O(n^2) regressions and obvious slowdowns.
#
# Run only these tests with:
#     uv run pytest test_notes_api.py -v -m performance
# Skip them with:
#     uv run pytest test_notes_api.py -v -m "not performance"
# ===========================================================================

# import time
# import statistics


# # Loose thresholds (seconds). Tune down if you want stricter SLAs.
# PERF_P95_BUDGET = 0.5         # 500 ms p95 for cheap point lookups / writes
# PERF_MEAN_BUDGET = 0.2        # 200 ms mean for cheap point lookups / writes
# PERF_SCAN_P95_BUDGET = 2.0    # 2 s p95 for endpoints that scan the whole table


# def _percentile(values: list[float], pct: float) -> float:
#     """Simple nearest-rank percentile (no numpy dependency)."""
#     if not values:
#         return 0.0
#     ordered = sorted(values)
#     k = max(0, min(len(ordered) - 1, int(round(pct / 100.0 * len(ordered))) - 1))
#     return ordered[k]


# def _measure(fn, n: int) -> list[float]:
#     """Call fn() n times and return per-call durations in seconds."""
#     durations = []
#     for _ in range(n):
#         start = time.perf_counter()
#         response = fn()
#         durations.append(time.perf_counter() - start)
#         # Fail fast if the endpoint is broken — perf of a 500 is meaningless.
#         assert response.status_code < 400, response.text
#     return durations


# def _report(name: str, durations: list[float]) -> dict:
#     stats = {
#         "n": len(durations),
#         "mean_ms": statistics.mean(durations) * 1000,
#         "median_ms": statistics.median(durations) * 1000,
#         "p95_ms": _percentile(durations, 95) * 1000,
#         "max_ms": max(durations) * 1000,
#     }
#     print(
#         f"\n[perf] {name:32s} "
#         f"n={stats['n']:>3}  "
#         f"mean={stats['mean_ms']:6.1f}ms  "
#         f"median={stats['median_ms']:6.1f}ms  "
#         f"p95={stats['p95_ms']:6.1f}ms  "
#         f"max={stats['max_ms']:6.1f}ms"
#     )
#     return stats


# @pytest.fixture(scope="module")
# def perf_dataset() -> list[dict]:
#     """Seed ~50 notes so list/filter/stats endpoints have something to chew on."""
#     categories = ["work", "personal", "school", "ideas"]
#     tag_pool = ["urgent", "later", "review", "todo", "draft", "perf"]
#     created = []
#     for i in range(50):
#         created.append(
#             _create_note(
#                 title=f"Perf Note {i}",
#                 content=f"Lorem ipsum content for perf note number {i}.",
#                 category=categories[i % len(categories)],
#                 tags=[tag_pool[i % len(tag_pool)], tag_pool[(i + 1) % len(tag_pool)]],
#             )
#         )
#     return created


# @pytest.mark.performance
# def test_perf_root_endpoint():
#     durations = _measure(lambda: requests.get(f"{BASE_URL}/"), n=50)
#     stats = _report("GET /", durations)
#     assert stats["p95_ms"] < PERF_P95_BUDGET * 1000
#     assert stats["mean_ms"] < PERF_MEAN_BUDGET * 1000


# @pytest.mark.performance
# def test_perf_list_notes(perf_dataset):
#     durations = _measure(lambda: requests.get(f"{BASE_URL}/notes"), n=30)
#     stats = _report("GET /notes", durations)
#     # Full table scan + serialization — looser budget.
#     assert stats["p95_ms"] < PERF_SCAN_P95_BUDGET * 1000


# @pytest.mark.performance
# def test_perf_get_single_note(perf_dataset):
#     nid = perf_dataset[0]["id"]
#     durations = _measure(lambda: requests.get(f"{BASE_URL}/notes/{nid}"), n=50)
#     stats = _report("GET /notes/{id}", durations)
#     assert stats["p95_ms"] < PERF_P95_BUDGET * 1000


# @pytest.mark.performance
# def test_perf_create_note():
#     def _post():
#         return requests.post(
#             f"{BASE_URL}/notes",
#             json={
#                 "title": "perf-create",
#                 "content": "throwaway",
#                 "category": "work",
#                 "tags": ["perf", "create"],
#             },
#         )
#     durations = _measure(_post, n=30)
#     stats = _report("POST /notes", durations)
#     assert stats["p95_ms"] < PERF_P95_BUDGET * 1000


# @pytest.mark.performance
# def test_perf_filtered_list(perf_dataset):
#     """Combined filters touch the heaviest query path."""
#     def _get():
#         return requests.get(
#             f"{BASE_URL}/notes",
#             params={"category": "work", "tag": "urgent", "search": "perf"},
#         )
#     durations = _measure(_get, n=30)
#     stats = _report("GET /notes (filtered)", durations)
#     assert stats["p95_ms"] < PERF_P95_BUDGET * 1000


# @pytest.mark.performance
# def test_perf_stats_endpoint(perf_dataset):
#     durations = _measure(lambda: requests.get(f"{BASE_URL}/notes/stats"), n=30)
#     stats = _report("GET /notes/stats", durations)
#     # Aggregates over all notes — looser budget.
#     assert stats["p95_ms"] < PERF_SCAN_P95_BUDGET * 1000


# @pytest.mark.performance
# def test_perf_patch_note(perf_dataset):
#     nid = perf_dataset[1]["id"]
#     counter = {"i": 0}

#     def _patch():
#         counter["i"] += 1
#         return requests.patch(
#             f"{BASE_URL}/notes/{nid}",
#             json={"title": f"perf-patch-{counter['i']}"},
#         )
#     durations = _measure(_patch, n=30)
#     stats = _report("PATCH /notes/{id}", durations)
#     assert stats["p95_ms"] < PERF_P95_BUDGET * 1000


# @pytest.mark.performance
# def test_perf_throughput_sequential_creates():
#     """Sanity check throughput: should comfortably exceed 10 req/s sequentially."""
#     n = 30
#     start = time.perf_counter()
#     for i in range(n):
#         r = requests.post(
#             f"{BASE_URL}/notes",
#             json={
#                 "title": f"tput-{i}",
#                 "content": "x",
#                 "category": "work",
#                 "tags": ["tput"],
#             },
#         )
#         assert r.status_code == 201
#     elapsed = time.perf_counter() - start
#     rps = n / elapsed
#     print(f"\n[perf] sequential POST throughput   {rps:5.1f} req/s over {n} reqs")
#     assert rps > 10, f"throughput too low: {rps:.1f} req/s"