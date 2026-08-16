from rest_framework.permissions import BasePermission


class IsProfileOwnerOrFamilyMember(BasePermission):
    """
    Object-level permission: only the owner of a financial profile, or a
    family member with sufficient role, can read/write objects scoped to it.
    This is enforced here — server-side — regardless of what the frontend
    shows or hides. Never rely on frontend checks for financial data access.
    """

    def has_object_permission(self, request, view, obj):
        profile = getattr(obj, "profile", obj)
        user = request.user

        if profile.owner_id == user.id:
            return True

        family = getattr(profile, "family", None)
        if family is None:
            return False

        membership = family.memberships.filter(user=user, deleted_at__isnull=True).first()
        if membership is None:
            return False

        if request.method in ("GET", "HEAD", "OPTIONS"):
            return membership.role in ("owner", "administrator", "member", "viewer")

        return membership.role in ("owner", "administrator", "member")
