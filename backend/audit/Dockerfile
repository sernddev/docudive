# Use the official Python image from the Docker Hub


FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI app code into the container
COPY . .

# Set the entrypoint for the container
CMD ["uvicorn", "audit_server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

