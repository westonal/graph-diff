
Setup
===

Install `dot` if not present, this is used to create the images from the `.dot` file.

On mac you can do:

```shell
brew install graphviz
```

Running
===

Create a file with gradle dependencies. You may need to edit the below command for your main app name (`:app`) and configuration name (`runtimeClasspath`) to match your project.

```shell
cd sample
gradle -q :app:dependencies --configuration runtimeClasspath > ../examples/dependencies.txt
```

Start the python virtual environment. On a mac:

```shell
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Pass this file into main and then out to `dot`:

```shell
python main.py diff examples/dependencies.txt
```

And it will create a png output.

Pass two files, and it will diff them:

```shell
python main.py diff examples/dependencies.txt examples/dependencies2.txt
```

It also creates an intermediary format which can be used as an input for non-gradle usages.

```shell
python main.py diff examples/revision1.deps examples/revision2.deps
```

Uses
===

- [NetworkX](https://github.com/networkx/networkx) for graph analysis
- [Rich](https://github.com/Textualize/rich) for CLI formatting
- [Click](https://github.com/pallets/click/) for the CLI command line arguments
