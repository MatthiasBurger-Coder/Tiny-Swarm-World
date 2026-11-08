"""Physical module paths and historical release paths keep state anchors stable."""
from pathlib import Path
import tempfile
import unittest

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_layout import configuration_member, infra_root, source_root
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths


class ProductLayoutTests(unittest.TestCase):
    def test_physical_and_historical_release_layouts(self):
        for prefix in ('modules/tsw_core', ''):
            with self.subTest(prefix=prefix), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = root / prefix / 'src'
                (source / 'tiny_swarm_world').mkdir(parents=True)
                (source / 'tiny_swarm_world/__main__.py').write_text('# release fixture\n')
                infra = root / prefix / 'infra'
                infra.mkdir()
                self.assertEqual(source_root(root), source)
                self.assertEqual(infra_root(root), infra)

    def test_missing_physical_module_cannot_be_hidden_by_legacy_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'modules/tsw_core').mkdir(parents=True)
            (root / 'src/tiny_swarm_world').mkdir(parents=True)
            (root / 'src/tiny_swarm_world/__main__.py').write_text('# stale legacy fixture\n')
            (root / 'infra').mkdir()
            for resolver in (source_root, infra_root):
                with self.assertRaises(LifecycleStateError):
                    resolver(root)

    def test_deleted_declared_module_and_dangling_module_link_deny_legacy_fallback(self):
        for case in ('declared', 'dangling', 'invalid-metadata'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / 'src/tiny_swarm_world').mkdir(parents=True)
                (root / 'src/tiny_swarm_world/__main__.py').write_text('# stale legacy source\n')
                (root / 'infra').mkdir()
                if case == 'declared':
                    (root / 'pyproject.toml').write_text('[tool.setuptools.packages.find]\nwhere=["modules/tsw_core/src"]\n')
                elif case == 'dangling':
                    (root / 'modules').mkdir()
                    (root / 'modules/tsw_core').symlink_to(root / 'absent-core')
                else:
                    (root / 'pyproject.toml').write_text('invalid = [')
                for resolver in (source_root, infra_root):
                    with self.assertRaises(LifecycleStateError):
                        resolver(root)

    def test_explicit_historical_metadata_still_uses_historical_release_layout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'src/tiny_swarm_world').mkdir(parents=True)
            (root / 'src/tiny_swarm_world/__main__.py').write_text('# historical release\n')
            (root / 'infra').mkdir()
            (root / 'pyproject.toml').write_text('[tool.setuptools.packages.find]\nwhere=["src"]\n')
            self.assertEqual(source_root(root), root / 'src')
            self.assertEqual(infra_root(root), root / 'infra')

    def test_config_members_accept_both_release_layouts_and_deny_escapes(self):
        for path in ('infra/config/ports.yaml', 'modules/tsw_core/infra/config/ports.yaml'):
            self.assertEqual(configuration_member(path), Path('config/ports.yaml'))
        for path in ('../infra/config', '/infra/config', 'modules/tsw_windows_wsl/infra/config', 'infra/../secret'):
            with self.subTest(path=path), self.assertRaises(LifecycleStateError):
                configuration_member(path)

    def test_module_relocation_does_not_move_state_or_infra_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'deployment'
            paths = ProjectPaths.from_roots(root)
            self.assertEqual(paths.repository_root, root)
            self.assertEqual(paths.source_root, root / 'modules/tsw_core/src')
            self.assertEqual(paths.config_root, root / 'modules/tsw_core/infra/config')
            self.assertEqual(paths.local_state_root, root / '.tiny-swarm-world')
            override = Path(temporary) / 'operator-infra'
            overridden = ProjectPaths.from_roots(root, override)
            self.assertEqual(overridden.config_root, override / 'config')
            self.assertEqual(overridden.local_state_root, paths.local_state_root)
