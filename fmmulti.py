#! env python3
'''
Copyright (c) 2019, shimoda as kuri65536 _dot_ hot mail _dot_ com
                    ( email address: convert _dot_ to . and joint string )

This Source Code Form is subject to the terms of the Mozilla Public License,
v.2.0. If a copy of the MPL was not distributed with this file,
You can obtain one at https://mozilla.org/MPL/2.0/.
'''
from argparse import ArgumentParser
from enum import Enum
import logging
from logging import debug as debg, warning as warn
import tempfile
import sys
from typing import (Dict, List, Optional, Text, Tuple, )
from xml.parsers.expat import ParserCreate  # type: ignore
from zipfile import ZipFile

import common as cmn
from common import Chars, HierBuilder, Node as Nod1, NodeDmy, NodeNote

Optional


class runmode(Enum):  # {{{1
    # {{{1
    through = 0
    normal = 1
    doc = 2
    test = 3

    def t(self) -> Text:  # {{{1
        t = Text(self)
        t = t.replace("runmode.", "")
        return t

    @classmethod  # choices {{{1
    def choices(cls) -> List[Text]:
        ret = []
        for i in runmode:
            t = i.t()
            ret.append(t)
        return ret

    @classmethod  # parse {{{1
    def parse(cls, src: Text) -> 'runmode':
        for i in runmode:
            if src == i.t():
                return i
        raise KeyError("'{}' is not a mode in {}".format(src, cls.choices()))


class options(object):  # {{{1
    def __init__(self) -> None:  # {{{1
        self.fname_xml = ""
        self.fname_zip = ""
        self.fname_out = ""
        self.mode = runmode.normal

    @classmethod  # parser {{{1
    def parser(cls) -> ArgumentParser:  # {{{1
        arg = ArgumentParser()
        arg.add_argument("-o", "--output", default="")
        arg.add_argument("-f", "--override", action="store_true")
        arg.add_argument("-m", "--mode", choices=runmode.choices(),
                         default=runmode.normal.t())
        arg.add_argument("-i", "--input-xml", default="")
        arg.add_argument("input_zip_name", type=Text, nargs="?")
        return arg

    @classmethod  # parse {{{1
    def parse(cls, args: List[Text]) -> 'options':
        logging.basicConfig(level=logging.DEBUG)
        ret = options()
        opts = ret.parser().parse_args(args)
        ret.fname_out = opts.output
        ret.fname_xml = opts.input_xml
        ret.mode = runmode.parse(opts.mode)
        src = ret.fname_zip = opts.input_zip_name
        if not isinstance(src, Text):
            src = ""
        if len(ret.fname_out) > 0:
            src = ret.fname_out
            ret.fname_out = cmn.number_output(opts.override, src, ".mm")
            return ret
        if len(src) < 1:
            src = ret.fname_xml
        if len(src) < 1:
            ret.fname_out = "/dev/stdout"
        else:
            ret.fname_out = cmn.number_output(opts.override, src, ".mm")
        return ret


