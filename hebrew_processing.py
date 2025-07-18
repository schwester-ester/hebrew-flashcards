from util import remove_duplicates, powerset
from typing import List

PREFIX_ORDER = [["ו"], ["ש", "כ", "ב", "ל", "מ"], ["ה"]]
PREFIX_MEANINGS = {
    "ש": "that",
    "ו": "and",
    "כ": "as",
    "ב": "in",
    "ל": "to",
    "מ": "from",
    "ה": "the",
}


def find_variations(word: str) -> List[str]:
    """
    Returns a list (in decreasing likelihood) of variations of the word.
    Variations include trying to remove double yuds and trying to remove the prefixes.
    Not every word is guaranteed to be a real word or related to the meaning, as
    there are situations where the prefix is part of a word, and removing it results in 
    a completely different word or nonsense. 

    """
    vars1 = remove_prefixes(word)

    variations = [word]
    for var in vars1:
        variations = variations + find_double_yud(var)

    return remove_duplicates(variations)


def find_double_yud(word: str, char="י") -> List[str]:
    """
    Finds all the locations of a double yud and outputs a list of words
    where every possible combination of locations of double yud are replaced
    with a single yud. 

    """
    double_char = char * 2
    results = []

    where_doubles = []
    for i in range(len(word)):
        if word[i : i + 2] == double_char:
            where_doubles.append(i)

    for subset in powerset(where_doubles):
        index = 0
        new_word = word
        for num in range(len(subset)):
            loc_to_replace = subset[num] - num
            while index <= loc_to_replace:
                if index == loc_to_replace:
                    assert new_word[index : index + 2] == double_char, print(
                        index, word
                    )
                    new_word = new_word[:index] + char + new_word[index + 2 :]
                index += 1
        results.append(new_word)

    return results



def remove_prefixes(word: str) -> List[str]:
    """
    Outputs a list of words where the prefixes (if any) are removed sequentially.

    """
    new_word = word

    results = [new_word]
    
    for stage in PREFIX_ORDER:
        if any(new_word.startswith(letter) for letter in stage):
            new_word = new_word[1:]
            results.append(new_word)

    return results

