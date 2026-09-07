import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('install_skill', ROOT / 'install-skill.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class SkillInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='skills-install-')
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)

    def test_install_is_repeatable_and_links_the_complete_skill(self):
        target = installer.install('unslop', 'codex', self.home, {})
        self.assertTrue((target / 'SKILL.md').is_file())
        self.assertTrue((target / 'agents/openai.yaml').is_file())
        self.assertEqual(installer.install('unslop', 'codex', self.home, {}), target)

    def test_existing_skill_is_preserved(self):
        target = self.home / '.claude/skills/unslop'
        target.mkdir(parents=True)
        (target / 'SKILL.md').write_text('my skill')
        with self.assertRaises(FileExistsError):
            installer.install('unslop', 'claude', self.home, {})
        self.assertEqual((target / 'SKILL.md').read_text(), 'my skill')
        self.assertEqual(list(target.iterdir()), [target / 'SKILL.md'])

    def test_dangling_foreign_link_is_preserved(self):
        target = self.home / '.codex/skills/unslop'
        target.parent.mkdir(parents=True)
        target.symlink_to(self.home / 'missing')
        with self.assertRaises(FileExistsError):
            installer.install('unslop', 'codex', self.home, {})
        self.assertEqual(target.readlink(), self.home / 'missing')

    def test_custom_client_directory_is_used(self):
        config = self.home / 'custom config'
        target = installer.install('unslop', 'codex', self.home, {'CODEX_HOME': str(config)})
        self.assertEqual(target, config / 'skills/unslop')

    def test_upstream_skill_and_license_match_the_recorded_snapshot(self):
        package = ROOT / 'packages/unslop'
        origin = json.loads((package / 'upstream.json').read_text())
        for record in origin['files']:
            self.assertEqual(hashlib.sha256((package / record['path']).read_bytes()).hexdigest(), record['sha256'], record['path'])


if __name__ == '__main__':
    unittest.main()
