from unittest import TestCase

from diff_dot.dependencies import Dependencies, Dependency


class TestDependencies(TestCase):

    def test_add_single_str(self):
        dependencies = Dependencies()
        dependencies.add_str("a -> b")
        self.assertEqual([Dependency("a", "b")], dependencies.list())

    def test_add_single_str_new_line(self):
        dependencies = Dependencies()
        dependencies.add_str("d -> e\n")
        self.assertEqual([Dependency("d", "e")], dependencies.list())

    def test_add_self_reference(self):
        dependencies = Dependencies()
        dependencies.add_str("a")
        self.assertEqual([Dependency("a", "a")], dependencies.list())

    def test_add_multiple(self):
        dependencies = Dependencies()
        dependencies.add_str("a -> b -> c")
        self.assertEqual([
            Dependency("a", "b"),
            Dependency("b", "c"),
        ], dependencies.list())
