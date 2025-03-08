# einkauf-heini

### requirements
python3.10

```bash
sudo apt install libffi-dev
pip install git+https://github.com/davekch/einkaufsbot.git
```

### usage
```bash
einkaufsbot path/to/token.txt --db path/to/db.sqlite

# or skip installation and run with uv:
uvx --python 3.12 --with git+https://github.com/davekch/einkaufsbot.git einkaufsbot token.txt
```
