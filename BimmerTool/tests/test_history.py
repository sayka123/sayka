import csv
import os
import tempfile
import unittest

from bimmertool.history import History


class HistoryTests(unittest.TestCase):
    def test_samples_are_bounded_and_keep_oldest_to_newest_order(self):
        history = History(limit=2)
        history.append("t1", [], "car")
        history.append("t2", [], "car")
        history.append("t3", [], "car")

        self.assertEqual([sample["timestamp"] for sample in history.samples], ["t2", "t3"])

    def test_append_and_samples_are_deeply_isolated(self):
        history = History()
        rows = [{"key": "soc", "value": 50, "details": {"flags": [1]}}]
        history.append("t1", rows, "car")
        rows[0]["details"]["flags"].append(2)
        rows.append({"key": "new"})

        sample = history.samples[0]
        sample["rows"][0]["details"]["flags"].append(3)
        sample["source"] = "changed"
        self.assertEqual(history.samples[0], {
            "timestamp": "t1", "source": "car",
            "rows": [{"key": "soc", "value": 50, "details": {"flags": [1]}}],
        })

    def test_series_marks_errors_missing_values_and_nonfinite_values_as_gaps(self):
        history = History()
        history.append("t1", [{"key": "soc", "value": 42.5}], "car")
        history.append("t2", [{"key": "soc", "value": 0, "error": "unavailable"}], "car")
        history.append("t3", [], "car")
        history.append("t4", [{"key": "soc", "value": float("nan")}], "car")
        history.append("t5", [{"key": "soc", "value": float("inf")}], "car")
        history.append("t6", [{"key": "soc", "value": True}], "car")
        history.append("t7", [{"key": "soc", "value": "42"}], "car")

        self.assertEqual(history.series("soc"), [
            ("t1", 42.5), ("t2", None), ("t3", None), ("t4", None),
            ("t5", None), ("t6", None), ("t7", None),
        ])
        self.assertEqual(history.series("unknown"), [(f"t{i}", None) for i in range(1, 8)])

    def test_clear_removes_all_samples_and_series(self):
        history = History()
        history.append("t1", [{"key": "soc", "value": 42}], "car")
        history.clear()
        self.assertEqual(history.samples, [])
        self.assertEqual(history.series("soc"), [])

    def test_csv_is_explicit_utf8_bom_and_protects_formula_strings(self):
        history = History()
        rows = [
            {"key": "=cmd", "name": " @SUM(A1:A2)", "value": -12.5,
             "unit": "-unit", "raw": "+1", "error": None},
            {"key": "next", "name": "Normal", "value": None,
             "unit": "V", "raw": "00", "error": "=failed"},
        ]
        history.append("-timestamp", rows, " +vehicle")
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "history.csv")
            self.assertFalse(os.path.exists(path))
            history.export_csv(path)

            with open(path, "rb") as file:
                content = file.read()
            self.assertTrue(content.startswith(b"\xef\xbb\xbf"))
            with open(path, encoding="utf-8-sig", newline="") as file:
                records = list(csv.DictReader(file))

        self.assertEqual(list(records[0]), [
            "source", "read_at", "key", "name", "value", "unit", "raw", "error",
        ])
        self.assertEqual(records[0], {
            "source": "' +vehicle", "read_at": "'-timestamp", "key": "'=cmd",
            "name": "' @SUM(A1:A2)", "value": "-12.5", "unit": "'-unit",
            "raw": "'+1", "error": "",
        })
        self.assertEqual(records[1]["error"], "'=failed")
        self.assertEqual(records[1]["value"], "")

    def test_limit_must_be_positive_integer(self):
        for limit in (0, -1, True, 1.5):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                History(limit=limit)


if __name__ == "__main__":
    unittest.main()
