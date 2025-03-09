#!/bin/bash

# Write out current crontab
# This example runs the scraper every day at 07:00
echo "0 7 * * * /usr/bin/python3 /app/scraper.py >> /var/log/cron.log 2>&1" > /etc/cron.d/daily_scraper

# Give execution rights on the cron job
chmod 0644 /etc/cron.d/scraper

# Create the log file to be able to run tail
touch /var/log/cron.log

# Apply cron job
crontab /etc/cron.d/scraper

# Start cron in foreground
cron && tail -f /var/log/cron.log