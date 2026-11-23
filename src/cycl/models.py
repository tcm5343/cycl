from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True, slots=True, kw_only=True)
class Stack:
    """A CloudFormation stack.

    Stacks are identified by ``name`` and ``id``, so stacks with the same name in different accounts or regions
    are different stacks. ``tags`` is not used for equality or hashing.

    Attributes:
        name: The stack name.
        id: The stack ARN. ``None`` when not known: from :func:`~cycl.fetch_exports`, that is a stack which only
            imports, unless fetched with ``describe_stacks=True``.
        tags: The stack tags, as a read-only mapping of key to value. Empty unless fetched with ``describe_stacks=True``.
    """

    name: str
    id: str | None = None
    tags: Mapping[str, str] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        # copy into a read-only mapping, so a frozen Stack cannot be changed through its tags
        object.__setattr__(self, 'tags', MappingProxyType(dict(self.tags)))


@dataclass(frozen=True, slots=True, kw_only=True)
class Export:
    """A CloudFormation export, along with the stack exporting it and the stacks importing it.

    Attributes:
        name: The export name.
        value: The exported value.
        exporting_stack: The stack which defines the export.
        importing_stacks: The stacks which import the export, without duplicates.
    """

    name: str
    value: str
    exporting_stack: Stack
    importing_stacks: tuple[Stack, ...] = ()
