# Use an official Python image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy the application files to the container
COPY . .

# Install dependencies from requirements.txt (if available)
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port FastAPI will run on
EXPOSE 8000

# Define the command to run the FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]