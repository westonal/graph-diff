import os


def cd(path):
    return Cd(path)


class Cd(object):
    def __init__(self, path):
        self.restore_path = os.getcwd()
        self.path = path

    def __enter__(self):
        os.chdir(self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.restore_path)
