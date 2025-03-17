def is_circular_reversible_permutation(lst: list, candidate: list) -> bool:
    """The output cycle is non-deterministic, it could be reversed and any node could be the start."""
    extended_lst = lst + lst
    extended_lst_reverse = lst[::-1] + lst[::-1]
    return any(extended_lst[i : i + len(candidate)] == candidate for i in range(len(lst))) or any(
        extended_lst_reverse[i : i + len(candidate)] == candidate for i in range(len(lst))
    )
