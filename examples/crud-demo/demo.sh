#!/bin/bash
# demo.sh - One-click demo: Build a FastAPI CRUD app from scratch

set -e

echo "🚀 Starting AI Factory OS CRUD Demo"
echo "This will create a working FastAPI app with database CRUD operations"
echo ""

# Create demo task
cat > tasks/task_demo.json << 'EOF'
{
  "task_id": "task_demo",
  "description": "Build a complete FastAPI CRUD application for managing users with SQLite database, Pydantic models, and REST endpoints",
  "assignee": "grok-fast",
  "status": "pending",
  "priority": 1,
  "files": [
    "shared/app/main.py",
    "shared/app/models.py",
    "shared/app/database.py",
    "requirements.txt"
  ]
}
EOF

echo "✅ Created demo task (task_demo.json)"
echo "🔄 Running orchestrator..."

# Run the orchestrator
python core/orchestrator.py

echo ""
echo "🎉 Demo complete! Check shared/app/ for the generated FastAPI app"
echo "Run with: cd shared/app && python main.py"
echo ""
echo "Test endpoints:"
echo "POST /users - Create user"
echo "GET /users - List users"
echo "GET /users/{id} - Get user"
echo "PUT /users/{id} - Update user"
echo "DELETE /users/{id} - Delete user"