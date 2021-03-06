#! env python3
'''
Copyright (c) 2019, shimoda as kuri65536 _dot_ hot mail _dot_ com
                    ( email address: convert _dot_ to . and joint string )

This Source Code Form is subject to the terms of the Mozilla Public License,
v.2.0. If a copy of the MPL was not distributed with this file,
You can obtain one at https://mozilla.org/MPL/2.0/.
'''
from argparse import ArgumentParser
import logging
from logging import (debug as debg, )  # , warning as warn
import re
import sys
import time
from typing import (Dict, Iterable, List, Optional, Text, )

import common as cmn
from common import HierBuilder, Node, NodeDmy, NodeNote

Dict, Optional


n_level_unit = 100
n_level_1st = 100
n_level_2nd = 200


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
            ret.fname_out = cmn.number_output(opts.override, src, ".mm")
        return ret


class MDNode(Node):  # {{{1
    def __init__(self, title: Text, buf: List[Text], n: int) -> None:  # {{{1
        Node.__init__(self, "section", {})

        title = title if not title.startswith(" ") else title[1:]

        self.parent: Optional[MDNode] = None
        self.title = title
        self.note = "\n".join(buf)
        self.n_level = n
        self.section = ""

    def compose(self, prv: Node) -> Text:  # {{{1
        debg("compose:node:" + Text(self.n_level))
        ret = '<node CREATED="{}" ID="{}" MODIFIED="{}"'.format(
                -1, int(time.time() * 1000), -1)
        ret += ' TEXT="{}"'.format(cmn.quote_attr(self.title))
        if len(self.note) > 0:
            node = NodeNote(self.note)
            self.children.insert(0, node)
        self.children.insert(0, cmn.Chars("\n"))
        self.children.insert(0, self.attr_section_number(prv))
        self.children.insert(0, cmn.Chars("\n"))
        self.children.insert(0, self.attr_level_score())
        if len(self.children) < 1:
            ret += "/>\n"
        else:
            ret += ">\n"
            prv_child: Node = NodeDmy()
            for nod in self.children:
                ret += nod.compose(prv_child)
                prv_child = nod
            ret += '</node>\n'
        return ret

    def attr_section_number_text(self, prv: Node) -> Text:  # {{{1
        if len(self.section) > 0:
            return self.section
        num = self.attr_section_number_from_title()
        if len(num) < 1:
            num = self.attr_section_number_from_nodes(prv)
        self.section = num
        return num

    def attr_section_number(self, prv: Node) -> Node:  # {{{1
        num = self.attr_section_number_text(prv)
        ret = Node("attribute", dict(
                        NAME="doc",
                        VALUE=num,
                   ))
        return ret

    def attr_level_score(self) -> Node:  # {{{1
        ret = Node("attribute", dict(
                        NAME="markdown-level",
                        VALUE=Text(self.n_level),
                   ))
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

    def attr_section_number_from_nodes(self, prv: Node) -> Text:  # {{{1
        if isinstance(prv, MDNode):
            num = prv.attr_section_number_text(prv)
            num = cmn.section_num_incr_desc(num)
            return num
        if isinstance(self.parent, MDNode):
            num = self.parent.section
        else:
            num = ""
        num = cmn.section_num_1st(num)
        return num

    def level_diff(self, nod: 'Node') -> int:  # {{{1
        if isinstance(nod, MDNode):
            n = nod.n_level
        elif nod.name == "root":
            n = 0
        else:
            n = n_level_unit * 10
        n = self.n_level - n
        return round(n / n_level_unit)

    def __repr__(self) -> Text:  # for debug {{{1
        return "{}-{}".format(self.n_level, self.title)


class FMXml(HierBuilder):  # {{{1
    @classmethod  # parse {{{1
    def parse_markdown(cls, fname: Text) -> 'FMXml':
        """parse Nodes from markdown
        """
        ret = FMXml()
        buf: List[Text] = []
        for line in cls.get_lines(fname):
            line = line.rstrip("\r\n")
            n = cls.is_section_line(line, buf)
            if n == 0:
                buf.append(line)
                continue
            debg("found {}-{}".format(n, line.strip()))
            if len(buf) < 1:
                buf = [line]
                continue
            if n in (n_level_1st, n_level_2nd):  # === or ---
                # exclude the last line.
                bf2 = buf[:-1]
                buf = [buf[-1], line]
            else:
                bf2 = buf
                buf = [line]
            ret.parse_markdown_build_hier(bf2)
        if len(ret.root.children) < 1:
            return ret
        ret.parse_markdown_build_hier(buf)  # parse left data...
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
    def is_section_line(cls, line: Text, lines: List[Text]) -> int:
        """- did not support '#' in \`\`\`
        """
        if len(line) < 1:
            return 0
        if line.startswith(" ") or line.startswith("\t"):
            return 0
        if len(line.lstrip("=")) < 1:
            if len(lines) < 1 or len(lines[-1].strip()) < 1:
                return 0
            return n_level_1st  # 1st level
        if len(line.lstrip("-")) < 1:
            if len(lines) < 1 or len(lines[-1].strip()) < 1:
                return 0
            return n_level_2nd  # 2nd level
        if not line.startswith("#"):
            return 0
        src = line.lstrip("#")
        n = len(line) - len(src)
        if n == 1:
            return n_level_1st + 10  # 1st level + alpha
        if n == 2:
            return n_level_2nd + 10  # 2nd level + alpha
        return n * n_level_unit

    def parse_markdown_build_hier(self, buf: List[Text]) -> None:  # {{{1
        line_2nd, buf2 = (buf[1], [buf[0]]) if len(buf) > 1 else ("", [])
        n = self.is_section_line(line_2nd, buf2)
        if n == n_level_1st:
            title, buf = buf[0], [] if len(buf) < 3 else buf[2:]
        elif n == n_level_2nd:
            title, buf = buf[0], [] if len(buf) < 3 else buf[2:]
        else:
            n = self.is_section_line(buf[0], [])
            title, buf = buf[0].lstrip("#"), buf[1:]
        nod = MDNode(title, buf, n)
        self.insert_node(nod)

    def output(self, fname: Text) -> int:  # {{{1
        debg("out:open:" + fname)
        seq = self.root.children
        with open(fname, "wt") as fp:
            fp.write('<map version="1.1.0">\n')
            fp.write(cmn.cmt_header + '\n')
            fp.write('<node TEXT="document">\n')
            prv: Node = NodeDmy()
            for node in seq:
                text = node.compose(prv)
                # debg("out:" + text)
                fp.write(text)
                prv = node
            fp.write('</node>\n</map>\n')
        return 0


def main(args: List[Text]) -> int:  # {{{1
    opts = options.parse(args)
    xml = FMXml.parse_markdown(opts.fname_mdn)
    return xml.output(opts.fname_out)


if __name__ == "__main__":  # {{{1
    sys.exit(main(sys.argv[1:]))
# vi: ft=python:et:ts=4:sw=4:tw=80:fdm=marker
