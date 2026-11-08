"""Closed service exposure policy; no runtime or routing effects."""
from collections.abc import Mapping
from typing import Literal

Exposure = Literal['published', 'internal']


def service_exposure_for(selected: tuple[str, ...] | None,
                         exposure: Mapping[str, str] | None = None) -> dict[str, Exposure]:
    keys = {'swagger'} if selected is None or 'swagger' in selected else set()
    if exposure is None:
        return {name: 'published' for name in keys}
    if set(exposure) != keys or any(type(value) is not str or value not in {'published', 'internal'}
                                    for value in exposure.values()):
        raise ValueError('Exposure must map exactly selected Swagger to published or internal.')
    return {name: 'internal' if exposure[name] == 'internal' else 'published' for name in keys}
