"""Number-to-words conversion for Indonesian text."""

import re
from num2words import num2words

def convert(input_string: str) -> str:
    """
    Convert all numeric digits in a string to Indonesian words.

    Finds all sequences of digits and replaces them with their Indonesian word equivalents.
    This ensures more natural TTS output by converting numbers like "123" to
    "seratus dua puluh tiga".

    Args:
        input_string: Text containing numbers to convert

    Returns:
        str: Text with all numbers converted to Indonesian words

    Example:
        >>> convert("Saya punya 3 apel")
        'Saya punya tiga apel'
        >>> convert("Harga Rp 15000")
        'Harga Rp lima belas ribu'
    """
    numbers = re.findall(r'\d+', input_string)

    for number in numbers:
        word = num2words(int(number), lang="id")
        input_string = input_string.replace(number, word)

    return input_string
