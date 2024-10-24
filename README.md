# einkauf-heini

### requirements
python3.10

```bash
sudo apt install libffi-dev
poetry install --no-root
```

### secrets
put the token in `token.txt` or just do `sops -e secrets.enc.yml > secrets.yml`
