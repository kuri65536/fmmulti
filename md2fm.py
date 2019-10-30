#! env python3
from argparse import ArgumentParser
import logging
from logging import debug as debg
import re
import os
import sys
import time
from typing import (Dict, Iterable, List, Optional, Text, )

import common as cmn

Dict, Optional


class options(object):  # {{{1
    def __init__(self) -> None:  # {{{1
        self.fname_mdn = ""
        self.fname_out = ""

    @classmethod  # parser {{{1
    def parser(cls) -> ArgumentParser:  # {{{1
        arg = ArgumentParser()
        arg.add_argument("-o", "--output", default="")
        arg.add_argument("-f", "--override", action="store_true")
        arg.add_argument("input_markdown", type=Text)
        return arg

    @classmethod  # parse {{{1
    def parse(cls, args: List[Text]) -> 'options':
        logging.basicConfig(level=logging.DEBUG)
        ret = options()
        opts = ret.parser().parse_args(args)
        ret.fname_out = opts.output
        src = ret.fname_mdn = opts.input_markdown
        if not isinstance(src, Text):
            src = ""
        if len(ret.fname_out) > 0:
            return ret
        if len(src) < 1:
            ret.fname_out = "/dev/stdout"
        else:
            ret.fname_out = cls.parse_output(opts.override, src)
        return ret

    @classmethod  # parse_output {{{1
    def parse_output(cls, f_override: bool, src: Text) -> Text:
        p = os.path.dirname(src)
        src = os.path.basename(src)
        src, ext = os.path.splitext(src)

        def fn(i: int) -> Text:
            sfx = (("-%d" % i) if i > 0 else "") + ".mm"
            return os.path.join(p, src + sfx)  # type: ignore

        n = 0
        ret = fn(n)
        if f_override:
            return ret
        while os.path.exists(ret):
            n += 1
            ret = fn(n)
        return ret


class Node(object):  # {{{1
    def __init__(self, name: Text) -> None:  # {{{1
        self.name = name
        self.attr: Dict[Text, Text] = {}
        self.children: List['Node'] = []

    def compose(self) -> Text:  # {{{1
        ret = "<" + self.name
        for k, v in self.attr.items():
            a = cmn.quote_attr(v)
            ret += ' {}="{}"'.format(k, a)
        if self.name == "map":  # TODO(shimoda): dirty hack...
            return ret + ">"
        ret += "/>\n"
        return ret


class NodeNote(Node):  # {{{1
    def __init__(self, note: Text) -> None:  # {{{1
        self.note = note

    def compose(self) -> Text:  # {{{1
        rt1 = ('<richcontent TYPE="NOTE"><html>\n  <head>\n  </head>\n'
               "  <body>\n"
               "    <p>\n"
               "      <pre>\n")
        rt2 = ("      </pre>\n"
               "    </p>\n"
               "  </body>\n"
               "</html></richcontent>\n")
        ret = rt1 + cmn.quote_xml(self.note) + rt2
        return ret


class MDNode(Node):  # {{{1
    def __init__(self, title: Text, buf: List[Text], n: int) -> None:  # {{{1
        Node.__init__(self, "section")

        title = title if not title.startswith(" ") else title[1:]

        self.parent: Optional[MDNode] = None
        self.title = title
        self.note = "\n".join(buf)
        self.n_level = n

    def compose(self) -> Text:  # {{{1
        debg("compose:node:" + Text(self.n_level))
        ret = '<node CREATED="{}" ID="{}" MODIFIED="{}"'.format(
                -1, int(time.time() * 1000), -1)
        ret += ' TEXT="{}"'.format(cmn.quote_attr(self.title))
        if len(self.note) > 0:
            node = NodeNote(self.note)
            self.children.insert(0, node)
        self.children.insert(0, self.attr_section_number())
        if len(self.children) < 1:
            ret += "/>\n"
        else:
            ret += ">\n"
            for nod in self.children:
                ret += nod.compose()
            ret += '</node>\n'
        return ret

    def attr_section_number(self) -> Node:  # {{{1
        ret = Node("attribute")
        num = self.attr_section_number_from_title()
        if len(num) < 1:
            num = self.attr_section_number_from_parent(0)
        ret.attr["NAME"] = "doc"
        ret.attr["VALUE"] = num
        return ret

    def attr_section_number_from_title(self) -> Text:  # {{{1
        mo = re.search(r"^ *[0-9-.]+ ", self.title)
        if mo is None:
            return ""
        num: Text = mo.group()
        num = num.replace(".", "-")
        num = num.strip()
        num = num.rstrip("-")
        return num

    def attr_section_number_from_parent(self, n: int) -> Text:  # {{{1
        if self.parent is None:
            seq = ("0", ) * n
            return "-".join(seq)
        num = self.parent.attr_section_number_from_title()
        if len(num) < 1:
            return self.parent.attr_section_number_from_parent(n + 1)
        return num

    def append(self, nod: 'MDNode') -> None:  # {{{1
        self.children.append(nod)
        nod.parent = self

    def append_to_parent(self, nod: 'MDNode', root: 'MDNode') -> None:  # {{{1
        par = self.parent if self.parent is not None else root
        par.children.append(nod)
        nod.parent = par


