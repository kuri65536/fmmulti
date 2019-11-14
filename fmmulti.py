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
    doc = 1
    test = 2
    backup = 3

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
        self.mode = runmode.through
        self.n_output_markdown = False
        self.f_disable_script = False

    @classmethod  # parser {{{1
    def parser(cls) -> ArgumentParser:  # {{{1
        arg = ArgumentParser()
        arg.add_argument("-o", "--output", default="")
        arg.add_argument("-B", "--remove-backup", action="store_true")
        arg.add_argument("-c", "--convert-backup", default="")
        arg.add_argument("-S", "--disable-script", action="store_true")
        arg.add_argument("-M", "--output-markdown", type=int, default=-1)
        arg.add_argument("-f", "--override", action="store_true")
        arg.add_argument("-m", "--mode", choices=runmode.choices(),
                         default=runmode.through.t())
        arg.add_argument("-z", "--input-zip-name", default="")
        arg.add_argument("input_xml", type=Text, nargs="?")
        return arg

    @classmethod  # parse {{{1
    def parse(cls, args: List[Text]) -> 'options':
        logging.basicConfig(level=logging.DEBUG)
        ret = options()
        opts = ret.parser().parse_args(args)
        ret.fname_out = opts.output
        ret.fname_xml = opts.input_xml
        ret.mode = runmode.parse(opts.mode)
        ret.n_output_markdown = opts.output_markdown
        ret.f_disable_script = opts.disable_script
        FMNode.f_no_backup = opts.remove_backup
        FMNode.convert_backup = opts.convert_backup
        src = ret.fname_zip = opts.input_zip_name
        if not isinstance(src, Text):
            src = ""
        sfx = ".mm" if not (ret.n_output_markdown >= 0) else ".md"
        if len(ret.fname_out) > 0:
            src = ret.fname_out
            ret.fname_out = cmn.number_output(opts.override, src, sfx)
            return ret
        if len(src) < 1:
            src = ret.fname_xml
        if len(src) < 1:
            ret.fname_out = "/dev/stdout"
        else:
            ret.fname_out = cmn.number_output(opts.override, src, sfx)
        return ret


class Node(Nod1):  # {{{1
    # {{{1
    convert_backup = ""

    def copy(self, include_children: bool=False) -> Nod1:  # {{{1
        ret = Node(self.name, self.attr)
        if include_children:
            ret.children = self.children + []
        return ret

    key_attr_mode = runmode.through

    def flattern(self, sec: Text, exclude_self: bool) -> List[Nod1]:  # {{{1
        dmy = self.copy()
        n, ret = 1, [dmy]
        if exclude_self:
            ret.clear()
        for i in self.children:
            if not isinstance(i, FMNode):
                dmy.children.append(i)
                continue
            n, sec0 = n + 1, (sec + "-" + Text(n)).lstrip("-")
            ret.extend(i.flattern(sec0, exclude_self=False))
        Node.rtrim_enter(dmy.children)
        if self.key_attr_mode != runmode.backup:
            dmy.attr_replace("backup", sec if sec != "" else "root")
        if Node.convert_backup:
            dmy.attr_change_name(runmode.backup.t(), Node.convert_backup)
        warn("flat:{}-{}".format(dmy, len(ret)))
        return ret

    @classmethod  # key_attr {{{1
    def key_attr(cls, a: Nod1) -> int:
        # TODO(kuriyama): from section_num_to_int
        N, U = cmn.lvl_cls, cmn.lvl_max + 1
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
            return (cmn.lvl_max, )
        if src == "root":
            return cmn.lvl_root
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
        if b.name == "root":
            return 1
        if not isinstance(b, Node):
            return 0

        def lvl(a: 'Node') -> int:
            ret = len(self.level(a, self.key_attr_mode))
            ret += 1
            ret = 0 if ret < 0 else ret
            return 100 * ret

        lvl_a = lvl(self)
        lvl_b = lvl(b)
        ret = round((lvl_a - lvl_b) / 100)
        warn("nod2:diff:{}-{}-{}".format(ret, self, b))
        return ret


class Comment(Nod1):  # {{{1
    def __init__(self, data: Text) -> None:  # {{{1
        Node.__init__(self, "__comment__", {})
        self.data = data

    def compose(self, prv: Nod1) -> Text:  # {{{1
        return "<!--" + self.data + "-->"


class LNode(Node):  # {{{1
    def __init__(self, name: Text) -> None:  # {{{1
        Node.__init__(self, "leave - " + name, {})

    def compose(self, prv: Nod1) -> Text:  # {{{1
        return "</" + self.name.replace("leave - ", "") + ">"


