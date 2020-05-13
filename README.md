# Pythagoras
harmony = relations between numbers

## Installation
```sh
pip install -r requirements.txt
```

## Distribution
```
pyinstaller --noconfirm --onefile --hidden-import packaging.requirements --hidden-import pkg_resources.py2_warn --add-data "venv/lib/python3.8/site-packages/pyfiglet:./pyfiglet" --icon aulos.ico pythagoras.py
```