"""Supply Inventory Manager Tool - Track and manage art supplies."""

import os
import json
import base64
from typing import Optional
from datetime import datetime
from app.models.database import SessionLocal, Supply, SupplyUsage


def get_all_supplies(category: Optional[str] = None) -> dict:
    """
    Get all supplies in inventory, optionally filtered by category.

    Args:
        category: Optional category filter (paint, brush, canvas, paper, etc.)

    Returns:
        Dictionary containing list of supplies with status.
    """
    db = SessionLocal()
    try:
        query = db.query(Supply)
        if category:
            query = query.filter(Supply.category == category)

        supplies = query.order_by(Supply.category, Supply.name).all()

        # Group by status for easy display
        grouped = {
            "green": [],  # plenty
            "yellow": [],  # low
            "red": []  # empty
        }

        supply_list = []
        for supply in supplies:
            supply_dict = supply.to_dict()
            supply_list.append(supply_dict)
            grouped[supply_dict["status"]].append(supply_dict)

        return {
            "success": True,
            "total": len(supplies),
            "supplies": supply_list,
            "by_status": grouped,
            "summary": {
                "plenty": len(grouped["green"]),
                "low": len(grouped["yellow"]),
                "empty": len(grouped["red"])
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def get_supply_by_id(supply_id: int) -> dict:
    """
    Get a specific supply by ID.

    Args:
        supply_id: The supply ID

    Returns:
        Dictionary containing supply details.
    """
    db = SessionLocal()
    try:
        supply = db.query(Supply).filter(Supply.id == supply_id).first()
        if supply:
            return {
                "success": True,
                "supply": supply.to_dict()
            }
        return {
            "success": False,
            "error": "Supply not found"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def add_supply(
    name: str,
    category: str,
    brand: Optional[str] = None,
    color: Optional[str] = None,
    size: Optional[str] = None,
    quantity: float = 1.0,
    unit: str = "piece",
    notes: Optional[str] = None
) -> dict:
    """
    Add a new supply to inventory.

    Args:
        name: Supply name (e.g., "Cadmium Yellow")
        category: Category (paint, brush, canvas, paper, medium, tool)
        brand: Brand name (e.g., "Winsor & Newton")
        color: Color name for paints/inks
        size: Size (e.g., "#6" for brushes, "8x10" for canvas)
        quantity: Amount (1.0 = full, 0.5 = half)
        unit: Unit type (tube, bottle, sheet, piece)
        notes: Additional notes

    Returns:
        Dictionary with created supply details.
    """
    db = SessionLocal()
    try:
        supply = Supply(
            name=name,
            category=category,
            brand=brand,
            color=color,
            size=size,
            quantity=quantity,
            unit=unit,
            notes=notes
        )
        db.add(supply)
        db.commit()
        db.refresh(supply)

        return {
            "success": True,
            "message": f"Added {name} to inventory",
            "supply": supply.to_dict()
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def update_supply(
    supply_id: int,
    name: Optional[str] = None,
    quantity: Optional[float] = None,
    notes: Optional[str] = None,
    **kwargs
) -> dict:
    """
    Update an existing supply.

    Args:
        supply_id: The supply ID to update
        name: New name (optional)
        quantity: New quantity (optional)
        notes: New notes (optional)
        **kwargs: Other fields to update

    Returns:
        Dictionary with updated supply details.
    """
    db = SessionLocal()
    try:
        supply = db.query(Supply).filter(Supply.id == supply_id).first()
        if not supply:
            return {
                "success": False,
                "error": "Supply not found"
            }

        # Update provided fields
        if name is not None:
            supply.name = name
        if quantity is not None:
            supply.quantity = max(0, min(1, quantity))  # Clamp between 0 and 1
        if notes is not None:
            supply.notes = notes

        # Update any additional fields
        for key, value in kwargs.items():
            if hasattr(supply, key) and value is not None:
                setattr(supply, key, value)

        supply.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(supply)

        return {
            "success": True,
            "message": f"Updated {supply.name}",
            "supply": supply.to_dict()
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def get_low_stock_supplies(threshold: float = 0.25) -> dict:
    """
    Get all supplies that are low or empty.

    Args:
        threshold: Quantity threshold for "low" (default 0.25)

    Returns:
        Dictionary containing low stock supplies grouped by category.
    """
    db = SessionLocal()
    try:
        supplies = db.query(Supply).filter(
            Supply.quantity <= threshold
        ).order_by(Supply.quantity, Supply.category).all()

        # Group by category
        by_category = {}
        for supply in supplies:
            cat = supply.category or "uncategorized"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(supply.to_dict())

        # Create shopping suggestions
        shopping_list = []
        for supply in supplies:
            shopping_list.append({
                "name": supply.name,
                "brand": supply.brand,
                "category": supply.category,
                "current_quantity": supply.quantity,
                "urgency": "critical" if supply.quantity < 0.1 else "low"
            })

        return {
            "success": True,
            "total_low_stock": len(supplies),
            "supplies": [s.to_dict() for s in supplies],
            "by_category": by_category,
            "shopping_list": shopping_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def use_supply(supply_id: int, amount_used: float, project_id: Optional[int] = None) -> dict:
    """
    Record usage of a supply, reducing its quantity.

    Args:
        supply_id: The supply ID
        amount_used: Amount used (0-1 scale)
        project_id: Optional project ID to associate usage with

    Returns:
        Dictionary with updated supply and usage record.
    """
    db = SessionLocal()
    try:
        supply = db.query(Supply).filter(Supply.id == supply_id).first()
        if not supply:
            return {
                "success": False,
                "error": "Supply not found"
            }

        # Calculate new quantity
        old_quantity = supply.quantity
        supply.quantity = max(0, supply.quantity - amount_used)
        supply.updated_at = datetime.utcnow()

        # Record usage
        usage = SupplyUsage(
            supply_id=supply_id,
            project_id=project_id,
            quantity_used=amount_used
        )
        db.add(usage)
        db.commit()

        # Check if supply is now low
        status_message = None
        if supply.quantity < 0.25 and old_quantity >= 0.25:
            status_message = f"⚠️ {supply.name} is now running low!"
        elif supply.quantity < 0.1:
            status_message = f"🔴 {supply.name} is almost empty!"

        return {
            "success": True,
            "supply": supply.to_dict(),
            "usage_recorded": amount_used,
            "previous_quantity": old_quantity,
            "status_alert": status_message
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def analyze_supply_photo(image_path: str) -> dict:
    """
    Analyze an uploaded photo of supplies to auto-generate inventory.

    This is a placeholder that describes what supplies are visible.
    In production, this would use an image analysis API.

    Args:
        image_path: Path to the uploaded image

    Returns:
        Dictionary with detected supplies.
    """
    # Check if file exists
    if not os.path.exists(image_path):
        return {
            "success": False,
            "error": f"Image file not found: {image_path}"
        }

    # In production, this would call an image analysis API
    # For now, return a helpful message about manual entry

    return {
        "success": True,
        "message": "Photo analysis requires an image analysis API integration.",
        "instructions": "Please describe the supplies visible in your photo, and I'll help you add them to your inventory.",
        "suggested_format": {
            "example": "I see: Winsor & Newton watercolors (half tube), Princeton #6 round brush, Arches 140lb cold press paper (5 sheets)"
        },
        "image_path": image_path
    }


def search_supplies(query: str) -> dict:
    """
    Search supplies by name, brand, or category.

    Args:
        query: Search query

    Returns:
        Dictionary with matching supplies.
    """
    db = SessionLocal()
    try:
        search_term = f"%{query}%"
        supplies = db.query(Supply).filter(
            (Supply.name.ilike(search_term)) |
            (Supply.brand.ilike(search_term)) |
            (Supply.category.ilike(search_term)) |
            (Supply.color.ilike(search_term))
        ).all()

        return {
            "success": True,
            "query": query,
            "count": len(supplies),
            "supplies": [s.to_dict() for s in supplies]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def get_supplies_for_project(medium: str, style: Optional[str] = None) -> dict:
    """
    Get available supplies suitable for a specific project type.

    Args:
        medium: Art medium (watercolor, oil, acrylic, etc.)
        style: Optional style (landscape, portrait, etc.)

    Returns:
        Dictionary with available supplies and any missing essentials.
    """
    db = SessionLocal()
    try:
        # Define essential supplies by medium
        essentials = {
            "watercolor": {
                "paint": ["yellow", "red", "blue"],
                "brush": ["round"],
                "paper": ["watercolor paper"]
            },
            "oil": {
                "paint": ["white", "yellow", "red", "blue"],
                "brush": ["flat", "filbert"],
                "canvas": ["canvas"],
                "medium": ["linseed oil", "turpentine"]
            },
            "acrylic": {
                "paint": ["white", "yellow", "red", "blue"],
                "brush": ["flat", "round"],
                "canvas": ["canvas"]
            }
        }

        # Get all supplies
        supplies = db.query(Supply).filter(Supply.quantity > 0.1).all()

        available = [s.to_dict() for s in supplies]

        # Check for missing essentials
        missing = []
        medium_essentials = essentials.get(medium.lower(), {})
        for category, items in medium_essentials.items():
            category_supplies = [s for s in supplies if s.category == category]
            for item in items:
                found = any(item.lower() in (s.name.lower() + " " + (s.color or "")) for s in category_supplies)
                if not found:
                    missing.append({"category": category, "item": item})

        return {
            "success": True,
            "medium": medium,
            "available_supplies": available,
            "missing_essentials": missing,
            "ready_to_start": len(missing) == 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()
