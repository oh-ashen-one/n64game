from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate-asset-contract"
BENCHMARK = ROOT / "docs" / "VISUAL_BENCHMARK_APPROVAL.md"
INVENTORY = ROOT / "docs" / "ASSET_INVENTORY.md"

MODEL_ID = "echo.quarrune"
ANIMATION_ID = "anm.echo.quarrune"
MODEL_SELECTORS = (
    "ASSET:blob_shadow",
    "ASSET:distance_model",
    "ASSET:hero_model",
    "ASSET:rig",
    "ASSET:texture",
)
ANIMATION_SELECTORS = (
    "CLIP:brace_relay",
    "CLIP:entrance",
    "CLIP:hit",
    "CLIP:horizon_break",
    "CLIP:idle_a",
    "CLIP:idle_b",
    "CLIP:knockout",
    "CLIP:reposition",
    "CLIP:ridge_ram",
)
MODEL_CELL = "final hero/distance model, texture, rig, blob shadow only; owns no animation clips"
MODEL_CELL_SHA256 = "91f3797ab46a85767b7b97da490b8f3890399b3705955f1daf773a26bf8ddb93"
MODEL_LOCKED_CELL = (
    "every animation clip; the nine benchmark clips are separately and exclusively owned by "
    "`anm.echo.quarrune`"
)
ANIMATION_CELL = (
    "`idle_a`, `idle_b`, `entrance`, `reposition`, `ridge_ram`, `brace_relay`, `hit`, "
    "`knockout`, `horizon_break` participation preview"
)
ANIMATION_CELL_SHA256 = "6f45d89316979094ebcf5b5d04f2cbd228d2091072300705179bafed159067dd"
MODEL_SELECTORS_SHA256 = "4300265ba1e2411f652b67fccd9d2701c82bd68747f3a080b6748e98c7dd050b"
ANIMATION_SELECTORS_SHA256 = "19c63aa5fba5046e28ece64820d93fe0aad6e167bf0091fae7b50aea28ad923c"
SELECTOR_PARTITION_SHA256 = "d06ed8980795025d6244de03730b9caf3e110fca5c8116071b843c436c332633"
INVENTORY_CLIP_CELL = (
    "14 total in paired `anm.echo.quarrune`; this model row owns no animation clips. `S1` requires "
    "`idle_a`, `idle_b`, `entrance`, `reposition`, `ridge_ram`, `brace_relay`, `hit`, `knockout`, "
    "and `horizon_break` participation preview from that bank; the remaining five bank clips are `S4`."
)
ANIMATION_INVENTORY_CELLS = [
    "`anm.echo.quarrune`",
    "14",
    "`S1`: idle_a/b, entrance, reposition, ridge_ram, brace_relay, hit, knockout; `S4`: "
    "grounding_ring, steady_pulse, victory, story_brace_alert, story_resolve",
    "`S1` participation preview; final integrated horizon_break remains `S4`",
    "`S1/S4 P0`",
]


def markdown_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.split("|")[1:-1]]


def production_row(document: str, production_id: str) -> list[str]:
    prefix = f"| `{production_id}` |"
    matches = [markdown_cells(line) for line in document.splitlines() if line.startswith(prefix)]
    if len(matches) != 1:
        raise AssertionError(f"expected one {production_id} table row, found {len(matches)}")
    return matches[0]


def policy_words(validator: str, constant_name: str) -> tuple[str, ...]:
    match = re.search(
        rf"(?ms)^{re.escape(constant_name)} = %w\[\n(?P<body>.*?)\n\]\.freeze$",
        validator,
    )
    if match is None:
        raise AssertionError(f"missing exact Ruby policy constant {constant_name}")
    return tuple(match.group("body").split())


def subset_digest(validator: str, production_id: str) -> str:
    matches = re.findall(
        rf'^  "{re.escape(production_id)}" => "([0-9a-f]{{64}})",$',
        validator,
        flags=re.MULTILINE,
    )
    if len(matches) != 1:
        raise AssertionError(f"expected one digest row for {production_id}, found {len(matches)}")
    return matches[0]


def partition_issues(model: tuple[str, ...], animation: tuple[str, ...]) -> list[str]:
    issues: list[str] = []
    if model != MODEL_SELECTORS:
        issues.append("model set")
    if animation != ANIMATION_SELECTORS:
        issues.append("animation set")
    if set(model) & set(animation):
        issues.append("owner overlap")
    if len(model) != 5 or any(not selector.startswith("ASSET:") for selector in model):
        issues.append("model selector type/count")
    if len(animation) != 9 or any(not selector.startswith("CLIP:") for selector in animation):
        issues.append("animation selector type/count")
    if sorted(model + animation) != sorted(MODEL_SELECTORS + ANIMATION_SELECTORS):
        issues.append("5+9 union")
    return issues