class FMNode(Node):  # {{{1
    # {{{1
    f_no_backup = False

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
                if self.f_no_backup and (nod.name == "attribute" and
                                         nod.attr["NAME"] == "backup"):
                    continue
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
        self.n_output_markdown = -1
        self.f_disable_script = False

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
        elif name == "map":  # TODO(shimoda): dirty, change parse procedures.
            nod: Nod1 = Node(name, attrs)
            nod.f_enter_only = True
        elif name != "richcontent":
            nod = Node(name, attrs)
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
        seq = self.cur.children
        if len(seq) > 0 and isinstance(seq[-1], FMNode):
            if len(data.strip()) < 1:
                return  # ignore white-spaces.
        nod = Chars(data)
        self.cur.children.append(nod)

    def enter_comment(self, data: Text) -> None:  # {{{1
        if self.cur_rich is not None:
            self.cur_rich.chars("<!--" + data + "-->")
            return
        nod = Comment(data)
        self.cur.children.append(nod)

    def output(self, fname: Text, mode: runmode) -> int:  # {{{1
        debg("out:open:" + fname)
        if mode == runmode.through:
            seq = self.root.children
            HierBuilder().mark_backup(seq, "root")
        else:
            seq = self.restruct(mode)
        if self.n_output_markdown >= 0:
            with open(fname, "wt") as fp:
                fp.write("")
            return self.output_markdown(fname, seq, self.n_output_markdown)
        with open(fname, "wt") as fp:
            prv: Nod1 = NodeDmy()
            for node in seq:
                text = node.compose(prv)
                debg("out:" + text)
                fp.write(text)
                prv = node
        return 0

    def output_markdown(self, fname: Text, seq: List[Nod1],  # {{{1
                        depth: int) -> int:
        def out_node(nod: Nod1, f: bool) -> bool:
            with open(fname, "at") as fp:
                if nod.name == "node":
                    title = ("#" * depth) + " " + nod.attr.get("TEXT", "")
                    fp.write("\n" + title + "\n")
                elif nod.name == "__chars__":
                    assert isinstance(nod, Chars)
                    if not f:
                        fp.write(nod.data)
                    elif len(nod.data.strip()) > 0:
                        fp.write(nod.data)
                elif nod.name == "__comment__":
                    assert isinstance(nod, Comment)
                    fp.write("<!--" + nod.data + "-->")
                elif nod.name == "richcontent":
                    assert isinstance(nod, NodeNote)
                    fp.write(cmn.unquote_note(nod.note))
                elif nod.name == "attribute":
                    fp.write("<!-- attr: {} = {} -->".format(
                            nod.attr.get("NAME", "name?"),
                            nod.attr.get("VALUE", "val?")))
                elif nod.name in ("map", "leave - map", "font", ):
                    return True
                else:
                    assert False
            return False

        f = True
        for node in seq:
            f = out_node(node, f)
            self.output_markdown(fname, node.children, depth + 1)
            if node.name == "node":
                out_node(Chars("\n"), False)
        return 0

    def restruct(self, mode: runmode) -> List[Nod1]:  # {{{1
        Node.key_attr_mode = mode
        debg("rest:mode={}-{}".format(mode, len(self.root.children)))
        n = 0
        ret: List[Nod1] = []
        for node in self.root.children:
            if not isinstance(node, FMNode):
                warn("rest:ignored-node={}".format(node.name))
                # ret.append(node)
                continue
            n += 1
            seq_flat = node.flattern("", exclude_self=False)
            debg("rest:flat:{}".format(len(seq_flat)))
            for i in seq_flat:
                debg("rest:sort:{}".format(i.name))
            ret.extend(seq_flat)
        ret = self.restruct_dup_root(ret, mode)
        ret.sort(key=Node.key_attr)
        ret = HierBuilder().restruct(ret)

        # insert header and footer
        if len(ret) < 1 or Node.level(ret[0], mode) != cmn.lvl_root:
            ret.insert(0, Chars("\n"))
            ret.insert(0, Nod1("node", {"TEXT": mode.t()}).enter_only(True))
            ret.append(LNode("node"))
        ret.insert(0, Chars("\n" + cmn.cmt_header + "\n"))
        ret.insert(0, Nod1("map", {"version": "1.1.0"}).enter_only(True))
        # ret.append(Chars("\n"))  # don't need, see Node.compose()
        ret.append(Chars("\n"))
        ret.append(LNode("map"))
        debg("rest:ret={}".format(len(ret)))
        return ret

    def restruct_dup_root(self, seq: List[Nod1], mode: runmode  # {{{1
                          ) -> List[Nod1]:
        def append_script(nod: Nod1) -> None:
            if self.f_disable_script:
                return
            cmds = cmn.compose_script(mode.t())
            nod.attr_replace("script1", cmds)

        seq_root: List[Nod1] = []
        for i in seq:
            if Node.level(i, mode) == cmn.lvl_root:
                seq_root.append(i)
            v = i.attr_get(mode.t(), "")
        if len(seq_root) < 2:
            if len(seq_root) > 0:
                append_script(seq_root[0])
            return seq

        f = False
        seq_rot2: List[Nod1] = []
        for i in seq_root:
            v = i.attr_get(mode.t(), "")
            if f:
                pass
            elif v != mode.t() and mode.t() in v:
                pass
            else:
                f = True
                append_script(i)
                continue
            seq_rot2.append(i)
        if len(seq_rot2) < 1:
            seq_rot2 = seq_root[:-1]

        for i in seq_rot2:
            i.attr_replace(mode.t(), "99")
        return seq


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
    xml.n_output_markdown = opts.n_output_markdown
    xml.f_disable_script = opts.f_disable_script
    return xml.output(opts.fname_out, opts.mode)


if __name__ == "__main__":  # {{{1
    sys.exit(main(sys.argv[1:]))
# vi: ft=python:et:ts=4:sw=4:tw=80:fdm=marker
