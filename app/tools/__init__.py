"""MCP Tools for Art Studio Companion."""

from app.tools.pinterest_inspiration import (
    get_pinterest_boards,
    search_pinterest_inspiration,
    analyze_style_preferences
)
from app.tools.supply_inventory import (
    get_all_supplies,
    get_supply_by_id,
    add_supply,
    update_supply,
    get_low_stock_supplies,
    analyze_supply_photo,
    use_supply
)
from app.tools.portfolio_storehouse import (
    get_portfolio,
    get_portfolio_piece,
    add_portfolio_piece,
    update_portfolio_piece,
    add_progress_image
)
from app.tools.project_filesaver import (
    get_all_projects,
    get_project,
    create_project,
    update_project,
    save_project_to_file,
    generate_shopping_list
)

__all__ = [
    # Pinterest
    "get_pinterest_boards",
    "search_pinterest_inspiration",
    "analyze_style_preferences",
    # Supply
    "get_all_supplies",
    "get_supply_by_id",
    "add_supply",
    "update_supply",
    "get_low_stock_supplies",
    "analyze_supply_photo",
    "use_supply",
    # Portfolio
    "get_portfolio",
    "get_portfolio_piece",
    "add_portfolio_piece",
    "update_portfolio_piece",
    "add_progress_image",
    # Project
    "get_all_projects",
    "get_project",
    "create_project",
    "update_project",
    "save_project_to_file",
    "generate_shopping_list"
]
