#!/bin/bash
# filepath: \\wsl.localhost\Debian\home\virga\apie-adv2\install.sh

echo "========================================="
echo "  NETCRAFT API Installation Script"
echo "========================================="

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Stop any existing containers
echo "🛑 Stopping existing containers..."
sudo docker compose down --volumes --remove-orphans 2>/dev/null || true

# Remove existing images (optional, uncomment if you want fresh builds)
echo "🗑️  Removing existing images..."
sudo docker compose down --rmi all 2>/dev/null || true

# Build and start the application
echo "🏗️  Building and starting NETCRAFT API..."
if sudo docker compose up -d --build --force-recreate; then
    echo "✅ NETCRAFT API started successfully!"
    echo ""
    echo "📋 Service Status:"
    sudo docker compose ps
    echo ""
    echo "🌐 Application URLs:"
    echo "   - API: http://localhost:3000"
    echo "   - Health Check: http://localhost:3000/health"
    echo ""
    echo "📊 To view logs:"
    echo "   - All services: sudo docker compose logs -f"
    echo "   - Web only: sudo docker compose logs -f web"
    echo "   - MySQL only: sudo docker compose logs -f mysql"
    echo ""
    echo "🔧 To stop the application:"
    echo "   - Run: ./uninstall.sh"
    echo "   - Or: sudo docker compose down"
else
    echo "❌ Failed to start NETCRAFT API"
    echo "📋 Checking logs..."
    sudo docker compose logs
    exit 1
fi

echo "========================================="
echo "  Installation Complete!"
echo "========================================="