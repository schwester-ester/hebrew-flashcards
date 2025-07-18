from typing import List
from itertools import chain, combinations


def yes_or_no_input(question: str) -> bool:
    return int(input(f"{question} (0 = yes, 1 = no)").strip()) == 0


def remove_duplicates(seq) -> List:
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))
