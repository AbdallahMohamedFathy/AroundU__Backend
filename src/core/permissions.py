def require_admin(user):
    """Raise PermissionError if user is not an admin."""
    if user.role != "ADMIN":
        raise PermissionError("Admin access required")


def require_owner_or_admin(user):
    """Raise PermissionError if user is neither an admin nor an owner."""
    if user.role not in ["ADMIN", "OWNER"]:
        raise PermissionError("Owner or Admin access required")


def require_place_owner_or_admin(user, place):
    """
    Raise PermissionError if user is not an admin 
    AND is not the owner of the specific place.
    """
    if user.role == "ADMIN":
        return
    if place.owner_id == user.id:
        return
    raise PermissionError("Not authorized for this place")
