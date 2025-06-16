#!/bin/bash
# filepath: \\wsl.localhost\Debian\home\virga\apie-adv2\uninstall.sh

echo "========================================="
echo "  NETCRAFT API Uninstallation Script"
echo "========================================="

# Function to confirm deletion
confirm_deletion() {
    read -p "⚠️  This will remove ALL containers, networks, volumes, and images. Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Uninstallation cancelled."
        exit 1
    fi
}

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Some cleanup may not be possible."
fi

# Confirm with user
confirm_deletion

echo "🛑 Stopping all containers..."
sudo docker compose down 2>/dev/null || true

echo "🗑️  Removing containers, networks, and volumes..."
sudo docker compose down --volumes --remove-orphans 2>/dev/null || true

echo "🗑️  Removing Docker images..."
# Remove images built by this compose file
if sudo docker compose down --rmi all 2>/dev/null; then
    echo "✅ Project images removed"
else
    echo "⚠️  Some images might still exist"
fi

# Optional: Remove specific images if they exist
echo "🗑️  Removing specific NETCRAFT images..."
sudo docker rmi netcraft_web 2>/dev/null || true
sudo docker rmi $(sudo docker images --filter "reference=apie-adv2*" -q) 2>/dev/null || true

echo "🗑️  Removing Docker volumes..."
# Remove named volumes
sudo docker volume rm apie-adv2_mysql_data 2>/dev/null || true
sudo docker volume rm $(sudo docker volume ls --filter "name=apie-adv2" -q) 2>/dev/null || true

echo "🗑️  Removing Docker networks..."
# Remove custom networks
sudo docker network rm apie-adv2_netcraft_network 2>/dev/null || true
sudo docker network rm $(sudo docker network ls --filter "name=apie-adv2" -q) 2>/dev/null || true

echo "🧹 Cleaning up unused Docker resources..."
# Clean up dangling images, containers, networks, and build cache
sudo docker system prune -f 2>/dev/null || true

echo "🧹 Removing build cache..."
sudo docker builder prune -f 2>/dev/null || true

echo ""
echo "📊 Remaining Docker resources:"
echo "--- Images ---"
sudo docker images
echo ""
echo "--- Volumes ---"
sudo docker volume ls
echo ""
echo "--- Networks ---"
sudo docker network ls
echo ""

echo "========================================="
echo "  ✅ Uninstallation Complete!"
echo "========================================="
echo ""
echo "🗑️  All NETCRAFT API resources have been removed:"
echo "   - Containers stopped and removed"
echo "   - Docker images removed"
echo "   - Volumes and data removed"
echo "   - Networks removed"
echo "   - Build cache cleared"
echo ""
echo "📁 Note: Source code files remain untouched"
echo "🔄 To reinstall, run: ./install.sh"