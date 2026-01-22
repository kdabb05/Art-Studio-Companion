"""Project Filesaver Tool - Save and manage art project plans."""

import os
import json
from typing import Optional
from datetime import datetime
from app.models.database import SessionLocal, Project, Supply


PROJECTS_DIR = "data/projects"


def _ensure_projects_dir():
    """Ensure projects directory exists."""
    os.makedirs(PROJECTS_DIR, exist_ok=True)


def get_all_projects(status: Optional[str] = None, limit: int = 50) -> dict:
    """
    Get all projects, optionally filtered by status.

    Args:
        status: Filter by status (planned, in_progress, completed)
        limit: Maximum number of results

    Returns:
        Dictionary containing projects list.
    """
    db = SessionLocal()
    try:
        query = db.query(Project)

        if status:
            query = query.filter(Project.status == status)

        projects = query.order_by(Project.updated_at.desc()).limit(limit).all()

        return {
            "success": True,
            "total": len(projects),
            "projects": [p.to_dict() for p in projects]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def get_project(project_id: int) -> dict:
    """
    Get a specific project by ID with full details.

    Args:
        project_id: The project ID

    Returns:
        Dictionary containing project details.
    """
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {
                "success": False,
                "error": "Project not found"
            }

        project_dict = project.to_dict()

        # Parse JSON fields
        if project.materials_list:
            try:
                project_dict["materials_list"] = json.loads(project.materials_list)
            except json.JSONDecodeError:
                pass

        if project.steps:
            try:
                project_dict["steps"] = json.loads(project.steps)
            except json.JSONDecodeError:
                pass

        return {
            "success": True,
            "project": project_dict
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def create_project(
    title: str,
    description: Optional[str] = None,
    medium: Optional[str] = None,
    style: Optional[str] = None,
    estimated_budget: Optional[float] = None,
    materials_list: Optional[list] = None,
    steps: Optional[list] = None,
    notes: Optional[str] = None
) -> dict:
    """
    Create a new art project.

    Args:
        title: Project title
        description: Project description
        medium: Art medium (watercolor, oil, acrylic, etc.)
        style: Art style (landscape, portrait, abstract, etc.)
        estimated_budget: Estimated cost
        materials_list: List of required materials
        steps: List of project steps
        notes: Additional notes

    Returns:
        Dictionary with created project details.
    """
    db = SessionLocal()
    try:
        project = Project(
            title=title,
            description=description,
            medium=medium,
            style=style,
            estimated_budget=estimated_budget,
            materials_list=json.dumps(materials_list) if materials_list else None,
            steps=json.dumps(steps) if steps else None,
            notes=notes,
            status="planned"
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        return {
            "success": True,
            "message": f"Created project: {title}",
            "project": project.to_dict()
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def update_project(
    project_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    materials_list: Optional[list] = None,
    steps: Optional[list] = None,
    notes: Optional[str] = None,
    actual_budget: Optional[float] = None,
    **kwargs
) -> dict:
    """
    Update an existing project.

    Args:
        project_id: The project ID
        title: New title (optional)
        description: New description (optional)
        status: New status (optional)
        materials_list: Updated materials list (optional)
        steps: Updated steps (optional)
        notes: Updated notes (optional)
        actual_budget: Actual spent budget (optional)
        **kwargs: Other fields to update

    Returns:
        Dictionary with updated project details.
    """
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {
                "success": False,
                "error": "Project not found"
            }

        # Update fields
        if title is not None:
            project.title = title
        if description is not None:
            project.description = description
        if status is not None:
            old_status = project.status
            project.status = status
            if status == "completed" and old_status != "completed":
                project.completed_at = datetime.utcnow()
        if materials_list is not None:
            project.materials_list = json.dumps(materials_list)
        if steps is not None:
            project.steps = json.dumps(steps)
        if notes is not None:
            project.notes = notes
        if actual_budget is not None:
            project.actual_budget = actual_budget

        # Update any additional fields
        for key, value in kwargs.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)

        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)

        return {
            "success": True,
            "message": f"Updated project: {project.title}",
            "project": project.to_dict()
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def save_project_to_file(project_id: int) -> dict:
    """
    Save a project's complete details to a file.

    Args:
        project_id: The project ID

    Returns:
        Dictionary with file path and success status.
    """
    _ensure_projects_dir()

    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {
                "success": False,
                "error": "Project not found"
            }

        # Create filename
        safe_title = "".join(c for c in project.title if c.isalnum() or c in " -_").strip()
        safe_title = safe_title.replace(" ", "_")[:50]
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{safe_title}_{timestamp}.json"
        filepath = os.path.join(PROJECTS_DIR, filename)

        # Prepare project data
        project_data = {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "status": project.status,
            "medium": project.medium,
            "style": project.style,
            "estimated_budget": project.estimated_budget,
            "actual_budget": project.actual_budget,
            "materials_list": json.loads(project.materials_list) if project.materials_list else [],
            "steps": json.loads(project.steps) if project.steps else [],
            "notes": project.notes,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "completed_at": project.completed_at.isoformat() if project.completed_at else None,
            "exported_at": datetime.utcnow().isoformat()
        }

        # Write to file
        with open(filepath, "w") as f:
            json.dump(project_data, f, indent=2)

        # Update project with file path
        project.file_path = filepath
        db.commit()

        return {
            "success": True,
            "message": f"Saved project to {filepath}",
            "file_path": filepath,
            "project": project.to_dict()
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def generate_shopping_list(project_id: int) -> dict:
    """
    Generate a shopping list for a project based on required materials
    and current inventory.

    Args:
        project_id: The project ID

    Returns:
        Dictionary with shopping list items.
    """
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {
                "success": False,
                "error": "Project not found"
            }

        if not project.materials_list:
            return {
                "success": True,
                "project": project.title,
                "shopping_list": [],
                "message": "No materials list defined for this project"
            }

        # Parse materials list
        try:
            materials = json.loads(project.materials_list)
        except json.JSONDecodeError:
            materials = []

        # Get current inventory
        supplies = db.query(Supply).all()
        supply_map = {}
        for s in supplies:
            key = f"{s.name}_{s.brand}".lower() if s.brand else s.name.lower()
            supply_map[key] = s

        # Check each material
        shopping_list = []
        have_list = []
        estimated_cost = 0

        for material in materials:
            material_name = material.get("name", "") if isinstance(material, dict) else str(material)
            material_lower = material_name.lower()

            # Try to find in inventory
            found = None
            for key, supply in supply_map.items():
                if material_lower in key or key in material_lower:
                    found = supply
                    break

            if found:
                if found.quantity < 0.25:
                    shopping_list.append({
                        "item": material_name,
                        "reason": "low stock",
                        "current_quantity": found.quantity,
                        "brand": found.brand
                    })
                else:
                    have_list.append({
                        "item": material_name,
                        "quantity": found.quantity,
                        "brand": found.brand
                    })
            else:
                shopping_list.append({
                    "item": material_name,
                    "reason": "not in inventory",
                    "current_quantity": 0
                })

        return {
            "success": True,
            "project": project.title,
            "shopping_list": shopping_list,
            "already_have": have_list,
            "items_to_buy": len(shopping_list),
            "items_available": len(have_list),
            "estimated_budget": project.estimated_budget
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def create_project_from_query(
    query: str,
    available_supplies: Optional[list] = None,
    budget: Optional[float] = None,
    style_preferences: Optional[dict] = None
) -> dict:
    """
    Create a project plan from a natural language query.

    This is a helper that structures a project based on user input.
    The actual project creation is done by create_project.

    Args:
        query: Natural language project description
        available_supplies: List of available supplies to consider
        budget: Maximum budget constraint
        style_preferences: User's style preferences

    Returns:
        Dictionary with suggested project structure.
    """
    query_lower = query.lower()

    # Parse medium from query
    medium = None
    mediums = ["watercolor", "oil", "acrylic", "pencil", "ink", "pastel", "charcoal", "mixed media"]
    for m in mediums:
        if m in query_lower:
            medium = m
            break

    # Parse style from query
    style = None
    styles = ["landscape", "portrait", "still life", "abstract", "botanical", "seascape", "cityscape"]
    for s in styles:
        if s in query_lower:
            style = s
            break

    # Extract subject if mentioned
    subject = None
    subjects = ["sunflower", "flower", "mountain", "ocean", "tree", "bird", "sunset", "forest"]
    for s in subjects:
        if s in query_lower:
            subject = s
            break

    # Build suggested materials based on medium
    materials = []
    if medium == "watercolor":
        materials = [
            {"name": "Watercolor paper", "category": "paper"},
            {"name": "Round brush #6", "category": "brush"},
            {"name": "Flat brush 1 inch", "category": "brush"},
            {"name": "Primary colors set", "category": "paint"}
        ]
    elif medium == "oil":
        materials = [
            {"name": "Stretched canvas", "category": "canvas"},
            {"name": "Oil paint set", "category": "paint"},
            {"name": "Linseed oil", "category": "medium"},
            {"name": "Filbert brush set", "category": "brush"}
        ]
    elif medium == "acrylic":
        materials = [
            {"name": "Canvas board", "category": "canvas"},
            {"name": "Acrylic paint set", "category": "paint"},
            {"name": "Flat brush set", "category": "brush"}
        ]

    # Build suggested steps
    steps = [
        {"step": 1, "description": "Gather reference images and plan composition"},
        {"step": 2, "description": "Sketch initial composition"},
        {"step": 3, "description": "Block in main shapes and values"},
        {"step": 4, "description": "Add details and refine"},
        {"step": 5, "description": "Final touches and evaluation"}
    ]

    # Build project title
    title_parts = []
    if subject:
        title_parts.append(subject.title())
    if style:
        title_parts.append(style.title())
    if medium:
        title_parts.append(f"in {medium.title()}")

    title = " ".join(title_parts) if title_parts else "New Art Project"

    return {
        "success": True,
        "suggested_project": {
            "title": title,
            "description": query,
            "medium": medium,
            "style": style,
            "subject": subject,
            "materials_list": materials,
            "steps": steps,
            "estimated_budget": budget
        },
        "parsed_from_query": {
            "medium": medium,
            "style": style,
            "subject": subject,
            "budget_constraint": budget
        }
    }


def add_session_notes(project_id: int, notes: str) -> dict:
    """
    Add session notes to a project.

    Args:
        project_id: The project ID
        notes: Notes from the session

    Returns:
        Dictionary with updated project.
    """
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {
                "success": False,
                "error": "Project not found"
            }

        # Append to existing notes with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_note = f"\n\n[{timestamp}]\n{notes}"

        if project.notes:
            project.notes = project.notes + new_note
        else:
            project.notes = f"[{timestamp}]\n{notes}"

        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)

        return {
            "success": True,
            "message": "Added session notes",
            "project": project.to_dict()
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()
