FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port
EXPOSE 8000

# Make startup script executable
RUN chmod +x /app/start.sh

# Seed data then start the server
CMD ["/app/start.sh"]
