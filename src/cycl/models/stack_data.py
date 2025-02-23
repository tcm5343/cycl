from __future__ import annotations


class StackData:
    def __init__(  # noqa: PLR0913
        self,
        stack_name: str,
        stack_id: str | None = None,
        name: str | None = None,
        value: str | None = None,
        parent_id: str | None = None,
        root_id: str | None = None,
        tags: str | None = None,
        outputs: list[str] | None = None,
        importing_stacks: list[StackData] | None = None,
    ) -> StackData:
        self.stack_name = stack_name
        self.stack_id = stack_id
        self.name = name
        self.value = value
        self.parent_id = parent_id
        self.root_id = root_id
        self.tags = tags
        self.outputs = outputs or []
        self.importing_stacks = importing_stacks or []

    def add_importing_stack(self, stack: StackData) -> None:
        self.importing_stacks.append(stack)
