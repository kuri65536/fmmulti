#! env python3
from argparse import ArgumentParser
from enum import Enum
import tempfile
from typing import Dict, List, Text
import sys
from zipfile import ZipFile


class runmode(Enum):  # {{{1
    normal = 1


class options(object):  # {{{1
    def __init__(self) -> None:  # {{{1
        self.fname_xml = ""
        self.fname_zip = ""
        self.mode = runmode.normal

    @classmethod  # parser {{{1
    def parser(cls) -> ArgumentParser:  # {{{1
        arg = ArgumentParser()
        return arg

    @classmethod  # parse {{{1
    def parse(cls, args: List[Text]) -> 'options':
        ret = options()
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
        zf = ZipFile(fname)
        for zi in zf.infolist():
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
