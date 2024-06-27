FROM python:3.9-slim

# Install required libraries
RUN pip install --no-cache-dir pymupdf requests && \
    pip install PyPDF2

# Copy the Python script
COPY translate_pdf.py /app/translate_pdf.py

# Set the working directory
WORKDIR /app

# Set the entry point
ENTRYPOINT ["python", "/app/translate_pdf.py"]

