# Use the python:3.10-slim-bullseye image as a base image
FROM python:3.11-slim-bullseye

# Set the working directory in the container to /app
WORKDIR /app

# Copy the entire project into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install .

# Install LaTeX dependencies and Microsoft fonts
# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-xetex \
    build-essential \
    poppler-utils \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-lang-cyrillic \
    texlive-lang-european \
    texlive-lang-english \
    fonts-liberation \
    fonts-dejavu \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Refresh font cache
RUN fc-cache -f -v
# Set the Python PATH to include /app
ENV PYTHONPATH=/app

# Run the command to start your application
#CMD ["python", "bot/app/run.py"]
CMD ["sh", "-c", "uvicorn bot.app.app:app --host 0.0.0.0 --port 8000"]
