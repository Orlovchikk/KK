import re
from urllib.parse import urlsplit, urlunsplit


def punycode(domain):
    return domain.encode("idna").decode("ascii")


def validate_ipv6_address(address):
    try:
        import socket

        socket.inet_pton(socket.AF_INET6, address)
    except (socket.error, OSError):
        return False


def validate_url(value, schemes=None):
    """Validate a URL string and check if the domain is 'vk.com'."""
    ul = "\u00a1-\uffff"  # Unicode letters range

    # Regular expressions for different URL components
    ipv4_re = (
        r"(?:0|25[0-5]|2[0-4][0-9]|1[0-9]?[0-9]?|[1-9][0-9]?)"
        r"(?:\.(?:0|25[0-5]|2[0-4][0-9]|1[0-9]?[0-9]?|[1-9][0-9]?)){3}"
    )
    ipv6_re = r"\[[0-9a-f:.]+\]"  # Simplified IPv6 regex
    hostname_re = (
        r"[a-z" + ul + r"0-9](?:[a-z" + ul + r"0-9-]{0,61}[a-z" + ul + r"0-9])?"
    )
    domain_re = r"(?:\.(?!-)[a-z" + ul + r"0-9-]{1,63}(?<!-))*"
    tld_re = r"\.(?!-)(?:[a-z" + ul + "-]{2,63}|xn--[a-z0-9]{1,59})(?<!-)\.?"
    host_re = f"({hostname_re}{domain_re}{tld_re}|localhost)"

    # Full URL regex pattern
    url_regex = re.compile(
        r"^(?:[a-z0-9.+-]*)://"  # Scheme
        r"(?:[^\s:@/]+(?::[^\s:@/]*)?@)?"  # User:pass
        r"(?:" + ipv4_re + "|" + ipv6_re + "|" + host_re + ")"  # Host
        r"(?::[0-9]{1,5})?"  # Port
        r"(?:[/?#][^\s]*)?"  # Resource path
        r"\Z",
        re.IGNORECASE,
    )

    # Default schemes
    schemes = schemes or ["http", "https", "ftp", "ftps"]
    max_length = 2048
    unsafe_chars = frozenset("\t\r\n")

    # Validation steps
    if not isinstance(value, str) or len(value) > max_length:
        return False
    if unsafe_chars.intersection(value):
        return False

    # Scheme check
    scheme = value.split("://")[0].lower()
    if scheme not in schemes:
        return False

    # URL format check
    try:
        splitted_url = urlsplit(value)
    except ValueError:
        return False

    if not url_regex.match(value):
        # Handle potential IDN domain
        scheme, netloc, path, query, fragment = splitted_url
        try:
            netloc = punycode(netloc)
        except UnicodeError:
            return False

        url = urlunsplit((scheme, netloc, path, query, fragment))
        if not url_regex.match(url):
            return False

    # Проверка домена
    if splitted_url.hostname != "vk.com":
        return False

    # IPv6 check
    host_match = re.search(r"^\[(.+)\](?::[0-9]{1,5})?$", splitted_url.netloc)
    if host_match:
        potential_ip = host_match[1]
        validate_ipv6_address(potential_ip)

    return True


