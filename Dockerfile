# Use the python:3.10-slim-bookworm  image as a base image
FROM python:3.11-slim-bookworm

# Set the working directory in the container to /app
WORKDIR /app

# Copy the entire project into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install .

# Install LaTeX with pdflatex support (not xelatex)
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-lang-cyrillic \
    texlive-fonts-recommended \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Configure fonts
RUN mktexlsr


# Set the Python PATH to include /app
ENV PYTHONPATH=/app

# Run the command to start your application
CMD ["sh", "-c", "uvicorn bot.app.app:app --host 0.0.0.0 --port 8000"]
