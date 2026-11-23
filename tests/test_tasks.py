import contextlib
import io
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from termnote import cli, config, domains, tasks
from termnote.dates import format_date


class ParseTest(unittest.TestCase):
    def test_round_trip(self):
        line = "- [ ] PR'ı incele (18-10-2026) @iş #frontend #acil ^43"
        t = tasks.parse_task_line(line)
        self.assertEqual(
            t,
            {
                "id": 43,
                "done": False,
                "text": "PR'ı incele",
                "date": "18-10-2026",
                "domain": "iş",
                "tags": ["frontend", "acil"],
            },
        )
        self.assertEqual(tasks.format_task_line(t), line)

    def test_tokens_in_any_order(self):
        t = tasks.parse_task_line("- [ ] ^7 #acil raporu @iş (18-10-2026) yaz")
        self.assertEqual((t["id"], t["domain"]), (7, "iş"))
        self.assertEqual((t["date"], t["tags"]), ("18-10-2026", ["acil"]))
        self.assertEqual(t["text"], "raporu yaz")

    def test_missing_metadata(self):
        t = tasks.parse_task_line("- [ ] sade")
        self.assertEqual(t["text"], "sade")
        self.assertEqual((t["id"], t["domain"], t["date"]), (None, None, None))
        self.assertEqual(t["tags"], [])

    def test_metadata_lookalikes_stay_in_text(self):
        for text in (
            "x^2 hesapla",
            "^2 hesapla",
            "mail a@b.com",
            "@ali ara",
            "C# öğren",
            "bug#12 düzelt",
            "toplantı (01-01-2020) notu",
            "iki  boşluk",
        ):
            with self.subTest(text=text):
                line = f"- [ ] {text} (18-10-2026) @iş ^43"
                t = tasks.parse_task_line(line)
                self.assertEqual(t["text"], text)
                self.assertEqual((t["id"], t["domain"]), (43, "iş"))
                self.assertEqual((t["date"], t["tags"]), ("18-10-2026", []))
                self.assertEqual(tasks.format_task_line(t), line)

    def test_standalone_hash_is_a_tag(self):
        t = tasks.parse_task_line("- [ ] bug #12 düzelt @iş ^1")
        self.assertEqual((t["text"], t["tags"]), ("bug düzelt", ["12"]))

    def test_checkbox_variants(self):
        for line, done in (("- [x] a", True), ("- [X] a", True), ("  - [ ] a", False)):
            with self.subTest(line=line):
                self.assertEqual(tasks.parse_task_line(line)["done"], done)

    def test_non_task_lines(self):
        for line in ("", "\n", "## Bu hafta", "- not", "düz metin"):
            with self.subTest(line=line):
                self.assertIsNone(tasks.parse_task_line(line))


class FileTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "tasks.md"
        for target, name, value in (
            (tasks, "TASKS_PATH", self.path),
            (config, "CONFIG_PATH", Path(tmp.name) / "config"),
            # Keep the CLI from creating files in the real home directory.
            (cli, "ensure_storage", lambda: None),
        ):
            patcher = mock.patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        domains.add_domain("test")

    def write(self, content):
        self.path.write_bytes(content.encode())

    def read(self):
        return self.path.read_bytes().decode()

    MIXED = "## Week\n\nnote\n- [X] old ^1\n  - [ ]  #b two @test  ^2\n- [ ] three ^3\n"

    def test_add_preserves_existing_content(self):
        self.write(self.MIXED)
        t = tasks.add_task("new", "test")
        self.assertEqual(t["id"], 4)
        self.assertEqual(self.read(), self.MIXED + tasks.format_task_line(t) + "\n")

    def test_add_without_trailing_newline(self):
        self.write("- [ ] one ^1")
        t = tasks.add_task("new", "test")
        self.assertEqual(
            self.read(), "- [ ] one ^1\n" + tasks.format_task_line(t) + "\n"
        )

    def test_done_changes_only_the_checkbox(self):
        self.write(self.MIXED)
        self.assertTrue(tasks.mark_done(2)["done"])
        self.assertEqual(self.read(), self.MIXED.replace("- [ ]  #b", "- [x]  #b"))

    def test_done_preserves_crlf(self):
        self.write("# h\r\n- [ ] one ^1\r\n")
        tasks.mark_done(1)
        self.assertEqual(self.read(), "# h\r\n- [x] one ^1\r\n")

    def test_done_unknown_id_leaves_file_alone(self):
        self.write("- [ ] x^2 ^5\n")
        with self.assertRaises(ValueError):
            tasks.mark_done(2)
        self.assertEqual(self.read(), "- [ ] x^2 ^5\n")

    def test_impossible_date_does_not_break_listings(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        self.write(
            "- [ ] bad (31-02-2026) ^1\n"
            f"- [ ] now ({format_date(today)}) ^2\n"
            f"- [ ] late ({format_date(yesterday)}) ^3\n"
            "- [x] closed (31-02-2026) ^4\n"
        )
        self.assertEqual([t["id"] for t in tasks.list_today()], [2])
        self.assertEqual([t["id"] for t in tasks.list_overdue()], [3])
        self.assertEqual([t["id"] for t in tasks.list_invalid_dates()], [1])

        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            cli.main(["task", "list"])
        self.assertIn("now", out.getvalue())
        self.assertEqual(err.getvalue().count("Warning"), 1)
        self.assertIn("bad", err.getvalue())


if __name__ == "__main__":
    unittest.main()
