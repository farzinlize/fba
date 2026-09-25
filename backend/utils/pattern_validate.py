import re


def search_string(pattern: str, text: str) -> re.Match[str]:
    """
    Match the entire field using a regular expression

    :param pattern: Regular expression pattern
    :param text: Text to match
    :return:
    """
    return re.search(pattern, text)


def match_string(pattern: str, text: str) -> re.Match[str]:
    """
    Match from the start of the field using a regular expression

    :param pattern: Regular expression pattern
    :param text: Text to match
    :return:
    """
    return re.match(pattern, text)


def is_phone(number: str) -> re.Match[str]:
    """
    Validate mobile phone number format

    :param number: Mobile phone number to validate
    :return:
    """
    phone_pattern = r'^1[3-9]\d{9}$'
    return match_string(phone_pattern, number)


def is_git_url(url: str) -> re.Match[str]:
    """
    Validate Git URL format (HTTP/HTTPS only)

    :param url: URL to validate
    :return:
    """
    git_pattern = r'^(?P<scheme>https?)://(?P<host>[^/]*)(?P<path>(?:/[^/]*)*/)(?P<repo>[^/]+?)(?:\.git)?$'
    return match_string(git_pattern, url)


def is_has_number(value: str) -> re.Match[str]:
    """
    Check for digits

    :param value: Value to check
    :return:
    """
    number_pattern = r'\d'
    return search_string(number_pattern, value)


def is_has_letter(value: str) -> re.Match[str]:
    """
    Check for letters

    :param value: Value to check
    :return:
    """
    letter_pattern = r'[a-zA-Z]'
    return search_string(letter_pattern, value)


def is_has_special_char(value: str) -> re.Match[str]:
    """
    Check for special characters

    :param value: Value to check
    :return:
    """
    special_char_pattern = r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]'
    return search_string(special_char_pattern, value)


def is_english_identifier(value: str) -> re.Match[str]:
    """
    Validate English identifier

    :param value: Value to check
    :return:
    """
    identifier_pattern = r'^[a-zA-Z][a-zA-Z_]*$'
    return match_string(identifier_pattern, value)
