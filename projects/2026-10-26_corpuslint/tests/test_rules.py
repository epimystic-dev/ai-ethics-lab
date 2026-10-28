"""Per-rule tests. Each test fixes a known-bad or known-good shape and asserts
exactly the rule ids it should fire. If a rule's id ever changes, the test
must change with it - that is the point of the id being stable."""

from __future__ import annotations

import unittest

from corpuslint import lint
from corpuslint.model import Severity, Verdict


def _manifest(**overrides):
    doc = {
        "id": "d1",
        "testimony_class": "testimony",
        "testifier": {"name": "example.org", "domain": "general-reference", "trust_weight": 0.5},
        "origin": "https://example.org/a",
        "chain_of_custody": [
            {"actor": "fetcher", "operation": "fetch", "timestamp": "2026-10-26T10:00:00Z"}
        ],
    }
    doc.update(overrides)
    return {"name": "unit-test-manifest", "documents": [doc]}


def _ids(result):
    return [f.rule_id for f in result.findings]


class ClassRules(unittest.TestCase):
    def test_001_class_missing(self):
        r = lint(_manifest(testimony_class=None))
        self.assertIn("CORP-001", _ids(r))

    def test_002_class_unknown(self):
        r = lint(_manifest(testimony_class="wisdom"))
        self.assertIn("CORP-002", _ids(r))

    def test_001_fires_once_per_bad_doc(self):
        m = _manifest(testimony_class=None)
        m["documents"].append(
            dict(m["documents"][0], id="d2", testimony_class=None)
        )
        r = lint(m)
        self.assertEqual(_ids(r).count("CORP-001"), 2)


class ChainRules(unittest.TestCase):
    def test_003_chain_missing(self):
        r = lint(_manifest(chain_of_custody=[]))
        self.assertIn("CORP-003", _ids(r))

    def test_004_chain_step_missing_actor(self):
        r = lint(_manifest(chain_of_custody=[
            {"actor": "", "operation": "fetch", "timestamp": "2026-10-26T10:00:00Z"}
        ]))
        self.assertIn("CORP-004", _ids(r))

    def test_004_chain_step_missing_timestamp(self):
        r = lint(_manifest(chain_of_custody=[
            {"actor": "fetcher", "operation": "fetch"}
        ]))
        self.assertIn("CORP-004", _ids(r))

    def test_005_chain_out_of_order(self):
        r = lint(_manifest(chain_of_custody=[
            {"actor": "a", "operation": "fetch", "timestamp": "2026-10-26T10:00:00Z"},
            {"actor": "b", "operation": "transform", "timestamp": "2026-10-26T09:00:00Z"},
        ]))
        self.assertIn("CORP-005", _ids(r))

    def test_005_well_ordered_chain_clean(self):
        r = lint(_manifest(chain_of_custody=[
            {"actor": "a", "operation": "fetch", "timestamp": "2026-10-26T10:00:00Z"},
            {"actor": "b", "operation": "transform", "timestamp": "2026-10-26T10:00:05Z"},
        ]))
        self.assertNotIn("CORP-005", _ids(r))


class TestifierRules(unittest.TestCase):
    def test_006_testimony_without_testifier(self):
        r = lint(_manifest(testifier=None))
        self.assertIn("CORP-006", _ids(r))

    def test_006_only_fires_for_testimony(self):
        r = lint(_manifest(testimony_class="perception", testifier=None))
        self.assertNotIn("CORP-006", _ids(r))

    def test_007_machine_text_misclassed_by_testifier(self):
        r = lint(_manifest(
            testimony_class="testimony",
            testifier={"name": "gpt-pipeline-9", "domain": "synthetic", "trust_weight": 0.1},
        ))
        self.assertIn("CORP-007", _ids(r))

    def test_007_machine_text_misclassed_by_origin(self):
        r = lint(_manifest(
            testimony_class="testimony",
            origin="https://cdn.example.com/synthetic/essay-01.html",
        ))
        self.assertIn("CORP-007", _ids(r))

    def test_007_not_triggered_for_well_classed_machine_text(self):
        r = lint(_manifest(
            testimony_class="machine_generated",
            testifier={"name": "gpt-pipeline-9", "domain": "synthetic", "trust_weight": 0.1},
        ))
        self.assertNotIn("CORP-007", _ids(r))

    def test_008_testifier_missing_fields(self):
        r = lint(_manifest(testifier={"name": "example.org"}))
        ids = _ids(r)
        self.assertIn("CORP-008", ids)


