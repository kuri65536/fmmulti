#! env python3
from typing import (Dict, List, Text, )
from xml.sax.saxutils import escape as quote_xml

List
quote_xml


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
