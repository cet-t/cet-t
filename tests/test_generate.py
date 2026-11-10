import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import generate  # noqa: E402
from generate import ConfigError  # noqa: E402


def build(toml_text: str) -> str:
    return generate.render(generate.validate(tomllib.loads(toml_text)))


SAMPLE = """
[[projects]]
repo = "moelle"
description = "Random number generator abstractions"

[[projects]]
repo = "splitmix"
description = "SplitMix32 / SplitMix64"

[[projects]]
repo = "clipboard-editor"

[[archive]]
repo = "urng"
description = "Random number generation library"
"""


class RenderTest(unittest.TestCase):
    def test_sample_output(self):
        expected = (
            "# Projects\n"
            "\n"
            "| Repository | Description |\n"
            "| --- | --- |\n"
            "| [moelle](https://github.com/cet-t/moelle) | Random number generator abstractions |\n"
            "| [splitmix](https://github.com/cet-t/splitmix) | SplitMix32 / SplitMix64 |\n"
            "| [clipboard-editor](https://github.com/cet-t/clipboard-editor) | |\n"
            "\n"
            "# Archive\n"
            "\n"
            "| Repository | Description |\n"
            "| --- | --- |\n"
            "| [urng](https://github.com/cet-t/urng) | Random number generation library |\n"
        )
        self.assertEqual(build(SAMPLE), expected)

    def test_order_preserved(self):
        out = build('[[projects]]\nrepo = "zeta"\n[[projects]]\nrepo = "alpha"\n[[projects]]\nrepo = "mid"\n')
        self.assertLess(out.index("[zeta]"), out.index("[alpha]"))
        self.assertLess(out.index("[alpha]"), out.index("[mid]"))

    def test_description_column_added(self):
        out = build('[[projects]]\nrepo = "a"\ndescription = "x"\n')
        self.assertIn("| Repository | Description |\n| --- | --- |\n| [a](https://github.com/cet-t/a) | x |", out)

    def test_description_column_omitted(self):
        out = build('[[archive]]\nrepo = "urng"\n')
        self.assertIn("# Archive\n\n| Repository |\n| --- |\n| [urng](https://github.com/cet-t/urng) |\n", out)
        self.assertNotIn("Description", out)

    def test_partial_descriptions(self):
        out = build('[[projects]]\nrepo = "a"\n[[projects]]\nrepo = "b"\ndescription = "B"\n')
        self.assertIn("| [a](https://github.com/cet-t/a) | |\n", out)
        self.assertIn("| [b](https://github.com/cet-t/b) | B |\n", out)

    def test_independent_columns_per_category(self):
        out = build('[[projects]]\nrepo = "a"\ndescription = "A"\n[[archive]]\nrepo = "b"\n')
        projects, archive = out.split("# Archive")
        self.assertIn("| Repository | Description |", projects)
        self.assertIn("| Repository |\n", archive)
        self.assertNotIn("Description", archive)

    def test_empty_categories(self):
        self.assertEqual(
            build(""),
            "# Projects\n\n| Repository |\n| --- |\n\n# Archive\n\n| Repository |\n| --- |\n",
        )
        out = build('[[archive]]\nrepo = "a"\n')
        self.assertTrue(out.startswith("# Projects\n\n| Repository |\n| --- |\n\n# Archive"))

    def test_special_characters_escaped(self):
        out = build('[[projects]]\nrepo = "a"\ndescription = "x | y \\\\ z\\nnext"\n')
        self.assertIn("| [a](https://github.com/cet-t/a) | x \\| y \\\\ z next |\n", out)

    def test_blank_description_treated_as_missing(self):
        out = build('[[projects]]\nrepo = "a"\ndescription = "  "\n')
        self.assertNotIn("Description", out)

    def test_name_used_as_label(self):
        out = build('[[projects]]\nname = "moelle / trng / urng_core"\nrepo = "moelle"\n')
        self.assertIn("| [moelle / trng / urng_core](https://github.com/cet-t/moelle) |\n", out)

    def test_repo_used_as_label_without_name(self):
        for extra in ["", 'name = "  "\n']:
            with self.subTest(extra=extra):
                out = build(f'[[projects]]\nrepo = "moelle"\n{extra}')
                self.assertIn("| [moelle](https://github.com/cet-t/moelle) |\n", out)

    def test_name_special_characters_escaped(self):
        out = build('[[projects]]\nrepo = "a"\nname = "x [y] | z"\n')
        self.assertIn("| [x \\[y\\] \\| z](https://github.com/cet-t/a) |\n", out)

    def test_duplicate_names_allowed(self):
        out = build('[[projects]]\nrepo = "a"\nname = "same"\n[[projects]]\nrepo = "b"\nname = "same"\n')
        self.assertEqual(out.count("[same]"), 2)

    def test_deterministic(self):
        self.assertEqual(build(SAMPLE), build(SAMPLE))


