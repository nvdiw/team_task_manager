FROM python:3.13-slim

# Prevent Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE 1

# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# Set working directory inside the container
WORKDIR /app

# Copy requirements file to the working directory
COPY requirements.txt /app/

# Install dependencies using Liara PyPI mirror for faster download in Iran
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . /app/

# Expose port 8000 for the Django development server
EXPOSE 8000

# Run database migrations and start the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]