def document_contract_issues(validator: str, benchmark: str, inventory: str) -> list[str]:
    issues: list[str] = []
    try:
        model = policy_words(validator, "QUARRUNE_MODEL_SELECTORS")
        animation = policy_words(validator, "QUARRUNE_BENCHMARK_ANIMATION_SELECTORS")
        issues.extend(partition_issues(model, animation))
        model_row = production_row(benchmark, MODEL_ID)
        animation_row = production_row(benchmark, ANIMATION_ID)
        if model_row[1:3] != [MODEL_CELL, MODEL_LOCKED_CELL]:
            issues.append("model whitelist cells")
        if animation_row[1] != ANIMATION_CELL:
            issues.append("animation whitelist cell")
        if subset_digest(validator, MODEL_ID) != MODEL_CELL_SHA256:
            issues.append("model digest")
        if subset_digest(validator, ANIMATION_ID) != ANIMATION_CELL_SHA256:
            issues.append("animation digest")
        authorization_rows = {
            cells[0]: cells[1].strip("`")
            for cells in (
                markdown_cells(line)
                for line in benchmark.splitlines()
                if re.match(r"^\| WB-\d{3} \|", line)
            )
        }
        if authorization_rows.get("WB-002") != MODEL_ID:
            issues.append("WB-002 mapping")
        if authorization_rows.get("WB-039") != ANIMATION_ID:
            issues.append("WB-039 mapping")
        if production_row(inventory, MODEL_ID)[4] != INVENTORY_CLIP_CELL:
            issues.append("inventory ownership")
        if production_row(inventory, ANIMATION_ID) != ANIMATION_INVENTORY_CELLS:
            issues.append("animation inventory bank")
    except (AssertionError, IndexError):
        issues.append("malformed contract")
    return issues


class QuarruneSelectorPartitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = VALIDATOR.read_text(encoding="utf-8")
        cls.benchmark = BENCHMARK.read_text(encoding="utf-8")
        cls.inventory = INVENTORY.read_text(encoding="utf-8")

    def test_source_selector_policy_has_exact_disjoint_five_plus_nine_owners(self) -> None:
        model = policy_words(self.validator, "QUARRUNE_MODEL_SELECTORS")
        animation = policy_words(self.validator, "QUARRUNE_BENCHMARK_ANIMATION_SELECTORS")
        self.assertEqual(partition_issues(model, animation), [])
        self.assertEqual(hashlib.sha256(("\n".join(model) + "\n").encode()).hexdigest(), MODEL_SELECTORS_SHA256)
        self.assertEqual(
            hashlib.sha256(("\n".join(animation) + "\n").encode()).hexdigest(),
            ANIMATION_SELECTORS_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(("\n".join(sorted(model + animation)) + "\n").encode()).hexdigest(),
            SELECTOR_PARTITION_SHA256,
        )
        self.assertIn(f'"{MODEL_ID}" => QUARRUNE_MODEL_SELECTORS,', self.validator)
        self.assertIn(
            f'"{ANIMATION_ID}" => QUARRUNE_BENCHMARK_ANIMATION_SELECTORS,',
            self.validator,
        )

    def test_whitelist_cells_digests_and_basis_mapping_are_exact(self) -> None:
        model_row = production_row(self.benchmark, MODEL_ID)
        animation_row = production_row(self.benchmark, ANIMATION_ID)
        self.assertEqual(model_row[1], MODEL_CELL)
        self.assertEqual(model_row[2], MODEL_LOCKED_CELL)
        self.assertEqual(animation_row[1], ANIMATION_CELL)
        self.assertEqual(hashlib.sha256(model_row[1].encode()).hexdigest(), MODEL_CELL_SHA256)
        self.assertEqual(hashlib.sha256(animation_row[1].encode()).hexdigest(), ANIMATION_CELL_SHA256)
        self.assertEqual(subset_digest(self.validator, MODEL_ID), MODEL_CELL_SHA256)
        self.assertEqual(subset_digest(self.validator, ANIMATION_ID), ANIMATION_CELL_SHA256)

        authorization_rows = {
            cells[0]: cells[1]
            for cells in (
                markdown_cells(line)
                for line in self.benchmark.splitlines()
                if re.match(r"^\| WB-\d{3} \|", line)
            )
        }
        self.assertEqual(authorization_rows["WB-002"].strip("`"), MODEL_ID)
        self.assertEqual(authorization_rows["WB-039"].strip("`"), ANIMATION_ID)

    def test_inventory_model_row_delegates_exact_clips_to_animation_bank(self) -> None:
        row = production_row(self.inventory, MODEL_ID)
        self.assertEqual(row[4], INVENTORY_CLIP_CELL)
        self.assertIn("this model row owns no animation clips", row[4])
        self.assertNotIn("`S1` owns idle", row[4])
        self.assertEqual(production_row(self.inventory, ANIMATION_ID), ANIMATION_INVENTORY_CELLS)

    def test_cross_owner_missing_locked_and_swapped_mutations_die(self) -> None:
        mutations: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []
        for selector in ANIMATION_SELECTORS:
            mutations.append((f"model_leaks_{selector}", tuple(sorted(MODEL_SELECTORS + (selector,))), ANIMATION_SELECTORS))
        for selector in MODEL_SELECTORS:
            mutations.append((f"animation_leaks_{selector}", MODEL_SELECTORS, tuple(sorted(ANIMATION_SELECTORS + (selector,)))))
        for selector in MODEL_SELECTORS:
            mutations.append((f"model_missing_{selector}", tuple(value for value in MODEL_SELECTORS if value != selector), ANIMATION_SELECTORS))
        for selector in ANIMATION_SELECTORS:
            mutations.append((f"animation_missing_{selector}", MODEL_SELECTORS, tuple(value for value in ANIMATION_SELECTORS if value != selector)))
        mutations.extend(
            (
                ("locked_grounding_ring", MODEL_SELECTORS, tuple(sorted(ANIMATION_SELECTORS + ("CLIP:grounding_ring",)))),
                ("owners_swapped", ANIMATION_SELECTORS, MODEL_SELECTORS),
            )
        )

        self.assertEqual(len(mutations), 30)
        for name, model, animation in mutations:
            with self.subTest(mutation=name):
                self.assertTrue(partition_issues(model, animation))

    def test_rehashed_document_mapping_and_inventory_regressions_die(self) -> None:
        self.assertEqual(document_contract_issues(self.validator, self.benchmark, self.inventory), [])
        old_inventory_cell = (
            "14 total; `S1` owns idle A/B, entrance, reposition, Ridge Ram, Brace Relay, hit, "
            "knockout, and Horizon Break participation preview; remaining clips are `S4`"
        )
        cases = {
            "model_clip_plus_rehashed_cell": (
                self.validator.replace(
                    "  ASSET:blob_shadow ASSET:distance_model ASSET:hero_model ASSET:rig ASSET:texture\n",
                    "  ASSET:blob_shadow ASSET:distance_model ASSET:hero_model ASSET:rig ASSET:texture CLIP:idle_a\n",
                    1,
                ).replace(MODEL_CELL_SHA256, hashlib.sha256((MODEL_CELL + "; idle_a").encode()).hexdigest(), 1),
                self.benchmark.replace(MODEL_CELL, MODEL_CELL + "; idle_a", 1),
                self.inventory,
            ),
            "animation_asset_plus_rehashed_cell": (
                self.validator.replace(
                    "  CLIP:knockout CLIP:reposition CLIP:ridge_ram\n",
                    "  ASSET:hero_model CLIP:knockout CLIP:reposition CLIP:ridge_ram\n",
                    1,
                ).replace(
                    ANIMATION_CELL_SHA256,
                    hashlib.sha256((ANIMATION_CELL + ", hero model").encode()).hexdigest(),
                    1,
                ),
                self.benchmark.replace(ANIMATION_CELL, ANIMATION_CELL + ", hero model", 1),
                self.inventory,
            ),
            "wb_owner_swap": (
                self.validator,
                self.benchmark.replace(
                    "| WB-002 | `echo.quarrune` |",
                    "| WB-002 | `owner.swap.tmp` |",
                    1,
                ).replace(
                    "| WB-039 | `anm.echo.quarrune` |",
                    "| WB-039 | `echo.quarrune` |",
                    1,
                ).replace(
                    "| WB-002 | `owner.swap.tmp` |",
                    "| WB-002 | `anm.echo.quarrune` |",
                    1,
                ),
                self.inventory,
            ),
            "inventory_model_claims_clips": (
                self.validator,
                self.benchmark,
                self.inventory.replace(INVENTORY_CLIP_CELL, old_inventory_cell, 1),
            ),
            "animation_inventory_drops_clip": (
                self.validator,
                self.benchmark,
                self.inventory.replace("idle_a/b, entrance", "idle_a, entrance", 1),
            ),
        }
        for name, (validator, benchmark, inventory) in cases.items():
            with self.subTest(mutation=name):
                self.assertTrue(document_contract_issues(validator, benchmark, inventory))


if __name__ == "__main__":
    unittest.main()