class Node(Nod1):  # {{{1
    def copy(self, include_children: bool=False) -> Nod1:  # {{{1
        ret = Node(self.name, self.attr)
        if include_children:
            ret.children = self.children + []
        return ret

    key_attr_mode = runmode.through

    def flattern(self, exclude_self: bool) -> List[Nod1]:  # {{{1
        dmy = self.copy()
        ret = [dmy]
        if exclude_self:
            ret.clear()
        for i in self.children:
            if not isinstance(i, FMNode):
                dmy.children.append(i)
                continue
            ret.extend(i.flattern(exclude_self=False))
        Node.rtrim_enter(dmy.children)
        warn("flat:{}-{}".format(dmy, len(ret)))
        return ret

    @classmethod  # key_attr {{{1
    def key_attr(cls, a: Nod1) -> int:
        # TODO(kuriyama): from section_num_to_int
        N, U = 8, 100000
        ret = 0
        if False:  # special case...
            pass
        else:
            lv = cls.level(a, cls.key_attr_mode) + (0, ) * N
            ret = 0
            for i in range(N):
                ret = ret * U + lv[i]
        warn("nod'{:20}'-lv{:42d}".format(Text(a), ret))
        return ret

    @classmethod  # level {{{1
    def level(cls, self: Nod1, mode: runmode) -> Tuple[int, ...]:
        t = mode.t()
        src = ""
        for node in self.children:
            if node.name != "attribute":
                continue
            src = node.attr.get("NAME", "")
            if src != t:
                continue
            src = node.attr.get("VALUE", "")
            break
        else:
            return ()
        if src == "root":
            return (-1, )
        src = src.replace(",", "-")  # allow ',' and '-' to splitter.
        seq = src.split("-")
        ret = tuple(cmn.section_num_to_int(i) for i in seq)
        return ret

    @classmethod  # is_enter {{{1
    def is_enter(cls, self: Nod1) -> bool:
        if not isinstance(self, Chars):
            return False
        if self.data != "\n":
            return False
        return True

    @classmethod  # insert_enter {{{1
    def insert_enter(cls, seq: List[Nod1], n: int) -> None:
        if len(seq) < 1 or n == -1:
            seq.append(Chars("\n"))
            return
        if n >= len(seq):
            n = -1
        if n < 0:
            n = len(seq) + n
            assert n >= 0, "%d" % n
        node = seq[n]
        if cls.is_enter(node):
            return
        seq.insert(n, Chars("\n"))

    @classmethod  # rtrim_enter {{{1
    def rtrim_enter(cls, seq: List[Nod1]) -> None:
        n = 0
        rev = seq + []
        rev.reverse()
        for i in rev:
            if not cls.is_enter(i):
                break
            n += 1
        if n == 0:
            seq.append(Chars('\n'))
            return
        if n == 1:
            return
        for j in range(n - 1):
            del seq[-1]

    def level_diff(self, b: Nod1) -> int:  # {{{1
        if not isinstance(b, Node):
            return 0

        def lvl(a: 'Node') -> int:
            ret = len(self.level(a, self.key_attr_mode))
            ret -= 1
            ret = 0 if ret < 0 else ret
            return 100 * ret

        lvl_a = lvl(self)
        lvl_b = lvl(b)
        ret = round((lvl_a - lvl_b) / 100)
        warn("nod2:diff:{}-{}-{}".format(ret, self, b))
        return ret


class Comment(Chars):  # {{{1
    def compose(self, prv: Nod1) -> Text:  # {{{1
        return "<!--" + self.data + "-->"


class LNode(Node):  # {{{1
    def __init__(self, name: Text) -> None:  # {{{1
        Node.__init__(self, "leave - " + name, {})

    def compose(self, prv: Nod1) -> Text:
        return "</" + self.name.replace("leave - ", "") + ">"


class FMNode(Node):  # {{{1
    def __init__(self, attrs: Dict[Text, Text]) -> None:  # {{{1
        Node.__init__(self, "node", attrs)
        self.parent: Optional[FMNode] = None
        self.text = attrs.get("TEXT", "")
        self.id_string = attrs.get("ID", "ID_0")
        self.position = attrs.get("POSITION", "")
        self.ts_create = int(attrs.get("CREATED", "-1"))
        self.ts_modify = int(attrs.get("MODIFIED", "-1"))

    def copy(self, include_children: bool=False) -> 'FMNode':  # {{{1
        ret = FMNode({
            "CREATED": "{}".format(self.ts_create),
            "MODIFIED": "{}".format(self.ts_modify),
            "ID": self.id_string,
            "TEXT": self.text,
            "POSITION": self.position})
        if include_children:
            ret.children = ret.children + []
        return ret

    def compose(self, prv: Nod1) -> Text:  # {{{1
        debg("compose:node:" + self.id_string)
        ret = '<node CREATED="{}" ID="{}" MODIFIED="{}"'.format(
                self.ts_create, self.id_string, self.ts_modify)
        if self.position:
            ret += ' POSITION="{}"'.format(self.position)
        ret += ' TEXT="{}"'.format(cmn.quote_attr(self.text))
        if len(self.children) < 1:
            ret += "/>\n"
        else:
            ret += ">"
            prv_child: Nod1 = NodeDmy()
            for nod in self.children:
                ret += nod.compose(prv_child)
                prv_child = nod
            ret += '</node>\n'
        return ret

    def level_flat(self) -> bool:  # {{{1
        return False


