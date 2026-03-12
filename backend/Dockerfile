FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port
EXPOSE 8000

# Run the application
<<<<<<< HEAD
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
=======
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
>>>>>>> 8f85023a091f4302d496481aa786772173e35887
