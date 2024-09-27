# anki-gen

This project is complimentary to my [blog post](https://fordeyn.tech), in which I discuss how to use it effectively with Vim and LaTeX. The main idea is to easily generate Anki flashcards from LaTeX files using custom-defined commands and parsing structures. 

## Prereqs
- **Python**: Make sure you have Python 3 installed, as the scripts are written in Python.
- **AnkiConnect**: An Anki plugin that allows external applications to interact with Anki. You can find it [here](https://ankiweb.net/shared/info/2055492159). Without this you'll get errors, you can add it within anki.
- **Vim plugins**: If you are using Vim, ensure that you have the necessary plugins for LaTeX and Python installed. You can find the recommended setup in the `./vim-extra` folder of this repository.

## Install
Clone the repository into `~/.local/share/anki-gen`:

```bash
git clone <repo-url> ~/.local/share/anki-gen
```

For more detailed info, visit the blog. 
