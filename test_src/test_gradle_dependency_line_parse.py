from unittest import TestCase

from diff_dot.gradle import gradle_line_parse, Project, GradleCoordinate


class TestGradleDependencyLineParsing(TestCase):

    def test_not_a_line(self):
        self.assertIsNone(gradle_line_parse("-------"))

    def test_a_project(self):
        indent, line = gradle_line_parse("|    |    |    +--- project :abc")
        self.assertEqual(Project(":abc"), line)
        self.assertEqual(4, indent)

    def test_a_different_project(self):
        indent, line = gradle_line_parse("|    |    +--- project :def:ghi")
        self.assertEqual(Project(":def:ghi"), line)
        self.assertEqual(3, indent)

    def test_a_gradle_coordinate(self):
        indent, line = gradle_line_parse("|    +--- com.android.billingclient:billing-ktx:7.1.1")
        self.assertEqual(GradleCoordinate("com.android.billingclient:billing-ktx"), line)
        self.assertEqual(2, indent)

    def test_a_gradle_coordinate_with_asterisk_meaning_repeated(self):
        indent, line = gradle_line_parse("|    |    +--- androidx.fragment:fragment-ktx:1.8.5 (*)")
        self.assertEqual(GradleCoordinate("androidx.fragment:fragment-ktx"), line)
        self.assertEqual(3, indent)

    def test_a_gradle_coordinate_with_version_update(self):
        indent, line = gradle_line_parse(
            "|    |    |    +--- com.google.android.datatransport:transport-api:3.0.0 -> 3.1.0 (*)"
        )
        self.assertEqual(GradleCoordinate("com.google.android.datatransport:transport-api"), line)
        self.assertEqual(4, indent)
