from lib.cli.commands import commands
# noinspection PyUnresolvedReferences
from lib.cli.diff import cmd_diff
# noinspection PyUnresolvedReferences
from lib.cli.git_gradle_diff import cmd_gradle_diff
# noinspection PyUnresolvedReferences
from lib.cli.tests import cmd_tests

if __name__ == '__main__':
    commands()
