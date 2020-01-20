#!/usr/bin/bash
pandoc KGDB.md -s -f markdown -t html -o KGDB.html
pandoc NOTES.md -s -f markdown -t html -o NOTES.html
pandoc README.md -s -f markdown -t html -o README.html
pandoc SKINNING.md -s -f markdown -t html -o SKINNING.html
