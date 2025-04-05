#!/bin/bash

# Get the absolute path to the update_credentials.py script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
UPDATE_SCRIPT="$SCRIPT_DIR/update_credentials.py"

# Create a temporary file for the crontab
TEMP_CRONTAB=$(mktemp)

# Export the current crontab
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "" > "$TEMP_CRONTAB"

# Check if the cron job already exists
if ! grep -q "$UPDATE_SCRIPT" "$TEMP_CRONTAB"; then
    # Add the cron job to run every Sunday at midnight
    echo "0 0 * * 0 cd $(dirname "$SCRIPT_DIR") && python3 $UPDATE_SCRIPT >> /var/log/justlearnit_credentials.log 2>&1" >> "$TEMP_CRONTAB"
    
    # Install the new crontab
    crontab "$TEMP_CRONTAB"
    echo "Cron job added successfully."
else
    echo "Cron job already exists."
fi

# Clean up
rm "$TEMP_CRONTAB" 