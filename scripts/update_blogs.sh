#!/bin/bash
# Script to update Mbugani Luxe Adventures blog posts
# This script runs the populate_luxury_blogs management command

echo "=========================================="
echo "Mbugani Luxe Adventures - Blog Update"
echo "=========================================="
echo ""

# Check if we should run in production mode
if [ "$1" == "--production" ] || [ "$1" == "-p" ]; then
    echo "⚠️  WARNING: Running in PRODUCTION mode"
    echo "This will update the LIVE production database!"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "❌ Cancelled."
        exit 0
    fi
    
    echo ""
    echo "🚀 Running blog update on PRODUCTION database..."
    DJANGO_ENV=production python manage.py populate_luxury_blogs
else
    echo "🔧 Running blog update on DEVELOPMENT database..."
    echo "(Use --production or -p flag to update production database)"
    echo ""
    python manage.py populate_luxury_blogs
fi

echo ""
echo "✅ Blog update complete!"
echo ""

