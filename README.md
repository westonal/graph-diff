
This library diffs two directional graphs and outputs the result as a dot file. Primary intended use is to compare changes in software dependencies, for example in gradle projects though it is designed to not be limited to gradle.

"Deps" Input Format
===

The input for one graph is just multiple lines in the format:
```
a -> b
```
This line denotes that `a` depends on `b`.

Files of this format have the `.deps` suffix. See the examples folder.

The set of dependencies in a file is then loaded in to a graph format, this is a [NetworkX DiGraph](https://networkx.org/documentation/stable/reference/classes/digraph.html) under the hood.

With two DiGraphs loaded (or otherwise created) you can compare them to create a diff.

The Diff
===

The diff of two DiGraphs _A_ and _B_ is another DiGraph that includes:

- All removed connections (present in _A_ but not _B_)
- All added connections (present in _B_ but not _A_)
- All removed nodes
- All added nodes
- All nodes at either end of an included connection
- All unchanging connections between all included nodes
- All transitive connections between all included nodes

Elements have metadata to describe which rule they are included under, such as "added"/"removed"/"transitive".

Output
===

The output is a dot file, properties in the DiGraph describing the added/removed/transitive state of elements are converted to color coding/line formats.

Gradle Input
===

This library contains code to parse a gradle dependency output into the deps format.

An example of generating this input is:

```shell
cd sample
gradle -q :app:dependencies --configuration runtimeClasspath > ../examples/dependencies.txt
```

For your own project you may need to edit the command for your main app name (`:app`) and configuration name (`runtimeClasspath`) to match your project. Also see `git_gradle_diff` section below for an end-to-end example.

Setup
===

Install `dot` if not present, this is used to create the images from the `.dot` file.

On mac you can do:

```shell
brew install graphviz
```

Create the python virtual environment. On a mac:

```shell
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Running
===

Start the python virtual environment if not still running from setup. On a mac:

```shell
source venv/bin/activate
```

Pass a single file into the diff.

```shell
python main.py diff examples/dependencies.txt
```

And it will create a png output.

Pass two deps files, and it will diff them:

```shell
python main.py diff examples/revision1.deps examples/revision2.deps
```

You can also pass in the output of the gradle dependencies query:

```shell
python main.py diff examples/dependencies.txt examples/dependencies2.txt
```

git_gradle_diff
===

The following command given a copy of the Signal git repository, will diff two commits on signal and produce a png.
It works by creating its own worktree and won't affect the repository otherwise.
Note that it leaves this worktree behind afterward.

```shell
python main.py git_gradle_diff ~/workspace/Signal-Android 1fc119e027d 4bbed2601cf -a :Signal-Android -c playProdReleaseRuntimeClasspath -o output/signal_diff.png
```

This is just one example integration, you can create your own scripts to generate intermediary gradle outputs or `.deps` files and just call the `diff` command with those.

Requirements
===

This project uses the following libraries for these purposes:

- [NetworkX](https://github.com/networkx/networkx) for graph analysis
- [Rich](https://github.com/Textualize/rich) for CLI formatting
- [Click](https://github.com/pallets/click/) for CLI command line argument parsing
