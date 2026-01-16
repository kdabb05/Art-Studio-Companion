"""Pinterest Inspiration Tool - Fetch boards and curated images for art inspiration."""

import os
import json
import requests
from typing import Optional
from app.models.database import SessionLocal, StylePreference


PINTEREST_API_BASE = "https://api.pinterest.com/v5"


def _get_pinterest_headers():
    """Get Pinterest API headers with access token."""
    token = os.getenv("PINTEREST_ACCESS_TOKEN")
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


def get_pinterest_boards(username: Optional[str] = None) -> dict:
    """
    Fetch Pinterest boards for a user.

    Args:
        username: Pinterest username. If not provided, fetches boards for authenticated user.

    Returns:
        Dictionary containing boards list or error message.
    """
    headers = _get_pinterest_headers()

    if not headers:
        # Return mock data when no API key is configured
        return {
            "success": True,
            "source": "mock",
            "boards": [
                {"id": "1", "name": "Watercolor Landscapes", "pin_count": 45, "description": "Beautiful watercolor landscape inspiration"},
                {"id": "2", "name": "Botanical Art", "pin_count": 32, "description": "Flowers, plants, and nature studies"},
                {"id": "3", "name": "Color Palettes", "pin_count": 28, "description": "Color combinations and schemes"},
                {"id": "4", "name": "Brush Techniques", "pin_count": 19, "description": "Brushwork and texture techniques"}
            ],
            "message": "Using mock data. Configure PINTEREST_ACCESS_TOKEN for real data."
        }

    try:
        if username:
            response = requests.get(
                f"{PINTEREST_API_BASE}/users/{username}/boards",
                headers=headers
            )
        else:
            response = requests.get(
                f"{PINTEREST_API_BASE}/boards",
                headers=headers
            )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "source": "pinterest_api",
                "boards": data.get("items", [])
            }
        else:
            return {
                "success": False,
                "error": f"Pinterest API error: {response.status_code}",
                "message": response.text
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def search_pinterest_inspiration(
    query: str,
    board_id: Optional[str] = None,
    limit: int = 10
) -> dict:
    """
    Search for art inspiration on Pinterest based on project theme.

    Args:
        query: Search query (e.g., "watercolor sunflower landscape")
        board_id: Optional board ID to search within
        limit: Maximum number of results to return

    Returns:
        Dictionary containing curated images and style analysis.
    """
    headers = _get_pinterest_headers()

    if not headers:
        # Return mock inspiration data
        mock_results = _generate_mock_inspiration(query, limit)
        return {
            "success": True,
            "source": "mock",
            "query": query,
            "results": mock_results,
            "style_analysis": _analyze_mock_style(query),
            "message": "Using mock data. Configure PINTEREST_ACCESS_TOKEN for real Pinterest results."
        }

    try:
        params = {
            "query": query,
            "limit": limit
        }

        response = requests.get(
            f"{PINTEREST_API_BASE}/search/pins",
            headers=headers,
            params=params
        )

        if response.status_code == 200:
            data = response.json()
            pins = data.get("items", [])

            # Extract relevant information from pins
            results = []
            for pin in pins:
                results.append({
                    "id": pin.get("id"),
                    "title": pin.get("title", "Untitled"),
                    "description": pin.get("description", ""),
                    "image_url": pin.get("media", {}).get("images", {}).get("originals", {}).get("url"),
                    "link": pin.get("link"),
                    "dominant_color": pin.get("dominant_color")
                })

            return {
                "success": True,
                "source": "pinterest_api",
                "query": query,
                "results": results,
                "style_analysis": _analyze_pinterest_style(results)
            }
        else:
            return {
                "success": False,
                "error": f"Pinterest API error: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _generate_mock_inspiration(query: str, limit: int) -> list:
    """Generate mock inspiration results based on query."""
    query_lower = query.lower()

    # Base mock results
    results = []

    if "watercolor" in query_lower:
        results.extend([
            {"title": "Loose Watercolor Landscape", "description": "Soft washes with wet-on-wet technique", "style_tags": ["loose", "wet-on-wet", "atmospheric"]},
            {"title": "Watercolor Sunset Study", "description": "Warm gradient washes", "style_tags": ["gradient", "warm colors", "sky"]},
        ])

    if "landscape" in query_lower:
        results.extend([
            {"title": "Mountain Vista", "description": "Layered mountain ranges with atmospheric perspective", "style_tags": ["depth", "atmospheric", "nature"]},
            {"title": "Coastal Scene", "description": "Ocean waves and rocky shoreline", "style_tags": ["seascape", "texture", "movement"]},
        ])

    if "sunflower" in query_lower or "flower" in query_lower:
        results.extend([
            {"title": "Sunflower Field", "description": "Bold yellows against blue sky", "style_tags": ["botanical", "bright", "contrast"]},
            {"title": "Floral Study", "description": "Detailed petal work with soft shadows", "style_tags": ["botanical", "detailed", "realistic"]},
        ])

    # Add generic art inspiration if we don't have enough
    while len(results) < limit:
        results.append({
            "title": f"Art Inspiration #{len(results) + 1}",
            "description": f"Curated inspiration for: {query}",
            "style_tags": ["inspiration", "art", "creative"]
        })

    return results[:limit]


def _analyze_mock_style(query: str) -> dict:
    """Analyze style preferences from mock query."""
    query_lower = query.lower()

    analysis = {
        "suggested_techniques": [],
        "color_palette": [],
        "mood": [],
        "difficulty": "intermediate"
    }

    if "watercolor" in query_lower:
        analysis["suggested_techniques"].extend(["wet-on-wet", "glazing", "lifting"])
        analysis["color_palette"].extend(["transparent washes", "soft edges"])

    if "landscape" in query_lower:
        analysis["suggested_techniques"].append("atmospheric perspective")
        analysis["mood"].append("serene")

    if "sunflower" in query_lower:
        analysis["color_palette"].extend(["cadmium yellow", "burnt sienna", "ultramarine blue"])
        analysis["mood"].append("cheerful")

    return analysis


def _analyze_pinterest_style(pins: list) -> dict:
    """Analyze style preferences from Pinterest pins."""
    colors = []
    themes = []

    for pin in pins:
        if pin.get("dominant_color"):
            colors.append(pin["dominant_color"])
        if pin.get("description"):
            themes.append(pin["description"])

    return {
        "dominant_colors": list(set(colors))[:5],
        "common_themes": themes[:5],
        "pin_count": len(pins)
    }


def analyze_style_preferences(save_to_db: bool = True) -> dict:
    """
    Analyze and return the user's inferred style preferences.

    Args:
        save_to_db: Whether to save new preferences to database

    Returns:
        Dictionary of style preferences by category.
    """
    db = SessionLocal()
    try:
        preferences = db.query(StylePreference).all()

        # Organize by category
        organized = {}
        for pref in preferences:
            if pref.category not in organized:
                organized[pref.category] = []
            organized[pref.category].append({
                "value": pref.value,
                "confidence": pref.confidence,
                "source": pref.source
            })

        # Sort by confidence within each category
        for category in organized:
            organized[category].sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "success": True,
            "preferences": organized,
            "total_preferences": len(preferences)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def save_style_preference(category: str, value: str, confidence: float = 0.5, source: str = "chat") -> dict:
    """
    Save a new style preference to the database.

    Args:
        category: Preference category (color_palette, brushwork, subject, mood)
        value: The preference value
        confidence: Confidence score 0-1
        source: Where this preference was inferred from

    Returns:
        Success status and preference details.
    """
    db = SessionLocal()
    try:
        # Check if preference already exists
        existing = db.query(StylePreference).filter(
            StylePreference.category == category,
            StylePreference.value == value
        ).first()

        if existing:
            # Update confidence (increase slightly for repeated mentions)
            existing.confidence = min(1.0, existing.confidence + 0.1)
            db.commit()
            return {
                "success": True,
                "action": "updated",
                "preference": existing.to_dict()
            }
        else:
            # Create new preference
            pref = StylePreference(
                category=category,
                value=value,
                confidence=confidence,
                source=source
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
            return {
                "success": True,
                "action": "created",
                "preference": pref.to_dict()
            }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()
