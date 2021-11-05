#!/usr/bin/bash
pandoc --highlight-style=tango -t html --standalone --toc -c buttondown.css -f markdown -t html -o KGDB.html KGDB.md
pandoc NOTES.md -s -f markdown -t html -o NOTES.html
pandoc README.md -s -f markdown -t html -o README.html
pandoc SKINNING.md -s -f markdown -t html -o SKINNING.html
