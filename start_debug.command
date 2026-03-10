#!/bin/bash
# Baby Game Debug Launcher for macOS
# Double-click this file to start the game in debug mode

cd "$(dirname "$0")"
echo "========================================="
echo "  Baby Keyboard & Mouse Game"
echo "========================================="
echo ""
echo "  Starting debug window..."
echo "  Windowed mode with normal mouse/keyboard behavior"
echo ""
python3 baby_game.py --debug
