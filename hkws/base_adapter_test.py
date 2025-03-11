from unittest import TestCase

from hkws.base_adapter import BaseAdapter


class TestHKAdapter(TestCase):
    def test_add_lib(self):
        a = BaseAdapter()
        a.add_lib("../lib/", ".dll")
        print(a.so_list)
