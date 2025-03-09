# Use an official Python image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY daily_scraper.py /app/
COPY channels.txt /app/
COPY scripts/run_cron.sh /app/scripts/
RUN chmod +x /app/scripts/run_cron.sh

# Create output directory
RUN mkdir -p /app/output

# Copy crontab file (we'll create it on the fly in run_cron.sh, or you can provide your own)
# If you have a static crontab file, you could do:
# COPY crontab /etc/cron.d/daily_scraper
# RUN chmod 0644 /etc/cron.d/daily_scraper

# Run the shell script that sets up cron, then runs the cron daemon in the foreground
CMD ["/app/scripts/run_cron.sh"]