#!/bin/bash

# Universal Website Scraper - Run Script

echo "🚀 Starting Universal Website Scraper..."

# Detect Python command (python3 or python)
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Error: Python not found. Please install Python 3.10+"
    exit 1
fi

echo "📌 Using Python command: $PYTHON_CMD"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Start the server
echo ""
echo "✅ Setup complete!"
echo "🎯 Starting server on http://localhost:8000"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the FastAPI application
python main.py