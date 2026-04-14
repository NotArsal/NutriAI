# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies required by XGBoost and Scikit-Learn
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY backend/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt 
# Copy the rest of the application code
COPY . .

# Ensure Uvicorn uses standard production hosts and ports
ENV HOST=0.0.0.0
ENV PORT=8000

# Expose port (common for Render/Railway)
EXPOSE 8000

# Run main.py using uvicorn when the container launches
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
