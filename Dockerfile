# Use Python base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy the application code
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 8080

# Run the app
CMD ["python", "main.py"]
