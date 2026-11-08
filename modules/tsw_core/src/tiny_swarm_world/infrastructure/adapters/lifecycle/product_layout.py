"""Resolve physical or historical release trees without relocating product state."""
from pathlib import Path
import tomllib

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError

CORE = Path('modules/tsw_core')
INFRA_PREFIXES = (CORE / 'infra', Path('infra'))


def _declares_physical(checkout: Path) -> bool:
    core = checkout / CORE
    if core.is_symlink() or (checkout / 'modules').is_symlink():
        raise LifecycleStateError('Release module roots must not be symlinks.')
    if core.exists():
        return True
    metadata = checkout / 'pyproject.toml'
    if metadata.is_symlink():
        raise LifecycleStateError('Release metadata must not be a symlink.')
    if not metadata.exists():
        return False
    try:
        if metadata.stat().st_size > 262144:
            raise ValueError('oversized release metadata')
        project = tomllib.loads(metadata.read_text(encoding='utf-8'))
        settings = project.get('tool', {}).get('setuptools', {})
        where = settings.get('packages', {}).get('find', {}).get('where', [])
        where = [where] if isinstance(where, str) else where
        return ('modules/tsw_core/src' in where
                or 'modules/tsw_core/src' in settings.get('package-dir', {}).values())
    except (OSError, ValueError, TypeError, AttributeError) as error:
        raise LifecycleStateError('Release layout metadata is unsafe or invalid.') from error


def source_root(checkout: Path) -> Path:
    """Use legacy source only for a historical checkout with no physical core."""
    declared = _declares_physical(checkout)
    physical = checkout / CORE / 'src'
    if (physical / 'tiny_swarm_world/__main__.py').is_file():
        return physical
    legacy = checkout / 'src'
    if not declared and (legacy / 'tiny_swarm_world/__main__.py').is_file():
        return legacy
    raise LifecycleStateError('Release Python source is missing from its declared layout.')


def infra_root(checkout: Path) -> Path:
    """Resolve versioned code assets; protected state/infra stays unchanged."""
    declared = _declares_physical(checkout)
    physical = checkout / CORE / 'infra'
    if physical.is_dir():
        return physical
    legacy = checkout / 'infra'
    if not declared and legacy.is_dir():
        return legacy
    raise LifecycleStateError('Release infrastructure is missing from its declared layout.')


def configuration_member(relative: str | Path) -> Path:
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts:
        raise LifecycleStateError('Release configuration path is unsafe.')
    for prefix in INFRA_PREFIXES:
        if path.is_relative_to(prefix) and path != prefix:
            return path.relative_to(prefix)
    raise LifecycleStateError('Release configuration path is outside core infrastructure.')
