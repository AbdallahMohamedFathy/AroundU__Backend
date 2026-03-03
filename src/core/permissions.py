def require_admin(user):
    """Raise PermissionError if user is not an admin."""
    if not user.is_admin:
        raise PermissionError("Admin access required")


def require_owner_or_admin(user):
    """Raise PermissionError if user is neither an admin nor an owner."""
    if not (user.is_admin or user.is_owner):
        raise PermissionError("Owner or Admin access required")


def require_place_owner_or_admin(user, place):
    """
    Raise PermissionError if user is not an admin 
    AND is not the owner of the specific place.
    """
    if user.is_admin:
        return
    if place.owner_id == user.id:
        return
    raise PermissionError("Not authorized for this place")
