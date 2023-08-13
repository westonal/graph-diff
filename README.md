
Setup
===

Install `dot` if not present, this is used to create the images from the `.dot` file.

On mac you can do:

```shell
brew install graphviz
```

Running
===

Create a file with gradle dependencies. You may need to customize the main app name (`:app`) and configuration name (`runtimeClasspath`) to match your project.

```shell
cd sample
gradle -q :app:dependencies --configuration runtimeClasspath > ../examples/dependencies.txt
```

Start the python virtual environment. On mac:

```shell
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Pass this file into main and then out to `dot`:

```shell
python3 main.py
dot -Tpng output/sample.dot -o output/sample.png
dot -Tpng output/example.dot -o output/example.png
```
