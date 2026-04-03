#!/bin/bash
# BKT Agency — Secure .env credential setter
# Usage: bash set_credentials.sh
# The password input is hidden (not shown on screen or in logs)

ENV_FILE="$(dirname "$0")/.env"

echo ""
echo "BKT Agency — WordPress Credential Setup"
echo "========================================"
echo "This script writes your WordPress Application Password"
echo "to the .env file. Input is hidden and never logged."
echo ""
echo "Leave blank and press Enter to skip a field."
echo ""

# Read WP_USERNAME
current_user=$(grep "^WP_USERNAME=" "$ENV_FILE" | cut -d= -f2)
read -p "WP_USERNAME [$current_user]: " new_user
new_user="${new_user:-$current_user}"

# Read WP_APP_PASSWORD silently
read -s -p "WP_APP_PASSWORD (hidden): " new_password
echo ""

if [ -z "$new_password" ]; then
  echo ""
  echo "No password entered — .env file unchanged."
  exit 0
fi

# Write values into .env using sed
sed -i "s|^WP_USERNAME=.*|WP_USERNAME=$new_user|" "$ENV_FILE"
sed -i "s|^WP_APP_PASSWORD=.*|WP_APP_PASSWORD=$new_password|" "$ENV_FILE"

echo ""
echo "✓ .env updated successfully."
echo "  WP_USERNAME    = $new_user"
echo "  WP_APP_PASSWORD = [hidden]"
echo ""
echo "To verify (password stays hidden):"
echo "  grep WP_ .env | sed 's/WP_APP_PASSWORD=.*/WP_APP_PASSWORD=[hidden]/'"
echo ""
