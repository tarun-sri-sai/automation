from validators import url


def is_url(text):
    return bool(url(text))
