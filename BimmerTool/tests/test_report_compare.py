import json
import os
import tempfile
import unittest

from bimmertool.report_compare import FORMAT, compare_reports, load_report


def report(dtcs, source="simulator", vin="WBA123", **extra):
    return {"format": FORMAT, "source": source, "vin": vin, "dtcs": dtcs, **extra}


def module(ecu=114, codes=None, error=None):
    return {"ecu": ecu, "error": error,
            "codes": codes if error is None else None}


class ReportCompareTests(unittest.TestCase):
    def test_added_removed_and_status_changes(self):
        before = report([module(codes=[{"code": "123ABC", "status": 1},
                                       {"code": "000001", "status": 4}])])
        after = report([module(codes=[{"code": "123ABC", "status": 2},
                                      {"code": "ABCDEF", "status": 3}])])
        rows = compare_reports(before, after)
        self.assertEqual(rows, [
            {"ecu": 114, "code": "000001", "before": 4, "after": None,
             "change": "Artık raporlanmıyor"},
            {"ecu": 114, "code": "123ABC", "before": 1, "after": 2,
             "change": "Durum değişti"},
            {"ecu": 114, "code": "ABCDEF", "before": None, "after": 3,
             "change": "Yeni kayıt"},
        ])

    def test_unchanged_codes_are_omitted(self):
        entry = [{"code": "123ABC", "status": 7}]
        self.assertEqual(compare_reports(report([module(codes=entry)]),
                                         report([module(codes=entry)])), [])

    def test_failed_or_missing_module_is_not_treated_as_resolved(self):
        before = report([module(codes=[{"code": "123ABC", "status": 1}]),
                         module(ecu=115, error="Yanıt yok")])
        after = report([module(error="Zaman aşımı")])
        self.assertEqual(compare_reports(before, after), [
            {"ecu": 114, "code": "—", "before": "Okundu", "after": "Zaman aşımı",
             "change": "Karşılaştırılamadı"},
            {"ecu": 115, "code": "—", "before": "Yanıt yok", "after": "Okunamadı",
             "change": "Karşılaştırılamadı"},
        ])

    def test_source_and_known_vin_must_match(self):
        valid = report([])
        with self.assertRaises(ValueError):
            compare_reports(valid, report([], source="vehicle"))
        with self.assertRaises(ValueError):
            compare_reports(valid, report([], vin="WBA999"))
        self.assertEqual(compare_reports(report([], vin=None), valid), [])

    def test_loads_own_valid_report_schema(self):
        expected = report([module(codes=[{"code": "ABC123", "status": 0}])])
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "report.json")
            with open(path, "w", encoding="utf-8") as file:
                json.dump(expected, file)
            self.assertEqual(load_report(path), expected)

    def test_rejects_invalid_data(self):
        valid = report([module(codes=[])])
        invalids = [
            {**valid, "format": "other"},
            {**valid, "source": "unknown"},
            {**valid, "dtcs": [{"ecu": 114, "codes": []}]},
            report([module(ecu=True, codes=[])]),
            report([module(ecu=65536, codes=[])]),
            report([module(codes=[{"code": "12345G", "status": 1}])]),
            report([module(codes=[{"code": "123456", "status": True}])]),
            report([module(codes=[{"code": "123456", "status": None}])]),
            report([module(codes=[{"code": "123456"}])]),
            report([module(codes=[{"code": "123456", "status": 256}])]),
            report([module(codes=[{"code": "123456", "status": 1},
                                  {"code": "123456", "status": 2}])]),
            {**valid, "dtcs": [{"ecu": 114, "error": "Yanıt yok", "codes": []}]},
            report([module(ecu=114, codes=[]), module(ecu=114, codes=[])]),
        ]
        for item in invalids:
            with self.subTest(item=item), self.assertRaises(ValueError):
                compare_reports(item, valid)

    def test_rejects_oversize_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "oversize.json")
            with open(path, "wb") as file:
                file.truncate(5 * 1024 * 1024 + 1)
            with self.assertRaises(ValueError):
                load_report(path)


if __name__ == "__main__":
    unittest.main()
