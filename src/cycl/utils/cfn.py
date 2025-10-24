from logging import getLogger

log = getLogger(__name__)


def parse_name_from_id(stack_id: str) -> str:
    """Extract the stack name from a given stack ID.

    Args:
        stack_id: The full stack ID, typically in the format
            'arn:aws:cloudformation:region:account-id:stack/stack-name/guid'.

    Returns:
        The extracted stack name, or an empty string if parsing fails.

    Note:
        Logs a warning if the stack ID format is unexpected.
    """
    try:
        return stack_id.split('/')[1]
    except IndexError:
        log.warning('Unable to parse stack_name from stack_id: %s', stack_id)
        return ''
