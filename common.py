#! env python3
'''
Copyright (c) 2019, shimoda as kuri65536 _dot_ hot mail _dot_ com
                    ( email address: convert _dot_ to . and joint string )

This Source Code Form is subject to the terms of the Mozilla Public License,
v.2.0. If a copy of the MPL was not distributed with this file,
You can obtain one at https://mozilla.org/MPL/2.0/.
'''
import os
from typing import (Dict, List, Text, )
from xml.sax.saxutils import escape as quote_xml

List
quote_xml


def number_output(f_override: bool, src: Text, sfx: Text) -> Text:  # {{{1
    p = os.path.dirname(src)
    src = os.path.basename(src)
    src, ext = os.path.splitext(src)

    def fn(i: int) -> Text:
        s = (("-%d" % i) if i > 0 else "") + sfx
        return os.path.join(p, src + s)  # type: ignore

    n = 0
    ret = fn(n)
    if f_override:
        return ret
    while os.path.exists(ret):
        n += 1
        ret = fn(n)
    return ret


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
    ret = ret.replace("<", "&gt;")
    ret = ret.replace(">", "&lt;")
    return ret


class Node(object):  # {{{1
    def __init__(self, name: Text, attr: Dict[Text, Text]) -> None:  # {{{1
        self.name = name
        self.attr = attr
        self.children: List['Node'] = []

    def compos2(self) -> Text:  # {{{1
        ret = "<" + self.name
        for k, v in self.attr.items():
            a = quote_attr(v)
            ret += ' {}="{}"'.format(k, a)
        return ret

    def compose(self) -> Text:  # {{{1
        ret = self.compos2()
        if self.name == "map":  # TODO(shimoda): dirty hack...
            return ret + ">"
        ret += "/>\n"
        return ret


class NodeNote(Node):  # {{{1
    def __init__(self, note: Text) -> None:  # {{{1
        self.name = "richcontent"
        self.note = note
        self.f_data = False

    def compose(self) -> Text:  # {{{1
        rt1 = ('<richcontent TYPE="NOTE"><html>\n  <head>\n  </head>\n'
               "  <body>\n"
               "    <p>\n"
               "      <pre>\n")
        rt2 = ("      </pre>\n"
               "    </p>\n"
               "  </body>\n"
               "</html></richcontent>\n")
        ret = rt1 + quote_xml(self.note) + rt2
        return ret

    def enter_tag(self, name: Text, attr: Dict[Text, Text]) -> None:  # {{{1
        if name in ("html", "head", "body", "p"):
            return
        if name == "pre":
            self.f_data = True  # TODO(shimoda): dirty...
            return
        nod = Node(name, attr)
        self.note += nod.compos2() + ">"

    def leave_tag(self, name: Text) -> None:  # {{{1
        if name in ("html", "head", "body", "p"):
            return
        if name == "pre":
            self.f_data = False  # TODO(shimdoa): dirty...
            return
        self.note += "</" + name + ">"

    def chars(self, data: Text) -> None:  # {{{1
        if self.f_data:
            self.note += data

# vi: ft=python:et:ts=4:sw=4:tw=80:fdm=marker
