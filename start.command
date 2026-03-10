#!/bin/bash
# Baby Game Launcher for macOS
# Double-click this file to start the game

cd "$(dirname "$0")"
echo "========================================="
echo "  Baby Keyboard & Mouse Game"
echo "========================================="
echo ""
echo "  Starting fullscreen game..."
echo "  Exit: Hold Ctrl + Shift + Escape for 3 seconds"
echo ""
python3 baby_game.py
