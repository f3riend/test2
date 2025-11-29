# secure-box

Secure Box is a Python CLI application that allows you to securely encrypt files and folders with AES-GCM and store them in a single file. 
The developed system scans large folders, compresses them, encrypts them with AES-GCM and stores them as a single file with a secure backup mechanism.


## Features

- Strong encryption with AES-GCM
- Encrypting large folders in parts (chunking)
- Secure backup and unpacking

## Utilization
### Locking a folder or file
```bash
uv run python main.py lock <folder> <output_filename> <password>
```

### Unlock
```bash
uv run python main.py unlock <filename> <password>
```
## File structure

```bash
secure-box/
├── main.py          ← CLI and entrypoint
├── utils/           ← Auxiliary modules
│   ├── lock.py
│   ├── unlock.py
│   ├── backup.py
│   ├── logger.py
│   ├── mail_manager.py
│   ├── observer.py
│   └── tools.py
├── logs/            ← Runtime logs
├── build.py         ← Build script (Nuitka + UV)
├── Makefile         ← Build ve debug commands
├── pyproject.toml   ← Dependencies
└── uv.lock          ← UV lock file
```
## Setup
# test2
