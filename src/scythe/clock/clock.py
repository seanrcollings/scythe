from .numbers import BIG_NUMBERS, BIG_COLON, SMALL_COLON, SMALL_NUMBERS


def extract_places(value: int) -> tuple[int, int]:
    """Given a number x | 9 < x < 100
    extract the places as values.

    extract_places(17) -> (1, 7)
    """
    tens_place = int(value % 100 / 10)
    ones_place = value % 10
    return tens_place, ones_place


def clock(hours, minutes, size="small"):
    """Retrun a bulky ASCII art clock
    given a number of hours and minutes
    """
    if size == "small":
        numbers = SMALL_NUMBERS
        colon = SMALL_COLON
    elif size == "big":
        numbers = BIG_NUMBERS
        colon = BIG_COLON
    else:
        raise ValueError("Size must be either small or big, was: " + size)

    if hours > 9:
        tens, ones = extract_places(hours)
        hours_str = join_numbers(numbers[tens], numbers[ones])
    else:
        hours_str = numbers[hours]

    if minutes > 9:
        tens, ones = extract_places(minutes)
        minutes_str = join_numbers(numbers[tens], numbers[ones])
    else:
        minutes_str = join_numbers(numbers[0], numbers[minutes])

    return join_numbers(hours_str, colon, minutes_str)


def join_numbers(*nums: str) -> str:
    joined: str = ""
    for lines in zip(*(num.split("\n") for num in nums)):
        joined += "    ".join(lines)
        joined += "\n"

    return joined
    # return "\n".join(
    #     "     ".join(lines) for lines in zip(*(num.split("\n") for num in nums))
    # )
