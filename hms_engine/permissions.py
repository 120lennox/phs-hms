"""
hms_engine/permissions.py
─────────────────────────────────────────────────────────
Custom DRF permission classes for the Pulse HMS API.
"""
from rest_framework.permissions import BasePermission


class IsHospitalAdmin(BasePermission):
    """
    Grants access if the authenticated user is a Django staff member
    (is_staff=True) OR has at least one hospital they created.

    This covers the case where an admin account was created before the
    HospitalAdminRegisterSerializer set is_staff=True automatically.
    """

    message = "You must be a hospital administrator to perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Primary check: standard Django is_staff flag
        if request.user.is_staff:
            return True

        # Fallback: user created at least one hospital
        # (covers legacy admins who pre-date the is_staff enforcement)
        return request.user.created_hospitals.exists()
