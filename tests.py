#! env python3
'''
Copyright (c) 2019, shimoda as kuri65536 _dot_ hot mail _dot_ com
                    ( email address: convert _dot_ to . and joint string )

This Source Code Form is subject to the terms of the Mozilla Public License,
v.2.0. If a copy of the MPL was not distributed with this file,
You can obtain one at https://mozilla.org/MPL/2.0/.
'''
import logging
from unittest import TestCase


logging.basicConfig(level=logging.INFO)


class TestCommand(TestCase):  # {{{1
    def test_fmmulti_through(self) -> None:  # {{{1
        import fmmulti as dut
        dut.main(["-f", "-o", "sample-0.mm", "-i", "sample.mm",
                  ])

    def test_fmmulti_doc(self) -> None:  # {{{1
        import fmmulti as dut
        dut.main(["-f", "-o", "sample-d.mm", "-i", "sample.mm",
                  "-m", "doc"])

    def test_fmmulti_test(self) -> None:  # {{{1
        import fmmulti as dut
        dut.main(["-f", "-o", "sample-t.mm", "-i", "sample.mm",
                  "-S", "-m", "test"])

    def test_fmmulti_backup(self) -> None:  # {{{1
        import fmmulti as dut
        dut.main(["-f", "-o", "sample-b.mm", "-i", "sample.mm",
                  "-m", "backup"])

    def test_fmmulti_remove_backup(self) -> None:  # {{{1
        import fmmulti as dut
        dut.main(["-f", "-B", "-o", "sample-B.mm", "-i", "sample.mm",
                  "-m", "backup"])

    def test_fmmulti_convert_backup(self) -> None:  # {{{1
        import fmmulti as dut
        dut.main(["-f", "-o", "sample-c.mm", "-i", "sample.mm", "-c", "bck1",
                  "-m", "backup"])

    def test_md2fm(self) -> None:  # {{{1
        import md2fm as dut
        dut.main(["-f", "-o", "sample-m.mm", "sample.md"])

        import fmmulti as dut2
        dut2.main(["-f", "-M", "0", "-o", "sample-m.md", "-i", "sample-m.mm"])

# end of file {{{1
# vi: ft=python:et:ts=4:sw=4:tw=80:fdm=marker
