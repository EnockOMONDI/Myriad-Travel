#!/bin/bash

# Script to update package categories for Mbugani Luxe Adventures
# This script provides a convenient wrapper around the Django management command

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Package Category Update Script${NC}"
echo -e "${BLUE}Mbugani Luxe Adventures${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Parse command line arguments
DRY_RUN=""
PRODUCTION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --production|-p)
            PRODUCTION="true"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--dry-run] [--production|-p]"
            exit 1
            ;;
    esac
done

# Change to project directory
cd "$PROJECT_DIR"

# Determine environment
if [ "$PRODUCTION" = "true" ]; then
    echo -e "${YELLOW}⚠️  PRODUCTION MODE${NC}"
    echo -e "${YELLOW}This will update package categories in the PRODUCTION database!${NC}"
    echo ""
    
    if [ -z "$DRY_RUN" ]; then
        echo -e "${RED}WARNING: This is NOT a dry run. Changes will be permanent!${NC}"
        echo ""
        read -p "Are you absolutely sure you want to continue? (type 'yes' to confirm): " confirm
        
        if [ "$confirm" != "yes" ]; then
            echo -e "${RED}Operation cancelled.${NC}"
            exit 1
        fi
    fi
    
    ENV_PREFIX="DJANGO_ENV=production"
else
    echo -e "${GREEN}📝 DEVELOPMENT MODE${NC}"
    echo -e "Using development database (SQLite)"
    echo ""
    ENV_PREFIX=""
fi

# Show dry run status
if [ -n "$DRY_RUN" ]; then
    echo -e "${BLUE}🔍 DRY RUN MODE: No changes will be saved${NC}"
    echo ""
fi

# Run the management command
echo -e "${GREEN}Running package category update command...${NC}"
echo ""

if [ -n "$ENV_PREFIX" ]; then
    $ENV_PREFIX python manage.py update_package_categories $DRY_RUN
else
    python manage.py update_package_categories $DRY_RUN
fi

# Success message
echo ""
if [ -n "$DRY_RUN" ]; then
    echo -e "${GREEN}✅ Dry run completed successfully!${NC}"
    echo -e "${BLUE}To apply changes, run without --dry-run flag${NC}"
else
    echo -e "${GREEN}✅ Package categories updated successfully!${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo ""

# Usage examples
if [ -z "$DRY_RUN" ] && [ -z "$PRODUCTION" ]; then
    echo -e "${YELLOW}💡 Usage Examples:${NC}"
    echo ""
    echo -e "  ${BLUE}# Preview changes (dry run):${NC}"
    echo -e "  ./scripts/update_package_categories.sh --dry-run"
    echo ""
    echo -e "  ${BLUE}# Update development database:${NC}"
    echo -e "  ./scripts/update_package_categories.sh"
    echo ""
    echo -e "  ${BLUE}# Preview production changes:${NC}"
    echo -e "  ./scripts/update_package_categories.sh --production --dry-run"
    echo ""
    echo -e "  ${BLUE}# Update production database:${NC}"
    echo -e "  ./scripts/update_package_categories.sh --production"
    echo ""
fi

