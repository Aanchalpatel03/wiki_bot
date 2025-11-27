#!/bin/bash
# Quick Start Script for Wikimedia CatDiffuse Bot
# Run this to set up your environment step-by-step

set -e  # Exit on error

echo "🤖 Wikimedia CatDiffuse Bot - Quick Start Setup"
echo "================================================"
echo ""

# Check Python version
echo "✓ Checking Python version..."
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.8+"; exit 1; }
echo ""

# Check if dependencies are installed
echo "✓ Checking dependencies..."
if ! python3 -c "import pywikibot" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing now..."
    pip3 install -r requirements.txt
else
    echo "✓ Dependencies already installed"
fi
echo ""

# Check for .env file
echo "✓ Checking for .env file..."
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo ""
    echo "📝 ACTION REQUIRED:"
    echo "   Please edit .env and add your bot credentials:"
    echo "   - BOT_USERNAME=YourBotName"
    echo "   - BOT_PASSWORD=your_bot_password"
    echo ""
    echo "   Create bot password at:"
    echo "   https://commons.wikimedia.org/wiki/Special:BotPasswords"
    echo ""
    read -p "Press Enter after you've edited .env..."
else
    echo "✓ .env file exists"
fi
echo ""

# Check for user-config.py
echo "✓ Checking for Pywikibot config..."
if [ ! -f user-config.py ]; then
    echo "⚠️  No user-config.py found. Creating from template..."
    cp user-config-template.py user-config.py
    echo ""
    echo "📝 ACTION REQUIRED:"
    echo "   Please edit user-config.py and set:"
    echo "   usernames['commons']['commons'] = 'YourBotName'"
    echo ""
    read -p "Press Enter after you've edited user-config.py..."
else
    echo "✓ user-config.py exists"
fi
echo ""

# Run tests
echo "✓ Running unit tests..."
python3 -m pytest tests/test_template_replacement.py -v
echo ""

# Offer dry-run
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Test with dry-run: python3 replace_catdiffuse.py --dry-run --limit 3"
echo "  2. Review logs: cat replace_catdiffuse.log"
echo "  3. Request bot approval (see BOT_APPROVAL_TEMPLATE.md)"
echo "  4. Run production: python3 replace_catdiffuse.py --limit 50 --delay 5"
echo ""

read -p "Would you like to run a dry-run test now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running dry-run test on 3 categories..."
    python3 replace_catdiffuse.py --dry-run --limit 3
    echo ""
    echo "Check replace_catdiffuse.log for details"
fi

echo ""
echo "✅ All done! Happy botting! 🤖"
