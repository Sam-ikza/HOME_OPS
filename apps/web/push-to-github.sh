#!/bin/bash

# HomeOps GitHub Push Script
# Run this after setting up your GitHub repository

echo "🚀 HomeOps GitHub Push Script"
echo "=============================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Initialize git if not already
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
fi

# Add all files
echo "Adding files to git..."
git add .

# Commit
echo "Committing changes..."
git commit -m "HomeOps MVP: AI Home Maintenance Assistant

- Complete interactive demo with dashboard, inventory, AI chat, home scan, and alerts
- Simulated multi-agent AI system with RAG capabilities
- Polished dark theme UI built with React + Tailwind CSS
- Ready for hackathon presentation or investor pitch"

# Ask for remote URL
echo ""
echo "📦 Ready to push to GitHub!"
echo ""
echo "If you haven't created a repository yet, please do so at:"
echo "  https://github.com/new"
echo ""
echo "Then run the following commands:"
echo ""
echo "  git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git"
echo "  git branch -M main"
echo "  git push -u origin main"
echo ""
echo "Or, if you've already set the remote, just run:"
echo "  git push -u origin main"
echo ""
echo "Happy hacking! 🏠✨"