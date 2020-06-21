# Pythagoras
harmony = relations between numbers

## Installation
Download:\
[linux-standalone](https://drive.google.com/uc?export=download&id=1Y2efsxE8QwaZ1zdd3UjLRBcphFtaeD7W)

Alternatively, clone and:
```sh
pip install -r requirements.txt
```

### Building standalone version
```
pyinstaller --noconfirm --onefile --hidden-import packaging.requirements --hidden-import pkg_resources.py2_warn --add-data "venv/lib/python3.8/site-packages/pyfiglet:./pyfiglet" --icon aulos.ico pythagoras.py
```