class FMXml(object):  # {{{1
    def __init__(self) -> None:  # {{{1
        self.cur = self.root = MDNode("root", [], 0)

    @classmethod  # parse {{{1
    def parse_markdown(cls, fname: Text) -> 'FMXml':
        """parse Nodes from markdown
        """
        ret, buf = FMXml(), []
        for line in cls.get_lines(fname):
            line = line.rstrip("\r\n")
            n = cls.is_section_line(line)
            if n == 0:
                buf.append(line)
                continue
            debg("found {}-{}".format(n, line.strip()))
            if len(buf) < 1:
                buf = [line]
                continue
            if n in (100, 200):  # === or ---, exclude the last line.
                bf2 = buf[:-1]
                buf = [buf[-1], line]
            else:
                bf2 = buf
                buf = [line]
            ret.parse_para(bf2)
        if len(ret.root.children) < 1:
            return ret
        ret.parse_para(buf)  # parse left data...
        return ret

    @classmethod  # get_lines {{{1
    def get_lines(cls, fname: Text) -> Iterable[Text]:
        try:
            with open(fname, "rt") as fp:
                for i in fp.readlines():
                    yield i
        except:
            pass

    @classmethod  # is_section_line {{{1
    def is_section_line(cls, line: Text) -> int:
        """- did not support '#' in \`\`\`
        """
        if len(line) < 1:
            return 0
        if line.startswith(" ") or line.startswith("\t"):
            return 0
        if len(line.lstrip("=")) < 1:
            return 100
        if len(line.lstrip("-")) < 1:
            return 200
        if not line.startswith("#"):
            return 0
        src = line.lstrip("#")
        n = len(line) - len(src)
        if n == 1:
            return 110
        if n == 2:
            return 120
        return n * 100

    def parse_para(self, buf: List[Text]) -> None:  # {{{1
        line_2nd = buf[1] if len(buf) > 1 else ""
        n = self.is_section_line(line_2nd)
        if n == 10:
            title, buf = buf[0], [] if len(buf) < 3 else buf[2:]
        elif n == 11:
            title, buf = buf[0], [] if len(buf) < 3 else buf[2:]
        else:
            n = self.is_section_line(buf[0])
            title, buf = buf[0].lstrip("#"), buf[1:]
        nod = MDNode(title, buf, n)
        cur = self.cur
        if cur.n_level == n:
            cur.append_to_parent(nod, self.root)
        elif cur.n_level > n:
            upto = cur.n_level - n
            self.parse_para_insert(upto, cur, nod)
        else:  # cur < new
            cur.append(nod)
        self.cur = nod

    def parse_para_insert(self, n: int, prv: MDNode, cur: MDNode  # {{{1
                          ) -> None:
        n = n // 100
        while n >= 0:
            n -= 1
            if prv.parent is None:
                break
            prv = prv.parent
        prv.append(cur)

    def output(self, fname: Text) -> int:  # {{{1
        debg("out:open:" + fname)
        seq = self.root.children
        with open(fname, "wt") as fp:
            fp.write('<map version="1.1.0">\n')
            fp.write('<!-- To view this file, '
                     'download free mind mapping software FreeMind from '
                     'http://freemind.sourceforge.net -->\n')
            fp.write('<node TEXT="document">\n')
            for node in seq:
                text = node.compose()
                # debg("out:" + text)
                fp.write(text)
            fp.write('</node>\n</map>\n')
        return 0


def main(args: List[Text]) -> int:  # {{{1
    opts = options.parse(args)
    xml = FMXml.parse_markdown(opts.fname_mdn)
    return xml.output(opts.fname_out)


if __name__ == "__main__":  # {{{1
    sys.exit(main(sys.argv[1:]))
# vi: ft=python:et:ts=4:sw=4:tw=80:fdm=marker
