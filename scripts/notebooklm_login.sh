#!/bin/bash
# Fix PATH for notebooklm CLI and playwright
export PATH="/Users/franzccm/Library/Python/3.14/bin:$PATH"

echo "Starting NotebookLM login..."
echo "A browser will open. Log in with your entradeceo Google account."
echo "Once you see the NotebookLM homepage, press ENTER in this terminal."
echo ""

notebooklm login
