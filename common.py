#! env python3
'''
Copyright (c) 2019, shimoda as kuri65536 _dot_ hot mail _dot_ com
                    ( email address: convert _dot_ to . and joint string )

This Source Code Form is subject to the terms of the Mozilla Public License,
v.2.0. If a copy of the MPL was not distributed with this file,
You can obtain one at https://mozilla.org/MPL/2.0/.
'''
import os
from logging import warning as warn, debug as debg
from typing import (Dict, List, Optional, Text, )
from xml.sax.saxutils import escape as quote_xml

List, Optional
warn
quote_xml

ch_splitter = "-"
sub_digit = [chr(i) for i in range(ord("a"), ord("z") + 1)]

cmt_header = ("<!-- To view this file, download free mind mapping software "
              "FreeMind from http://freemind.sourceforge.net -->")


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


def section_num_1st(num: Text) -> Text:
    num = num + ch_splitter + "0" + sub_digit[0]
    num = num.lstrip(ch_splitter)
    return num


def section_num_to_int(num: Text) -> int:  # {{{1
    dgt = num.rstrip("".join(sub_digit))
    alp = num.replace(dgt, "")
    ret = int(dgt) * 1000
    ret += section_num_conv(alp)
    return ret


def section_num_conv(num: Text) -> int:  # {{{1
    n, f, N = 0, 1, len(sub_digit)
    for ch in num:
        n = n * N + (sub_digit.index(ch) + f)
        f = 1
    return n


def section_num_recv(n: int) -> Text:  # {{{1
    if n < 1:
        return sub_digit[0]
    n, lst, N = n, "", len(sub_digit)
    while True:
        n -= 1
        i = int(n % N)
        lst = sub_digit[i] + lst
        n = int(n / N)
        # warn("num1:{}-{}".format(i, n))
        if n < 1:
            break
    # warn("num2:{}".format(n - 1))
    return lst


def section_num_incr_desc(num: Text) -> Text:  # {{{1
    if len(num) < 1:
        return sub_digit[0]
    spl = ch_splitter
    seq = num.split(spl)
    lst = seq[-1]
    if lst.isdigit():
        return spl.join(seq[:-1] + [lst + sub_digit[0]])
    hed = lst.rstrip("".join(sub_digit))
    lst = lst.lstrip(hed)
    n = section_num_conv(lst)
    n += 1
    lst = section_num_recv(n)
    ret = spl.join(seq[:-1] + [hed + lst])
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
        self.parent: Optional['Node'] = None
        self.f_enter_only = False

    def __repr__(self) -> Text:  # for debug {{{1
        par = self.parent.name if self.parent is not None else "None"
        return "{}-{}-{}".format(self.name, len(self.children), par)

    def compos2(self) -> Text:  # {{{1
        ret = "<" + self.name
        for k, v in self.attr.items():
            a = quote_attr(v)
            ret += ' {}="{}"'.format(k, a)
        return ret

    def compose(self, prv: 'Node') -> Text:  # {{{1
        ret = self.compos2()
        if self.f_enter_only:
            return ret + ">"
        ret += "/>"
        return ret

    def enter_only(self, f: bool) -> 'Node':  # {{{1
        self.f_enter_only = f
        return self

    def level_flat(self) -> bool:  # {{{1
        return True

    def level_diff(self, b: 'Node') -> int:  # {{{1
        assert False

    def append(self, nod: 'Node') -> None:  # {{{1
        if self.name == "root":  # root will not have level_diff()
            dif = 0
        else:
            dif = self.level_diff(nod)
        debg("append: {}".format(dif))
        # nod_dummy, n = self, self.n_level
        nod_dummy = self
        for i in range(dif - 1):
            # n += n_level_unit
            nod_dummy_child = Node("### dummy paragraph ###", {})
            nod_dummy.children.append(nod_dummy_child)
            nod_dummy_child.parent = nod_dummy
            nod_dummy = nod_dummy_child
        nod_dummy.children.append(nod)
        nod.parent = nod_dummy

    def append_to_parent(self, nod: 'Node', root: 'Node') -> None:  # {{{1
        par = self.parent if self.parent is not None else root
        par.children.append(nod)
        nod.parent = par


class NodeDmy(Node):  # {{{1
    def __init__(self) -> None:  # {{{1
        Node.__init__(self, "### dummy ###", {})

    def compose(self, prv: 'Node') -> Text:  # {{{1
        return ""


class Chars(Node):  # {{{1
    def __init__(self, data: Text) -> None:  # {{{1
        Node.__init__(self, "__chars__", {})
        self.data = data

    def compose(self, prv: 'Node') -> Text:
        return self.data


class NodeNote(Node):  # {{{1
    def __init__(self, note: Text) -> None:  # {{{1
        self.name = "richcontent"
        self.note = note
        self.f_data = False

    def compose(self, prv: 'Node') -> Text:  # {{{1
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


class HierBuilder(object):  # {{{1
    def __init__(self) -> None:  # {{{1
        self.cur = self.root = Node("root", {})

    def restruct(self, seq: List[Node]) -> List[Node]:  # {{{1
        ret: List[Node] = []
        for nod in seq:
            if nod.level_flat():
                self.cur.append_to_parent(nod, self.root)
                continue
            self.insert_node(nod)
        ret = self.root.children + []
        return ret

    def insert_node(self, nod: Node) -> None:  # {{{1
        cur = self.cur
        res = nod.level_diff(cur)
        debg("{}-{}-{}".format(res, cur, nod))
        if res == 0:
            cur.append_to_parent(nod, self.root)
        elif res < 0:  # new < cur -> drill up
            self.hier_insert_and_up(cur, nod)
        else:          # new > cur -> drill down
            cur.append(nod)
        self.cur = nod

    def hier_insert_and_up(self, cur: Node, ins: Node  # {{{1
                           ) -> None:
        par = cur
        while True:
            if par.name == "root":  # root will not have level_diff()
                break
            if par.level_diff(ins) < 0:
                break
            tmp = par.parent
            if tmp is None:  # or par.n_level < n_level_unit:
                par = self.root
                break
            par = tmp
        par.append(ins)


# end of file {{{1
# vi: ft=python:et:ts=4:sw=4:tw=80:fdm=marker
