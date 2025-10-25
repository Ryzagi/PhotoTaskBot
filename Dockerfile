# Use the python:3.10-slim-bullseye image as a base image
FROM python:3.11-slim-bullseye

# Set the working directory in the container to /app
WORKDIR /app

# Copy the entire project into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install .

# Install LaTeX with complete font support
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-xetex \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-lang-cyrillic \
    poppler-utils \
    fontconfig \
    fonts-dejavu \
    fonts-dejavu-extra \
    && rm -rf /var/lib/apt/lists/*

# Configure fonts - single run
RUN fc-cache -fv && mktexlsr

# Set the Python PATH to include /app
ENV PYTHONPATH=/app

# Run the command to start your application
CMD ["sh", "-c", "uvicorn bot.app.app:app --host 0.0.0.0 --port 8000"]
