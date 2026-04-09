import uuid
from django.db import models
from django.contrib.auth import get_user_model
from hospitals.models import Hospital

User = get_user_model()

class HealthProfessional(models.Model):

    SPECIALIZATION_CHOICES = [
        ('general_medicine', 'General Medicine'),
        ('mental_health', 'Mental Health'),
        ('surgery', 'Surgery'),
        ('pediatrics', 'Pediatrics'),
        ('orthopedics', 'Orthopedics'),
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('dermatology', 'Dermatology'),
        ('gynecology', 'Gynecology'),
        ('laboratory', 'Laboratory'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    staff_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Auto generated as HP-{license_number}"
    )
    license_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Official medical license number"
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='health_professional',
        null=True,
        blank=True
    )

    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=255, db_index=True)

    specialization = models.CharField(
        max_length=50,
        choices=SPECIALIZATION_CHOICES,
        db_index=True
    )
    department = models.CharField(max_length=100, db_index=True)

    
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(unique=True, db_index=True)

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.PROTECT,
        related_name='health_professionals',
        db_index=True
    )

   
    
    is_active = models.BooleanField(default=True)
    registered_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='registered_health_professionals',
        help_text="Admin who registered this health professional"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'health_professionals'
        ordering = ['full_name']
        verbose_name = 'Health Professional'
        verbose_name_plural = 'Health Professionals'
        indexes = [
            models.Index(fields=['full_name']),
            models.Index(fields=['specialization']),
            models.Index(fields=['hospital']),
            models.Index(fields=['department']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.specialization}) - {self.staff_id}"

    def save(self, *args, **kwargs):
        # Auto build full_name
        if not self.full_name:
            self.full_name = f"{self.first_name} {self.last_name}".strip()

        # Auto generate staff_id
        if not self.staff_id:
            self.staff_id = f"HP-{self.license_number}"

        super().save(*args, **kwargs)