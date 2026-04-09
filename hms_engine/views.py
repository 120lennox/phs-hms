from hospitals.models import Hospital
from hospitals.serializers import (
    OrganizationListSerializer,
    OrganizationDetailSerializer,
    UserProfileSerializer,
)
from health_professionals.models import HealthProfessional
from health_professionals.serializers import (
    PractitionerSerializer,
    PractitionerCreateSerializer,
    PractitionerLoginSerializer,
    HealthProfessionalDetailSerializer,
)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken


# ── Hospital ──────────────────────────────────────────────────────────────────

class HospitalViewSet(viewsets.ModelViewSet):
    """
    CRUD for Hospital (FHIR Organization resource).

    list      GET  /api/hospitals/           — any authenticated user
    retrieve  GET  /api/hospitals/{id}/      — any authenticated user
    create    POST /api/hospitals/           — staff (hospital admin) only
    update    PUT  /api/hospitals/{id}/      — staff only
    destroy   DELETE /api/hospitals/{id}/   — staff only
    """

    queryset = Hospital.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return OrganizationListSerializer
        return OrganizationDetailSerializer

    def get_permissions(self):
        """Read is open to any authenticated user; writes require is_staff."""
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Bind the creating hospital admin to the record."""
        serializer.save(created_by=self.request.user)

    # ── convenience endpoint ──────────────────────────────────────────────────
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """GET /api/hospitals/me/  — return the current admin's profile."""
        serializer = UserProfileSerializer(request.user)
        return Response({'success': True, 'user': serializer.data})


# ── Health Professional ───────────────────────────────────────────────────────

class HealthProfessionalViewSet(viewsets.ModelViewSet):
    """
    CRUD for HealthProfessional (FHIR Practitioner resource).

    list      GET  /api/practitioners/           — authenticated users
    retrieve  GET  /api/practitioners/{id}/      — authenticated users
    create    POST /api/practitioners/           — hospital admin (is_staff) only
    update    PUT  /api/practitioners/{id}/      — hospital admin only
    destroy   DELETE /api/practitioners/{id}/   — hospital admin only
    login     POST /api/practitioners/login/     — open (AllowAny)
    """

    queryset = HealthProfessional.objects.select_related('hospital', 'user', 'registered_by')

    def get_serializer_class(self):
        if self.action == 'create':
            return PractitionerCreateSerializer
        if self.action == 'retrieve':
            return HealthProfessionalDetailSerializer
        if self.action == 'login':
            return PractitionerLoginSerializer
        return PractitionerSerializer

    def get_permissions(self):
        if self.action == 'login':
            return [AllowAny()]
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Hospital admin is automatically set as registered_by."""
        serializer.save(registered_by=self.request.user)

    # ── Login ─────────────────────────────────────────────────────────────────

    @action(detail=False, methods=['post'], permission_classes=[AllowAny],
            url_path='login')
    def login(self, request):
        """
        POST /api/practitioners/login/
        Body: { "license_number": "...", "password": "..." }

        Authenticates the practitioner via their linked Django User account
        (username == license_number) and returns JWT access + refresh tokens.
        """
        serializer = PractitionerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        license_number = serializer.validated_data['license_number']
        password = serializer.validated_data['password']

        # Look up practitioner
        try:
            hp = HealthProfessional.objects.select_related('user', 'hospital').get(
                license_number=license_number
            )
        except HealthProfessional.DoesNotExist:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not hp.is_active:
            return Response(
                {'detail': 'This account has been deactivated.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if hp.user is None:
            return Response(
                {'detail': 'No login account linked to this practitioner. Contact your admin.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Verify password against the linked User account
        if not hp.user.check_password(password):
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Issue JWT tokens
        refresh = RefreshToken.for_user(hp.user)
        refresh['user_type'] = 'practitioner'
        refresh['license_number'] = hp.license_number
        refresh['staff_id'] = hp.staff_id
        refresh['hospital_id'] = str(hp.hospital.id)

        return Response(
            {
                'success': True,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'practitioner': PractitionerSerializer(hp).to_representation(hp),
            },
            status=status.HTTP_200_OK,
        )
