import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Hospital(models.Model):

    HOSPITAL_CATEGORY_CHOICES = [
        ('central_hospital', 'Central Hospital'),
        ('district_hospital', 'District Hospital'),
        ('rural_hospital', 'Rural Hospital'),
        ('health_center', 'Health Center'),
        ('clinic', 'Clinic'),
    ]

    # identifiers
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    hospital_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Human readable ID — auto generated as HOSP-{registration_number}"
    )
    registration_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Official government registration number"
    )

    
    name = models.CharField(max_length=255, db_index=True)
    category = models.CharField(
        max_length=50,
        choices=HOSPITAL_CATEGORY_CHOICES,
        db_index=True
    )
    district = models.CharField(max_length=255, db_index=True)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)

    # CPR reference — after HMS registers with CPR
    # stored here so HMS knows its own CPR institution ID
  
    cpr_institution_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID assigned by CPR when this hospital registered as an institution"
    )


    # Status + audit
  
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_hospitals',
        help_text="Admin who created this hospital"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hospitals'
        ordering = ['name']
        verbose_name = 'Hospital'
        verbose_name_plural = 'Hospitals'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['district']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.hospital_id:
            self.hospital_id = f"HOSP-{self.registration_number}"
        super().save(*args, **kwargs)

    @property
    def total_health_professionals(self):
        return self.health_professionals.count()

    @property
    def active_health_professionals(self):
        return self.health_professionals.filter(is_active=True).count()

    @property
    def total_patients(self):
        return self.patients.count()

    @property
    def active_patients(self):
        return self.patients.filter(is_active=True).count()