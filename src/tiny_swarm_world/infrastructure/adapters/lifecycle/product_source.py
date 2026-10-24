"""Official public release resolution. Preview performs bounded reads only."""
import hashlib
import re
import tomllib

import requests

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.models import ProductIdentity
from tiny_swarm_world.domain.lifecycle.product_upgrade import ProductRelease, SOURCE_REVISION, TARGET_RELEASE, TARGET_REVISION

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
        if target != TARGET_RELEASE:
            raise LifecycleStateError('Unsupported product target; only 0.5.0 is admitted. Downgrade is unsupported.')
        try:
            release = self._get(API + '/releases/tags/' + target).json()
            if release['draft'] or release['prerelease'] or release['tag_name'] != target:
                raise ValueError
            reference = self._get(API + '/git/ref/tags/' + target).json()['object']
            if reference['type'] == 'tag':
                reference = self._get(API + '/git/tags/' + reference['sha']).json()['object']
            revision = reference['sha']
            if reference['type'] != 'commit' or re.fullmatch('[0-9a-f]{40}', revision) is None or revision != TARGET_REVISION:
                raise ValueError
            base = RAW + '/' + revision + '/'
            project = tomllib.loads(self._get(base + 'pyproject.toml').text)['project']
            lock = self._get(base + 'requirements.lock').content
            comparison = self._get(API + '/compare/' + SOURCE_REVISION + '...' + revision).json()
            if comparison['status'] != 'ahead':
                raise ValueError
            configuration = self._configuration_changes(revision)
            return ProductRelease(product=ProductIdentity(release=target, revision=revision,
                dependency_lock='sha256:' + hashlib.sha256(lock).hexdigest()), package_version=project['version']), configuration
        except (ValueError, KeyError, TypeError):
            raise LifecycleStateError('Official release metadata, migration policy or ancestry is unsupported; inspect release evidence.') from None

    def _configuration_changes(self, revision):
        trees = []
        for commit in (SOURCE_REVISION, revision):
            payload = self._get(API + '/git/trees/' + commit + '?recursive=1').json()
            if payload['truncated']:
                raise ValueError
            entries = {item['path']: item for item in payload['tree']
                       if item['path'].startswith('infra/') and item['type'] == 'blob'}
            if any(item['mode'] == '120000' for item in entries.values()):
                raise ValueError
            trees.append(entries)
        before, after = trees
        if set(before) - set(after):
            raise ValueError('Configuration removal needs a separately admitted migration.')
        return tuple(sorted(name for name, item in after.items() if before.get(name) != item))


def release_policy():
    return {'schema_version': 1, 'source_release': '0.4.0', 'source_revision': SOURCE_REVISION,
            'source_package_version': '0.2.0', 'target_release': '0.5.0', 'target_revision': TARGET_REVISION,
            'target_package_version': '0.2.0',
            'hosts': ['native-linux', 'wsl2'], 'configuration_schema': 1,
            'migrations': ['protected-infra-v1', 'installation-product-v1'],
            'component_policy': 'preserve-installed-images', 'downgrade': 'unsupported'}
