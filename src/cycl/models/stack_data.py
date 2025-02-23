from __future__ import annotations


class StackData:
    def __init__(  # noqa: PLR0913
        self,
        stack_name: str,
        stack_id: str | None = None,
        export_name: str | None = None,
        export_value: str | None = None,
        parent_id: str | None = None,
        root_id: str | None = None,
        tags: str | None = None,
        outputs: list[str] | None = None,
        importing_stacks: list[StackData] | None = None,
    ) -> None:
        self.stack_name = stack_name
        self.stack_id = stack_id
        self.export_name = export_name
        self.export_value = export_value
        self.parent_id = parent_id
        self.root_id = root_id
        self.tags = tags
        self.outputs = outputs or []
        self.importing_stacks = importing_stacks or []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StackData):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        return hash(tuple((key, tuple(value) if isinstance(value, list) else value) for key, value in self.__dict__.items()))

    def add_importing_stack(self, stack: StackData) -> None:
        self.importing_stacks.append(stack)
