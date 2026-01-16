"""Portfolio Storehouse Tool - Store and manage artwork portfolio."""

import os
import json
import shutil
from typing import Optional
from datetime import datetime
from werkzeug.utils import secure_filename
from app.models.database import SessionLocal, PortfolioPiece


PORTFOLIO_DIR = "data/portfolio"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _ensure_portfolio_dir():
    """Ensure portfolio directory exists."""
    os.makedirs(PORTFOLIO_DIR, exist_ok=True)
    os.makedirs(os.path.join(PORTFOLIO_DIR, "thumbnails"), exist_ok=True)
    os.makedirs(os.path.join(PORTFOLIO_DIR, "progress"), exist_ok=True)


def get_portfolio(
    status: Optional[str] = None,
    medium: Optional[str] = None,
    limit: int = 50
) -> dict:
    """
    Get all portfolio pieces, optionally filtered.

    Args:
        status: Filter by status (sketch, wip, completed)
        medium: Filter by medium (watercolor, oil, etc.)
        limit: Maximum number of results

    Returns:
        Dictionary containing portfolio pieces.
    """
    db = SessionLocal()
    try:
        query = db.query(PortfolioPiece)

        if status:
            query = query.filter(PortfolioPiece.status == status)
        if medium:
            query = query.filter(PortfolioPiece.medium == medium)

        pieces = query.order_by(PortfolioPiece.updated_at.desc()).limit(limit).all()

        # Group by status
        by_status = {
            "sketch": [],
            "wip": [],
            "completed": []
        }

        piece_list = []
        for piece in pieces:
            piece_dict = piece.to_dict()
            piece_list.append(piece_dict)
            if piece.status in by_status:
                by_status[piece.status].append(piece_dict)

        return {
            "success": True,
            "total": len(pieces),
            "pieces": piece_list,
            "by_status": by_status,
            "summary": {
                "sketches": len(by_status["sketch"]),
                "works_in_progress": len(by_status["wip"]),
                "completed": len(by_status["completed"])
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def get_portfolio_piece(piece_id: int) -> dict:
    """
    Get a specific portfolio piece by ID.

    Args:
        piece_id: The portfolio piece ID

    Returns:
        Dictionary containing piece details and progress images.
    """
    db = SessionLocal()
    try:
        piece = db.query(PortfolioPiece).filter(PortfolioPiece.id == piece_id).first()

        if not piece:
            return {
                "success": False,
                "error": "Portfolio piece not found"
            }

        piece_dict = piece.to_dict()

        # Parse progress images JSON if present
        if piece.progress_images:
            try:
                piece_dict["progress_images"] = json.loads(piece.progress_images)
            except json.JSONDecodeError:
                piece_dict["progress_images"] = []

        return {
            "success": True,
            "piece": piece_dict
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def add_portfolio_piece(
    title: str,
    description: Optional[str] = None,
    project_id: Optional[int] = None,
    status: str = "sketch",
    medium: Optional[str] = None,
    dimensions: Optional[str] = None,
    image_path: Optional[str] = None
) -> dict:
    """
    Add a new piece to the portfolio.

    Args:
        title: Title of the artwork
        description: Description of the piece
        project_id: Optional associated project ID
        status: Current status (sketch, wip, completed)
        medium: Art medium used
        dimensions: Physical dimensions (e.g., "8x10 inches")
        image_path: Path to the main image file

    Returns:
        Dictionary with created piece details.
    """
    _ensure_portfolio_dir()
    db = SessionLocal()

    try:
        # Handle image path
        final_image_path = None
        thumbnail_path = None

        if image_path and os.path.exists(image_path):
            # Copy image to portfolio directory
            filename = secure_filename(os.path.basename(image_path))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{timestamp}_{filename}"
            final_image_path = os.path.join(PORTFOLIO_DIR, new_filename)
            shutil.copy2(image_path, final_image_path)

            # Create thumbnail path (actual thumbnail generation would need Pillow)
            thumbnail_path = os.path.join(PORTFOLIO_DIR, "thumbnails", new_filename)

        piece = PortfolioPiece(
            title=title,
            description=description,
            project_id=project_id,
            status=status,
            medium=medium,
            dimensions=dimensions,
            image_path=final_image_path,
            thumbnail_path=thumbnail_path,
            progress_images="[]"
        )

        db.add(piece)
        db.commit()
        db.refresh(piece)

        return {
            "success": True,
            "message": f"Added '{title}' to portfolio",
            "piece": piece.to_dict()
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def update_portfolio_piece(
    piece_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    image_path: Optional[str] = None,
    **kwargs
) -> dict:
    """
    Update an existing portfolio piece.

    Args:
        piece_id: The piece ID to update
        title: New title (optional)
        description: New description (optional)
        status: New status (optional)
        image_path: New main image path (optional)
        **kwargs: Other fields to update

    Returns:
        Dictionary with updated piece details.
    """
    db = SessionLocal()
    try:
        piece = db.query(PortfolioPiece).filter(PortfolioPiece.id == piece_id).first()

        if not piece:
            return {
                "success": False,
                "error": "Portfolio piece not found"
            }

        # Update fields
        if title is not None:
            piece.title = title
        if description is not None:
            piece.description = description
        if status is not None:
            old_status = piece.status
            piece.status = status
            # Set completed_at if status changed to completed
            if status == "completed" and old_status != "completed":
                piece.completed_at = datetime.utcnow()

        # Handle new image
        if image_path and os.path.exists(image_path):
            _ensure_portfolio_dir()
            filename = secure_filename(os.path.basename(image_path))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{timestamp}_{filename}"
            final_path = os.path.join(PORTFOLIO_DIR, new_filename)
            shutil.copy2(image_path, final_path)
            piece.image_path = final_path

        # Update any additional fields
        for key, value in kwargs.items():
            if hasattr(piece, key) and value is not None:
                setattr(piece, key, value)

        piece.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(piece)

        return {
            "success": True,
            "message": f"Updated '{piece.title}'",
            "piece": piece.to_dict()
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def add_progress_image(
    piece_id: int,
    image_path: str,
    description: Optional[str] = None
) -> dict:
    """
    Add a progress image to a portfolio piece.

    Args:
        piece_id: The piece ID
        image_path: Path to the progress image
        description: Description of this progress stage

    Returns:
        Dictionary with updated piece and progress images.
    """
    if not os.path.exists(image_path):
        return {
            "success": False,
            "error": f"Image file not found: {image_path}"
        }

    _ensure_portfolio_dir()
    db = SessionLocal()

    try:
        piece = db.query(PortfolioPiece).filter(PortfolioPiece.id == piece_id).first()

        if not piece:
            return {
                "success": False,
                "error": "Portfolio piece not found"
            }

        # Copy progress image
        filename = secure_filename(os.path.basename(image_path))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"progress_{piece_id}_{timestamp}_{filename}"
        progress_path = os.path.join(PORTFOLIO_DIR, "progress", new_filename)
        shutil.copy2(image_path, progress_path)

        # Update progress images list
        progress_images = []
        if piece.progress_images:
            try:
                progress_images = json.loads(piece.progress_images)
            except json.JSONDecodeError:
                progress_images = []

        progress_images.append({
            "path": progress_path,
            "description": description,
            "added_at": datetime.utcnow().isoformat()
        })

        piece.progress_images = json.dumps(progress_images)
        piece.updated_at = datetime.utcnow()

        # Update status to WIP if it was just a sketch
        if piece.status == "sketch":
            piece.status = "wip"

        db.commit()
        db.refresh(piece)

        return {
            "success": True,
            "message": "Added progress image",
            "piece": piece.to_dict(),
            "progress_count": len(progress_images)
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def delete_portfolio_piece(piece_id: int, delete_files: bool = False) -> dict:
    """
    Delete a portfolio piece.

    Args:
        piece_id: The piece ID to delete
        delete_files: Whether to also delete associated image files

    Returns:
        Success status.
    """
    db = SessionLocal()
    try:
        piece = db.query(PortfolioPiece).filter(PortfolioPiece.id == piece_id).first()

        if not piece:
            return {
                "success": False,
                "error": "Portfolio piece not found"
            }

        title = piece.title

        # Optionally delete files
        if delete_files:
            if piece.image_path and os.path.exists(piece.image_path):
                os.remove(piece.image_path)
            if piece.thumbnail_path and os.path.exists(piece.thumbnail_path):
                os.remove(piece.thumbnail_path)
            if piece.progress_images:
                try:
                    for img in json.loads(piece.progress_images):
                        if os.path.exists(img.get("path", "")):
                            os.remove(img["path"])
                except (json.JSONDecodeError, KeyError):
                    pass

        db.delete(piece)
        db.commit()

        return {
            "success": True,
            "message": f"Deleted '{title}' from portfolio"
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def get_portfolio_stats() -> dict:
    """
    Get portfolio statistics and insights.

    Returns:
        Dictionary with portfolio statistics.
    """
    db = SessionLocal()
    try:
        pieces = db.query(PortfolioPiece).all()

        # Gather stats
        stats = {
            "total_pieces": len(pieces),
            "by_status": {"sketch": 0, "wip": 0, "completed": 0},
            "by_medium": {},
            "recent_completed": [],
            "active_wips": []
        }

        for piece in pieces:
            # Status counts
            if piece.status in stats["by_status"]:
                stats["by_status"][piece.status] += 1

            # Medium counts
            medium = piece.medium or "unspecified"
            stats["by_medium"][medium] = stats["by_medium"].get(medium, 0) + 1

            # Recent completed
            if piece.status == "completed" and piece.completed_at:
                stats["recent_completed"].append({
                    "id": piece.id,
                    "title": piece.title,
                    "completed_at": piece.completed_at.isoformat()
                })

            # Active WIPs
            if piece.status == "wip":
                stats["active_wips"].append({
                    "id": piece.id,
                    "title": piece.title,
                    "updated_at": piece.updated_at.isoformat() if piece.updated_at else None
                })

        # Sort recent completed by date
        stats["recent_completed"].sort(key=lambda x: x["completed_at"], reverse=True)
        stats["recent_completed"] = stats["recent_completed"][:5]

        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()
