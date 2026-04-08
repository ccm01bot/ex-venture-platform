#!/bin/bash

echo "Starting EX Venture Platform..."

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ./backend/.env ]; then
    echo "Creating .env file from .env.example..."
    cp ./backend/.env.example ./backend/.env
fi

# Create .env.local file for frontend if it doesn't exist
if [ ! -f ./frontend/.env.local ]; then
    echo "Creating frontend .env.local file..."
    cp ./frontend/.env.local.example ./frontend/.env.local
fi

# Start Docker services
echo "Starting Docker services..."
docker-compose up --build

echo "Done! Access the application at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
