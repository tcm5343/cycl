from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True, kw_only=True)
class Stack:
    """A CloudFormation stack.

    Stacks are identified by name; ``id`` is informational and is not used for equality or hashing, since
    ``ListImports`` only returns stack names.

    Attributes:
        name: The stack name.
        id: The stack ARN, when known.
    """

    name: str
    id: str | None = field(default=None, compare=False)


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
