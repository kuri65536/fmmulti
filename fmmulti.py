#! env python3
from argparse import ArgumentParser
from enum import Enum
import logging
from logging import debug as debg
import tempfile
import os
import sys
from typing import Dict, List, Text
from zipfile import ZipFile


class runmode(Enum):  # {{{1
    normal = 1

    @classmethod  # choices {{{1
    def choices(cls) -> List[Text]:
        ret = []
        for i in runmode:
            t = Text(i)
            t = t.replace("runmode.", "")
            ret.append(t)
        return ret

    @classmethod  # parse {{{1
    def parse(cls, src: Text) -> 'runmode':
        for i in runmode:
            if src == Text(i):
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


class FMNode(object):  # {{{1
    def __init__(self, attrs: Dict[Text, Text]) -> None:  # {{{1
        pass


class FMXml(object):  # {{{1
    def __init__(self) -> None:  # {{{1
        self.f_header = True
        self.t_header = ""
        self.t_footer = ""
        self.cur = FMNode({})

    @classmethod  # parse {{{1
    def parse(cls, fname: Text) -> 'FMXml':
        """parse Nodes from xml.
        """
        ret = FMXml()
        return ret

    def start_tag(self, name: Text, attrs: Dict[Text, Text]) -> None:  # {{{1
        pass

    def end_tag(self, name: Text) -> None:  # {{{1
        pass

    def output(self, mode: runmode) -> int:  # {{{1
        return 0


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
            if zi.is_dir():
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
    xml = FMXml()
    xml.parse(opts.fname_xml)
    return xml.output(opts.mode)


if __name__ == "__main__":  # {{{1
    sys.exit(main(sys.argv[1:]))
# vi: ft=python:et:ts=4:sw=4:tw=80:fdm=marker