class MachineTextRules(unittest.TestCase):
    def test_009_recursive_synthetic(self):
        manifest = {
            "name": "m",
            "documents": [
                {
                    "id": "d1",
                    "testimony_class": "machine_generated",
                    "origin": "pipeline://a",
                    "chain_of_custody": [
                        {"actor": "a", "operation": "generate", "timestamp": "2026-10-26T10:00:00Z"}
                    ],
                },
                {
                    "id": "d2",
                    "testimony_class": "machine_generated",
                    "origin": "pipeline://b",
                    "downstream_of": "d1",
                    "chain_of_custody": [
                        {"actor": "b", "operation": "generate", "timestamp": "2026-10-26T11:00:00Z"}
                    ],
                },
            ],
        }
        r = lint(manifest)
        self.assertIn("CORP-009", _ids(r))

    def test_009_not_triggered_when_parent_is_human(self):
        manifest = {
            "name": "m",
            "documents": [
                {
                    "id": "d1",
                    "testimony_class": "testimony",
                    "testifier": {"name": "example.org", "domain": "ref", "trust_weight": 0.5},
                    "origin": "https://example.org/x",
                    "chain_of_custody": [
                        {"actor": "a", "operation": "fetch", "timestamp": "2026-10-26T10:00:00Z"}
                    ],
                },
                {
                    "id": "d2",
                    "testimony_class": "machine_generated",
                    "origin": "pipeline://b",
                    "downstream_of": "d1",
                    "chain_of_custody": [
                        {"actor": "b", "operation": "generate", "timestamp": "2026-10-26T11:00:00Z"}
                    ],
                },
            ],
        }
        r = lint(manifest)
        self.assertNotIn("CORP-009", _ids(r))


class AccountingRules(unittest.TestCase):
    def test_010_inflated_independence(self):
        manifest = {
            "name": "m",
            "documents": [
                {
                    "id": "d1",
                    "testimony_class": "testimony",
                    "testifier": {"name": "example.org", "domain": "ref", "trust_weight": 0.5},
                    "origin": "https://example.org/a",
                    "chain_of_custody": [
                        {"actor": "a", "operation": "fetch", "timestamp": "2026-10-26T10:00:00Z"}
                    ],
                },
                {
                    "id": "d2",
                    "testimony_class": "testimony",
                    "testifier": {"name": "example.org", "domain": "ref", "trust_weight": 0.5},
                    "origin": "https://example.org/b",
                    "chain_of_custody": [
                        {"actor": "a", "operation": "fetch", "timestamp": "2026-10-26T10:00:05Z"}
                    ],
                },
            ],
        }
        r = lint(manifest)
        self.assertIn("CORP-010", _ids(r))

    def test_010_single_testifier_clean(self):
        r = lint(_manifest())
        self.assertNotIn("CORP-010", _ids(r))

    def test_011_origin_missing(self):
        r = lint(_manifest(origin=""))
        self.assertIn("CORP-011", _ids(r))

    def test_011_origin_malformed_url(self):
        r = lint(_manifest(origin="http:/malformed"))
        self.assertIn("CORP-011", _ids(r))

    def test_011_non_http_origin_accepted(self):
        r = lint(_manifest(origin="pipeline://summarizer/42"))
        self.assertNotIn("CORP-011", _ids(r))


class ManifestLevelRules(unittest.TestCase):
    def test_012_manifest_no_name(self):
        m = _manifest()
        m["name"] = ""
        r = lint(m)
        self.assertIn("CORP-012", _ids(r))

    def test_012_manifest_no_documents(self):
        r = lint({"name": "empty"})
        self.assertIn("CORP-012", _ids(r))

    def test_013_class_coverage_info(self):
        m = _manifest()
        r = lint(m)
        self.assertIn("CORP-013", _ids(r))


class Verdicts(unittest.TestCase):
    def test_clean_input_is_healthy(self):
        r = lint({
            "name": "healthy",
            "documents": [
                {
                    "id": "p1",
                    "testimony_class": "perception",
                    "origin": "sensor://a",
                    "chain_of_custody": [
                        {"actor": "cam", "operation": "capture", "timestamp": "2026-10-26T10:00:00Z"}
                    ],
                },
                {
                    "id": "t1",
                    "testimony_class": "testimony",
                    "testifier": {"name": "example.org", "domain": "ref", "trust_weight": 0.5},
                    "origin": "https://example.org/x",
                    "chain_of_custody": [
                        {"actor": "a", "operation": "fetch", "timestamp": "2026-10-26T10:05:00Z"}
                    ],
                },
            ],
        })
        self.assertEqual(r.verdict, Verdict.HEALTHY)

    def test_high_only_is_unhealthy(self):
        r = lint(_manifest(testimony_class=None))
        self.assertEqual(r.verdict, Verdict.UNHEALTHY)

    def test_medium_only_is_needs_attention(self):
        m = {
            "name": "mid",
            "documents": [
                {
                    "id": "d1",
                    "testimony_class": "perception",
                    "origin": "",
                    "chain_of_custody": [
                        {"actor": "cam", "operation": "capture", "timestamp": "2026-10-26T10:00:00Z"}
                    ],
                },
                {
                    "id": "d2",
                    "testimony_class": "perception",
                    "origin": "sensor://b",
                    "chain_of_custody": [
                        {"actor": "cam", "operation": "capture", "timestamp": "2026-10-26T10:00:05Z"}
                    ],
                },
            ],
        }
        r = lint(m)
        self.assertEqual(r.verdict, Verdict.NEEDS_ATTENTION)


class Disable(unittest.TestCase):
    def test_disable_skips_the_rule(self):
        r = lint(_manifest(testimony_class=None), disable=["CORP-001"])
        self.assertNotIn("CORP-001", _ids(r))

    def test_no_info_skips_infos(self):
        r = lint(_manifest(), include_info=False)
        self.assertNotIn("CORP-013", _ids(r))


if __name__ == "__main__":
    unittest.main()