class ValidateTest(unittest.TestCase):
    def assertInvalid(self, toml_text: str, message: str):
        with self.assertRaises(ConfigError) as ctx:
            build(toml_text)
        self.assertIn(message, str(ctx.exception))

    def test_invalid_repo_names(self):
        for name in ["", "a b", "foo/bar", "..", ".", "a" * 101, "日本語", "../x"]:
            with self.subTest(name=name):
                self.assertInvalid(f'[[projects]]\nrepo = "{name}"\n', "invalid repository name")

    def test_valid_repo_names(self):
        for name in ["a", "A-b_c.d", "cet-t", ".github", "a" * 100]:
            with self.subTest(name=name):
                build(f'[[projects]]\nrepo = "{name}"\n')

    def test_missing_repo(self):
        self.assertInvalid('[[projects]]\ndescription = "x"\n', "'repo' is required")
        self.assertInvalid('[[projects]]\nname = "a"\n', "'repo' is required")

    def test_non_string_fields(self):
        self.assertInvalid("[[projects]]\nrepo = 1\n", "'repo' is required")
        self.assertInvalid('[[projects]]\nrepo = "a"\ndescription = 1\n', "'description' must be a string")
        self.assertInvalid('[[projects]]\nrepo = "a"\nname = 1\n', "'name' must be a string")

    def test_unknown_keys(self):
        self.assertInvalid('[[project]]\nrepo = "a"\n', "unknown top-level key")
        self.assertInvalid('[[projects]]\nrepo = "a"\nurl = "x"\n', "unknown field")

    def test_category_must_be_array(self):
        self.assertInvalid('projects = "a"\n', "array of tables")

    def test_duplicate_within_category(self):
        self.assertInvalid('[[projects]]\nrepo = "a"\n[[projects]]\nrepo = "a"\n', "duplicate")

    def test_duplicate_across_categories(self):
        self.assertInvalid('[[projects]]\nrepo = "Foo"\n[[archive]]\nrepo = "foo"\n', "duplicate")


class MainTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.config = self.dir / "projects.toml"
        self.output = self.dir / "README.md"

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self) -> int:
        return generate.main(["--config", str(self.config), "--output", str(self.output)])

    def test_writes_and_skips_unchanged(self):
        self.config.write_text(SAMPLE, encoding="utf-8")
        self.assertEqual(self.run_main(), 0)
        self.assertEqual(self.output.read_text(encoding="utf-8"), build(SAMPLE))
        mtime = self.output.stat().st_mtime_ns
        self.assertFalse(generate.write_if_changed(self.output, build(SAMPLE)))
        self.assertEqual(self.run_main(), 0)
        self.assertEqual(self.output.stat().st_mtime_ns, mtime)

    def test_invalid_config_leaves_readme_untouched(self):
        self.output.write_text("original\n", encoding="utf-8")
        for text in ['[[projects]]\nrepo = "bad name"\n', "not = [valid"]:
            with self.subTest(text=text):
                self.config.write_text(text, encoding="utf-8")
                self.assertEqual(self.run_main(), 1)
                self.assertEqual(self.output.read_text(encoding="utf-8"), "original\n")

    def test_missing_config(self):
        self.assertEqual(self.run_main(), 1)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
