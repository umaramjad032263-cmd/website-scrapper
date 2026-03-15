# Use Google's official Playwright image for absolute compatibility
FROM mcr.microsoft.com/playwright:v1.42.0-jammy

# Set working directory
WORKDIR /app

# Install Node.js
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Install Python and Pip
RUN apt-get install -y python3 python3-pip

# Copy project files
COPY . .

# Install dependencies
RUN npm install
RUN pip3 install -r requirements.txt

# Expose port
EXPOSE 3005

# Start the server
CMD ["node", "scraper_server.js"]
