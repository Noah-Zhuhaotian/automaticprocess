# automaticprocess

An automated office assistant: a Windows desktop app (eventually packaged
as an exe) with three features:

1. Automatically create folders under a specified base directory
2. Automatically fill in content into a Word document
3. Automatically submit content to a timesheet/info recording website

## Project structure

```
app/
├── main.py            # app entry point, launches the GUI
├── gui/
│   └── main_window.py # main window (one tab per feature)
├── core/
│   ├── folder_creator.py  # Step 1: create folders
│   ├── word_filler.py     # Step 2: fill Word
│   └── web_filler.py      # Step 3: fill timesheet website
├── config/
│   └── settings.py    # read/write user settings (saved paths, etc.)
└── utils/
    └── logger.py       # logging

resources/templates/     # Word templates and other assets
build_scripts/           # exe build scripts (added later)
tests/                   # tests
main.py                  # root entry script, run `python main.py` to start
requirements.txt
```

## Dev setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Progress

- [x] Project skeleton
- [ ] Step 1: automatically create folders
- [ ] Step 2: automatically fill Word documents
- [ ] Step 3: automatically fill the timesheet website
- [ ] Package as exe
