"""Official public release resolution. Preview performs bounded reads only."""
import hashlib
import re
import tomllib

import requests

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.models import ProductIdentity
from tiny_swarm_world.domain.lifecycle.product_upgrade import (
    PRODUCT_UPGRADE_TARGETS, RC6_RELEASES, ProductRelease, SOURCE_REVISION, TARGET_REVISION,
)
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_layout import configuration_member

OFFICIAL_REPOSITORY = 'https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World.git'
API = 'https://api.github.com/repos/MatthiasBurger-Coder/Tiny-Swarm-World'
RAW = 'https://raw.githubusercontent.com/MatthiasBurger-Coder/Tiny-Swarm-World'


class OfficialProductSource:
    def _get(self, url):
        try:
            response = requests.get(url, timeout=(5, 30), allow_redirects=False)
            response.raise_for_status()
            if response.status_code != 200 or len(response.content) > 4 * 1024 * 1024:
                raise ValueError
            return response
        except (requests.RequestException, ValueError):
            raise LifecycleStateError('Official release unavailable; publishing a release is a separate operation.') from None

    def resolve(self, target):
        if target not in PRODUCT_UPGRADE_TARGETS:
            raise LifecycleStateError('Unsupported product target. Downgrade is unsupported.')
        rc6 = target in RC6_RELEASES
        try:
            release = self._get(API + '/releases/tags/' + target).json()
            if release['draft'] or (release['prerelease'] and not rc6) or release['tag_name'] != target:
                raise ValueError
            reference = self._get(API + '/git/ref/tags/' + target).json()['object']
            if reference['type'] == 'tag':
                reference = self._get(API + '/git/tags/' + reference['sha']).json()['object']
            revision = reference['sha']
            expected_revision = release['target_commitish'] if rc6 else TARGET_REVISION
            if reference['type'] != 'commit' or re.fullmatch('[0-9a-f]{40}', revision) is None or revision != expected_revision:
                raise ValueError
            base = RAW + '/' + revision + '/'
            project = tomllib.loads(self._get(base + 'pyproject.toml').text)['project']
            lock = self._get(base + 'requirements.lock').content
            source_revision = TARGET_REVISION if rc6 else SOURCE_REVISION
            comparison = self._get(API + '/compare/' + source_revision + '...' + revision).json()
            if comparison['status'] != 'ahead':
                raise ValueError
            if rc6 and project['version'] != target:
                raise ValueError
            configuration = self._configuration_changes(revision, source_revision=source_revision, relocate=rc6)
            return ProductRelease(product=ProductIdentity(release=target, revision=revision,
                dependency_lock='sha256:' + hashlib.sha256(lock).hexdigest()), package_version=project['version']), configuration
        except (ValueError, KeyError, TypeError):
            raise LifecycleStateError('Official release metadata, migration policy or ancestry is unsupported; inspect release evidence.') from None

    def _configuration_changes(self, revision, *, source_revision=SOURCE_REVISION, relocate=False):
        trees = []
        for commit in (source_revision, revision):
            payload = self._get(API + '/git/trees/' + commit + '?recursive=1').json()
            if payload['truncated']:
                raise ValueError
            entries = {item['path']: item for item in payload['tree']
                       if item['path'].startswith(('infra/', 'modules/tsw_core/infra/')) and item['type'] == 'blob'}
            if any(item['mode'] == '120000' for item in entries.values()):
                raise ValueError
            trees.append(entries)
        before, after = trees
        if relocate:
            return self._relocated_changes(before, after)
        if set(before) - set(after):
            raise ValueError('Configuration removal needs a separately admitted migration.')
        return tuple(sorted(name for name, item in after.items() if before.get(name) != item))

    @staticmethod
    def _relocated_changes(before, after):
        legacy_prefix = 'infra/'
        physical_prefix = 'modules/tsw_core/infra/'
        if (not before or not after or not all(path.startswith(legacy_prefix) for path in before)
                or not all(path.startswith(physical_prefix) for path in after)):
            raise ValueError('Unexpected source or target infrastructure layout.')
        original = {configuration_member(path): (item['sha'], item['mode']) for path, item in before.items()}
        installed = {configuration_member(path): (item['sha'], item['mode']) for path, item in after.items()}
        if original.keys() - installed.keys():
            raise ValueError('Infrastructure members cannot be removed by layout migration.')
        return tuple(sorted(path for path in after
                            if installed[configuration_member(path)] != original.get(configuration_member(path))))


def release_policy():
    return {'schema_version': 1, 'source_release': '0.4.0', 'source_revision': SOURCE_REVISION,
            'source_package_version': '0.2.0', 'target_release': '0.5.0', 'target_revision': TARGET_REVISION,
            'target_package_version': '0.2.0',
            'source_supported_manifest_schemas': [1], 'target_supported_manifest_schemas': [1],
            'hosts': ['native-linux', 'wsl2'], 'configuration_schema': 1,
            'migrations': ['protected-infra-v1', 'installation-product-v1'],
            'component_policy': 'preserve-installed-images', 'downgrade': 'unsupported'}
