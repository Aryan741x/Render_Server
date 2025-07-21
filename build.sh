#!/usr/bin/env bash

# Update and install system dependency for C++ AST analysis
echo "Installing exuberant-ctags..."
apt-get update && apt-get install -y exuberant-ctags

# Print version to confirm success
ctags --version

# Done
echo "✅ Ctags installed successfully in Render build."
