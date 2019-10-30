#! env python3
from typing import (Text, )


def quote_attr(src: Text) -> Text:  # {{{1
    ret = ""
    for ch in src:
        _v = ch.encode('ascii', 'xmlcharrefreplace')
        v = Text(_v)
        v = v[2:-1]  # remove "b'" and "'"
        if v.startswith("&#") and v.endswith(";"):
            v = v[2:-1]
            n = int(v)
            v = "&#x{:x};".format(n)
        ret += v
    return ret

# vi: ft=python:et:ts=4:sw=4:tw=80:fdm=marker
