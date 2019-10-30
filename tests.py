from unittest import TestCase


class TestCommand(TestCase):  # {{{1
    def test_fmmulti_normal(self) -> None:  # {{{1
        import fmmulti as dut
        dut.main(["-f", "-o", "sample-n.mm", "-i", "sample.mm",
                  "-m", "normal"])

    def test_fmmulti_doc(self) -> None:  # {{{1
        import fmmulti as dut
        dut.main(["-f", "-o", "sample-d.mm", "-i", "sample.mm",
                  "-m", "doc"])

    def test_fmmulti_test(self) -> None:  # {{{1
        import fmmulti as dut
        dut.main(["-f", "-o", "sample-t.mm", "-i", "sample.mm",
                  "-m", "test"])

    def test_md2fm(self) -> None:  # {{{1
        import md2fm as dut
        dut.main(["-f", "-o", "sample-m.mm", "sample.md"])

# end of file {{{1
# vi: ft=python:et:ts=4:sw=4:tw=80:fdm=marker
