import dataclasses

import pytest

from cycl import Export, Stack


def test_stack_equality_uses_name_and_id_but_not_tags():
    assert Stack(name='a', id='arn:a', tags={'k': 'v'}) == Stack(name='a', id='arn:a')
    assert hash(Stack(name='a', id='arn:a', tags={'k': 'v'})) == hash(Stack(name='a', id='arn:a'))
    assert Stack(name='a', id='arn:dev:a') != Stack(name='a', id='arn:prod:a')
    assert Stack(name='a') != Stack(name='b')


def test_stack_defaults_to_no_tags():
    assert Stack(name='a').tags == {}


def test_stack_tags_are_read_only_copies():
    tags = {'k': 'v'}
    stack = Stack(name='a', tags=tags)
    tags['k'] = 'changed'

    assert stack.tags == {'k': 'v'}
    with pytest.raises(TypeError):
        stack.tags['k'] = 'changed'  # type: ignore[index]


def test_models_are_frozen():
    stack = Stack(name='a')
    export = Export(name='e', value='v', exporting_stack=stack)

    with pytest.raises(dataclasses.FrozenInstanceError):
        stack.name = 'b'  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        export.importing_stacks = (stack,)  # type: ignore[misc]


def test_models_are_keyword_only():
    with pytest.raises(TypeError):
        Stack('a')  # type: ignore[misc]


def test_export_is_hashable():
    export = Export(name='e', value='v', exporting_stack=Stack(name='a'), importing_stacks=(Stack(name='b'),))
    assert {export, dataclasses.replace(export)} == {export}


def test_export_defaults_to_no_importing_stacks():
    assert Export(name='e', value='v', exporting_stack=Stack(name='a')).importing_stacks == ()
