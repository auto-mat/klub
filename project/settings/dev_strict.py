from .dev import *  # noqa


class InvalidStringError(str):
    def __mod__(self, other):
        raise Exception("empty string %s" % other)
        return "!!!!!empty string %s!!!!!" % other


TEMPLATES[0]['OPTIONS']['string_if_invalid'] = InvalidStringError("%s")  # noqa
