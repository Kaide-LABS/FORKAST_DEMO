# Use official Playwright image which has all browser dependencies
# Must match playwright version in requirements.txt
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Ensure Playwright uses pre-installed browsers
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run uses PORT env var)
EXPOSE 8080

# Start the application - Cloud Run provides PORT env variable
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