class FMXml(object):  # {{{1
    def __init__(self) -> None:  # {{{1
        self.cur = self.root = FMNode({})
        self.cur_rich: Optional[NodeNote] = None

    @classmethod  # parse {{{1
    def parse(cls, fname: Text) -> 'FMXml':
        """parse Nodes from xml.
        """
        ret = FMXml()
        parser = ParserCreate()
        parser.StartElementHandler = ret.enter_tag
        parser.EndElementHandler = ret.leave_tag
        parser.CharacterDataHandler = ret.enter_chars
        parser.CommentHandler = ret.enter_comment
        with open(fname, "rb") as fp:
            parser.ParseFile(fp)
        return ret

    def enter_tag(self, name: Text, attrs: Dict[Text, Text]) -> None:  # {{{1
        if name == "node":
            self.f_header = False
            node = FMNode(attrs)
            node.parent = self.cur
            self.cur.children.append(node)
            self.cur = node
            debg("new node:" + node.id_string)
            return
        if self.cur_rich is not None:
            self.cur_rich.enter_tag(name, attrs)
            return
        elif name != "richcontent":
            nod: Nod1 = Node(name, attrs)
        else:
            nod = self.cur_rich = NodeNote("")
        self.cur.children.append(nod)

    def leave_tag(self, name: Text) -> None:  # {{{1
        if self.cur_rich is not None:
            if name == "richcontent":
                self.cur_rich = None
            else:
                self.cur_rich.leave_tag(name)
            return
        if name == "node":
            assert self.cur.parent is not None
            debg("cls node:" + self.cur.id_string)
            self.cur = self.cur.parent
            return
        nod = self.cur.children[-1]
        if nod.name == name:
            return
        nod = LNode(name)
        self.cur.children.append(nod)

    def enter_chars(self, data: Text) -> None:  # {{{1
        if self.cur_rich is not None:
            self.cur_rich.chars(data)
            return
        nod = Chars(data)
        self.cur.children.append(nod)

    def enter_comment(self, data: Text) -> None:  # {{{1
        if self.cur_rich is not None:
            self.cur_rich.note += "<!--" + data + "-->"
            return
        nod = Comment(data)
        self.cur.children.append(nod)

    def output(self, fname: Text, mode: runmode) -> int:  # {{{1
        debg("out:open:" + fname)
        if mode == runmode.through:
            seq = self.root.children
        else:
            seq = self.restruct(mode)
        with open(fname, "wt") as fp:
            prv: Nod1 = NodeDmy()
            for node in seq:
                text = node.compose(prv)
                debg("out:" + text)
                fp.write(text)
                prv = node
        return 0

    def restruct(self, mode: runmode) -> List[Nod1]:  # {{{1
        Node.key_attr_mode = mode
        debg("rest:mode={}-{}".format(mode, len(self.root.children)))
        ret: List[Nod1] = []
        for node in self.root.children:
            if not isinstance(node, FMNode):
                warn("rest:ignored-node={}".format(node.name))
                # ret.append(node)
                continue
            seq_flat = node.flattern(exclude_self=False)
            debg("rest:flat:{}".format(len(seq_flat)))
            for i in seq_flat:
                debg("rest:sort:{}".format(i.name))
            ret.extend(seq_flat)
        ret.sort(key=Node.key_attr)
        ret = HierBuilder().restruct(ret)

        # insert header and footer
        ret.insert(0, Chars("\n"))
        ret.insert(0, Nod1("node", {"TEXT": mode.t()}).enter_only(True))
        ret.insert(0, Chars("\n" + cmn.cmt_header + "\n"))
        ret.insert(0, Nod1("map", {"version": "1.1.0"}).enter_only(True))
        # ret.append(Chars("\n"))  # don't need, see Node.compose()
        ret.append(LNode("node"))
        ret.append(Chars("\n"))
        ret.append(LNode("map"))
        debg("rest:ret={}".format(len(ret)))
        return ret


def zip_extract(fname: Text) -> Text:  # {{{1
    ret = tempfile.mktemp(".xml", "fmmulti", dir=".")
    try:
        debg("zip:" + fname)
        zf = ZipFile(fname)
    except Exception as ex:
        debg("zip:" + fname + "->" + Text(ex))
        return ""

    try:
        for zi in zf.infolist():
            debg("found entry {}".format(zi))
            if zi.is_dir():  # type: ignore  # no `is_dir` in python2
                continue
            with open(ret, "w") as fp:
                fp.write(zf.extract(zi))
            return ret
    finally:
        zf.close()
    return ""


def main(args: List[Text]) -> int:  # {{{1
    opts = options.parse(args)
    if opts.fname_zip:
        opts.fname_xml = zip_extract(opts.fname_zip)
    if len(opts.fname_xml) < 1:
        options.parser().print_help()
        return 1
    xml = FMXml.parse(opts.fname_xml)
    return xml.output(opts.fname_out, opts.mode)


if __name__ == "__main__":  # {{{1
    sys.exit(main(sys.argv[1:]))
# vi: ft=python:et:ts=4:sw=4:tw=80:fdm=marker
