# 1. Use official Python image
FROM python:3.10-slim

# 2. Set working directory inside container
WORKDIR /app

# 3. Copy dependency file
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy project files
COPY . .

# 6. Run the app
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]



