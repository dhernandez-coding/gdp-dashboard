# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file from the backend directory
COPY react-dashboard/backend/requirements.txt ./react-dashboard/backend/

# Install any needed packages
RUN pip install --no-cache-dir -r react-dashboard/backend/requirements.txt

# Copy everything from the root context
COPY . .

# Set working directory to backend for running the app
WORKDIR /app/react-dashboard/backend

# Make port 5000 available
EXPOSE 5000

# Define environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONPATH=/app

# Run app.py with gunicorn for production
# Azure Web Apps can map to this port
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]
