"""Flask routes for Art Studio Companion."""

import os
import json
from flask import Blueprint, request, jsonify, render_template, current_app
from werkzeug.utils import secure_filename

from app.models import init_db, SessionLocal, Supply, Project, PortfolioPiece
from app.tools.supply_inventory import get_all_supplies, get_low_stock_supplies, add_supply
from app.tools.portfolio_storehouse import get_portfolio, get_portfolio_stats
from app.tools.project_filesaver import get_all_projects, create_project_from_query


main_bp = Blueprint('main', __name__)

# Upload configuration
UPLOAD_FOLDER = 'data/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main_bp.before_app_request
def setup():
    """Initialize database on first request."""
    init_db()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============== Main Page ==============

@main_bp.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')


# ============== Chat API ==============

@main_bp.route('/api/chat', methods=['POST'])
def chat():
    """Send a message to the Letta agent and get a response."""
    data = request.get_json()
    message = data.get('message', '')

    if not message:
        return jsonify({"success": False, "error": "No message provided"}), 400

    try:
        from app.agent import get_agent
        agent = get_agent()
        response = agent.send_message(message)
        return jsonify(response)
    except Exception as e:
        # Fallback to a simple response if Letta is not available
        return jsonify({
            "success": True,
            "response": f"I received your message: '{message}'. Note: Letta agent is not currently connected. Please ensure the Letta server is running.",
            "fallback": True,
            "error_details": str(e)
        })


# ============== Supplies API ==============

@main_bp.route('/api/supplies', methods=['GET'])
def api_get_supplies():
    """Get all supplies with optional category filter."""
    category = request.args.get('category')
    result = get_all_supplies(category=category)
    return jsonify(result)


@main_bp.route('/api/supplies/low-stock', methods=['GET'])
def api_low_stock():
    """Get low stock supplies."""
    threshold = float(request.args.get('threshold', 0.25))
    result = get_low_stock_supplies(threshold=threshold)
    return jsonify(result)


@main_bp.route('/api/supplies', methods=['POST'])
def api_add_supply():
    """Add a new supply."""
    data = request.get_json()
    result = add_supply(
        name=data.get('name'),
        category=data.get('category'),
        brand=data.get('brand'),
        color=data.get('color'),
        size=data.get('size'),
        quantity=float(data.get('quantity', 1.0)),
        unit=data.get('unit', 'piece'),
        notes=data.get('notes')
    )
    return jsonify(result)


@main_bp.route('/api/supplies/scan', methods=['POST'])
def api_scan_supplies():
    """Handle supply photo upload for scanning."""
    if 'photo' not in request.files:
        return jsonify({"success": False, "error": "No photo provided"}), 400

    file = request.files['photo']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # In a full implementation, this would use image analysis
        return jsonify({
            "success": True,
            "message": "Photo uploaded successfully. Please describe the supplies visible and I'll help add them to your inventory.",
            "image_path": filepath
        })

    return jsonify({"success": False, "error": "Invalid file type"}), 400


# ============== Projects API ==============

@main_bp.route('/api/projects', methods=['GET'])
def api_get_projects():
    """Get all projects."""
    status = request.args.get('status')
    result = get_all_projects(status=status)
    return jsonify(result)


@main_bp.route('/api/projects/suggest', methods=['POST'])
def api_suggest_project():
    """Get project suggestion from a query."""
    data = request.get_json()
    query = data.get('query', '')
    budget = data.get('budget')

    result = create_project_from_query(
        query=query,
        budget=float(budget) if budget else None
    )
    return jsonify(result)


# ============== Portfolio API ==============

@main_bp.route('/api/portfolio', methods=['GET'])
def api_get_portfolio():
    """Get portfolio pieces."""
    status = request.args.get('status')
    medium = request.args.get('medium')
    result = get_portfolio(status=status, medium=medium)
    return jsonify(result)


@main_bp.route('/api/portfolio/stats', methods=['GET'])
def api_portfolio_stats():
    """Get portfolio statistics."""
    result = get_portfolio_stats()
    return jsonify(result)


@main_bp.route('/api/portfolio/upload', methods=['POST'])
def api_upload_artwork():
    """Upload an artwork image."""
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No image provided"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join('data/portfolio', filename)
        os.makedirs('data/portfolio', exist_ok=True)
        file.save(filepath)

        return jsonify({
            "success": True,
            "image_path": filepath
        })

    return jsonify({"success": False, "error": "Invalid file type"}), 400


# ============== Dashboard API ==============

@main_bp.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    """Get dashboard summary data."""
    supplies = get_all_supplies()
    projects = get_all_projects()
    portfolio = get_portfolio_stats()

    return jsonify({
        "success": True,
        "supplies": {
            "total": supplies.get("total", 0),
            "low_stock": supplies.get("summary", {}).get("low", 0) + supplies.get("summary", {}).get("empty", 0),
            "summary": supplies.get("summary", {})
        },
        "projects": {
            "total": projects.get("total", 0),
            "active": len([p for p in projects.get("projects", []) if p.get("status") == "in_progress"])
        },
        "portfolio": portfolio.get("stats", {})
    })


# ============== Quick Actions ==============

@main_bp.route('/api/quick-action/new-project', methods=['POST'])
def quick_new_project():
    """Quick action to start a new project."""
    data = request.get_json()
    idea = data.get('idea', 'new art project')

    result = create_project_from_query(query=idea)

    return jsonify({
        "success": True,
        "action": "new_project",
        "suggestion": result.get("suggested_project", {}),
        "message": f"Here's a project plan for: {idea}"
    })


@main_bp.route('/api/quick-action/check-supplies', methods=['GET'])
def quick_check_supplies():
    """Quick action to check low supplies."""
    result = get_low_stock_supplies()

    low_count = result.get("total_low_stock", 0)
    message = f"You have {low_count} items running low." if low_count > 0 else "All supplies are well stocked!"

    return jsonify({
        "success": True,
        "action": "check_supplies",
        "low_stock": result.get("supplies", []),
        "shopping_list": result.get("shopping_list", []),
        "message": message
    })
