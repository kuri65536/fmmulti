#! env python3
from argparse import ArgumentParser
from enum import Enum
import logging
from logging import debug as debg
import tempfile
import os
import sys
from typing import (Dict, List, Optional, Text, Tuple, )
from xml.parsers.expat import ParserCreate  # type: ignore
from zipfile import ZipFile

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
        arg.add_argument("-m", "--mode", choices=runmode.choices(),
                         default=Text(runmode.normal))
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
            return ret
        if len(src) < 1:
            src = ret.fname_xml
        if len(src) < 1:
            ret.fname_out = "/dev/stdout"
        else:
            p = os.path.dirname(src)
            src = os.path.basename(src)
            src, ext = os.path.splitext(src)
            ret.fname_out = os.path.join(p, src + "-1.mm")
        return ret


class Node(object):  # {{{1
    def __init__(self, name: Text, attrs: Dict[Text, Text]) -> None:  # {{{1
        self.name = name
        self.attr = attrs
        self.children: List['Node'] = []

    key_attr_mode = runmode.through

    def compose(self) -> Text:  # {{{1
        ret = "<" + self.name
        for k, v in self.attr.items():
            a = self.quote_attr(v)
            ret += ' {}="{}"'.format(k, a)
        if self.name == "map":  # TODO(shimoda): dirty hack...
            return ret + ">"
        ret += "/>"
        return ret

    @classmethod  # quote_attr
    def quote_attr(cls, src: Text) -> Text:  # {{{1
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

    def flattern(self, exclude_self: bool) -> List['Node']:  # {{{1
        ret = [self]
        if exclude_self:
            ret.clear()
        for i in self.children:
            ret.extend(i.flattern(False))
        return ret

    @classmethod  # key_attr {{{1
    def key_attr(cls, a: 'Node') -> int:
        N = 8
        lv = a.level(cls.key_attr_mode) + (0, ) * N
        ret = 0
        for i in range(N):
            ret = ret * 1000 + lv[i]
        return ret

    def level(self, mode: runmode) -> Tuple[int, ...]:  # {{{1
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
        seq = src.split("-")
        ret = tuple(int(i) for i in seq)
        return ret


class Chars(Node):  # {{{1
    def __init__(self, data: Text) -> None:  # {{{1
        Node.__init__(self, "__chars__", {})
        self.data = data

    def compose(self) -> Text:
        return self.data


class Comment(Chars):  # {{{1
    def compose(self) -> Text:  # {{{1
        return "<!--" + self.data + "-->"


class LNode(Node):  # {{{1
    def __init__(self, name: Text) -> None:  # {{{1
        Node.__init__(self, name, {})

    def compose(self) -> Text:
        return "</" + self.name + ">"


class FMNode(Node):  # {{{1
    def __init__(self, attrs: Dict[Text, Text]) -> None:  # {{{1
        Node.__init__(self, "node", attrs)
        self.parent: Optional[FMNode] = None
        self.text = attrs.get("TEXT", "")
        self.id_string = attrs.get("ID", "ID_0")
        self.position = attrs.get("POSITION", "")
        self.ts_create = int(attrs.get("CREATED", "-1"))
        self.ts_modify = int(attrs.get("MODIFIED", "-1"))

    def compose(self) -> Text:  # {{{1
        debg("compose:node:" + self.id_string)
        ret = '<node CREATED="{}" ID="{}" MODIFIED="{}"'.format(
                self.ts_create, self.id_string, self.ts_modify)
        if self.position:
            ret += ' POSITION="{}"'.format(self.position)
        ret += ' TEXT="{}"'.format(self.quote_attr(self.text))
        if len(self.children) < 1:
            ret += "/>"
        else:
            ret += ">"
            for nod in self.children:
                ret += nod.compose()
            ret += '</node>'
        return ret


class FMXml(object):  # {{{1
    def __init__(self) -> None:  # {{{1
        self.cur = self.root = FMNode({})

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
        nod = Node(name, attrs)
        self.cur.children.append(nod)

    def leave_tag(self, name: Text) -> None:  # {{{1
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
        nod = Chars(data)
        self.cur.children.append(nod)

    def enter_comment(self, data: Text) -> None:  # {{{1
        nod = Comment(data)
        self.cur.children.append(nod)

    @classmethod  # compose_tag {{{1
    def compose_tag(cls, name: Text, attrs: Dict[Text, Text]) -> Text:
        attr = ""
        for k, v in attrs.items():
            attr += ' {}="{}"'.format(k, v)
        ret = "<{}{}>".format(name, attr)
        return ret

    @classmethod  # compose_ltag {{{1
    def compose_ltag(cls, name: Text) -> Text:
        ret = "</{}>".format(name)
        return ret

    def output(self, fname: Text, mode: runmode) -> int:  # {{{1
        debg("out:open:" + fname)
        if mode == runmode.through:
            seq = self.root.children
        else:
            seq = self.restruct(mode)
        with open(fname, "wt") as fp:
            for node in seq:
                text = node.compose()
                debg("out:" + text)
                fp.write(text)
        return 0

    def restruct(self, mode: runmode) -> List[Node]:  # {{{1
        Node.key_attr_mode = mode
        debg("rest:mode={}-{}".format(mode, len(self.root.children)))
        ret: List[Node] = []
        for node in self.root.children:
            if not isinstance(node, FMNode):
                ret.append(node)
                continue
            seq_flat = node.flattern(exclude_self=True)
            debg("rest:flat:{}".format(len(seq_flat)))
            # TODO(shimoda): consider nodes of the except FMNode.
            seq_flat.sort(key=Node.key_attr)
            for i in seq_flat:
                debg("rest:sort:{}".format(i.name))
            root = self.restruct_hier(seq_flat, mode)
            ret.append(root)
        return ret

    def restruct_hier(self, seq: List[Node], mode: runmode  # {{{1
                      ) -> FMNode:
        root = FMNode({})
        non: List[Node] = []
        for node in seq:
            levels = node.level(mode)
            if len(levels) < 1:
                non.append(node)
                continue
            debg("hier:{}".format(Text(levels)))
            self.restruct_insert(root.children, mode, levels, node, 0)
        root.children.insert(0, Chars("\n"))
        root.children.extend(non)
        return root

    def restruct_insert(self, seq: List[Node], mode: runmode,  # {{{1
                        levels: Tuple[int, ...],
                        add: Node, depth: int) -> int:
        """1, 2, 2-1, 3-1, 4, 5, 6-1, 7
        """
        if depth > 7:
            return 1  # stopper of recursive calls.
        f = 0
        lv_add = levels[depth]
        for n, node in enumerate(seq):
            lvs = node.level(mode)
            lv_cur = lvs[depth]
            if lv_cur < lv_add:
                continue
            if lv_cur > lv_add:
                f = n - 1
                break
            if depth + 1 >= len(levels):  # failed to sort?
                return -1
            if len(node.children) < 1:
                f = n
                break
            f = self.restruct_insert(node.children, mode, levels,
                                     add, depth + 1)
            assert f != 0  # failed to append...????
            return f
        if f > 0:
            seq.insert(f, add)
            return f + 1
        seq.append(add)
        return len(seq) - 1


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
