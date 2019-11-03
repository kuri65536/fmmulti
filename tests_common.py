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


class TestCommon(TestCase):  # {{{1
    def test_section_num_conv(self) -> None:  # {{{1
        from common import section_num_conv as dut
        self.assertEqual(0, dut(""))
        self.assertEqual(1, dut("a"))
        self.assertEqual(2, dut("b"))
        self.assertEqual(25, dut("y"))
        self.assertEqual(26, dut("z"))
        self.assertEqual(27, dut("aa"))
        self.assertEqual(52, dut("az"))
        self.assertEqual(53, dut("ba"))
        self.assertEqual(78, dut("bz"))
        self.assertEqual(79, dut("ca"))
        self.assertEqual(339, dut("ma"))
        self.assertEqual(675, dut("yy"))
        self.assertEqual(676, dut("yz"))
        self.assertEqual(701, dut("zy"))
        self.assertEqual(702, dut("zz"))
        self.assertEqual(703, dut("aaa"))

    def test_section_num_recv(self) -> None:  # {{{1
        from common import section_num_recv as dut
        self.assertEqual("a", dut(0))
        self.assertEqual("a", dut(1))    # 0
        self.assertEqual("b", dut(2))    # 1
        self.assertEqual("y", dut(25))   # 24
        self.assertEqual("z", dut(26))   # 25
        self.assertEqual("aa", dut(27))  # 1, 0
        self.assertEqual("ab", dut(28))  # 1, 1
        self.assertEqual("az", dut(52))  # 1, 25
        self.assertEqual("ba", dut(53))
        self.assertEqual("bz", dut(78))
        self.assertEqual("ca", dut(79))
        self.assertEqual("ma", dut(339))
        self.assertEqual("yy", dut(675))
        self.assertEqual("yz", dut(676))
        self.assertEqual("zy", dut(701))
        self.assertEqual("zz", dut(702))
        self.assertEqual("aaa", dut(703))
        self.assertEqual("zzz", dut(18278))
        self.assertEqual("aaaa", dut(18279))

    def test_section_num_incr_sub1(self) -> None:  # {{{1
        from common import section_num_incr_desc as dut
        self.assertEqual("a", dut(""))
        self.assertEqual("b", dut("a"))
        self.assertEqual("z", dut("y"))
        self.assertEqual("aa", dut("z"))
        self.assertEqual("ab", dut("aa"))
        self.assertEqual("ba", dut("az"))
        self.assertEqual("ca", dut("bz"))
        self.assertEqual("mn", dut("mm"))
        self.assertEqual("yz", dut("yy"))
        self.assertEqual("za", dut("yz"))
        self.assertEqual("zy", dut("zx"))
        self.assertEqual("zz", dut("zy"))
        self.assertEqual("aaa", dut("zz"))

    def test_section_num_incr_sub2(self) -> None:  # {{{1
        from common import section_num_incr_desc as dut
        self.assertEqual("0a", dut("0"))
        self.assertEqual("9a", dut("9"))
        self.assertEqual("99a", dut("99"))
        self.assertEqual("0-0a", dut("0-0"))
        self.assertEqual("0-0aa", dut("0-0z"))
        self.assertEqual("999-999a", dut("999-999"))


def main_section_num() -> None:  # {{{1
    dgt = [chr(i) for i in range(ord('a'), ord('z') + 1)]
    cur = "a"

    print("{:3d},{}".format(1, cur))

    for i in range(2, 18300):
        new = ""
        ch = cur[-1]
        n = dgt.index(ch)
        carry = n == len(dgt) - 1
        if carry:
            new = dgt[0]
        else:
            new = dgt[n + 1]
        for ch in reversed(cur[:-1]):
            n = dgt.index(ch)
            if not carry:
                new = ch + new
            elif n == len(dgt) - 1:
                new = dgt[0] + new  # carry = continue...
            else:
                carry, new = False, dgt[n + 1] + new
        if carry:
            new = dgt[0] + new
        cur = new
        print("{:3d},{}".format(i, new))

# end of file {{{1
# vi: ft=python:et:ts=4:sw=4:tw=80:fdm=marker
