from rest_framework import serializers
from .models import HealthProfessional
from hospitals.models import Hospital
from hms.constants import (
    FHIRSystems,
    CodeSystems,
    IdentifierTypes,
    PractitionerSpecializationMapping
)


class PractitionerSerializer(serializers.ModelSerializer):
    
    # FHIR input fields (write_only for receiving FHIR JSON)
    identifier = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="FHIR: Practitioner.identifier — [{system, value, use}]"
    )
    name = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="FHIR: Practitioner.name — [{use, text, family, given[]}]"
    )
    telecom = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="FHIR: Practitioner.telecom — [{system: phone|email, value}]"
    )
    qualification = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="FHIR: Practitioner.qualification — [{code, identifier}]"
    )
    
    class Meta:
        model = HealthProfessional
        fields = [
            'id',
            'active',
            'identifier',
            'name',
            'telecom',
            'qualification'
        ]
        extra_kwargs = {
            'id': {'read_only': True},
        }
    
    def validate_name(self, value):
        """Validate name is provided with required fields"""
        if not value:
            raise serializers.ValidationError("Practitioner.name is required.")
        
        official = next((n for n in value if n.get('use') == 'official'), value[0] if value else None)
        if not official:
            raise serializers.ValidationError("Practitioner.name with use='official' is required.")
        
        if not official.get('family'):
            raise serializers.ValidationError("Practitioner.name.family (last name) is required.")
        if not official.get('given'):
            raise serializers.ValidationError("Practitioner.name.given (first name) is required.")
        
        return value
    
    def validate(self, attrs):
        """Validate required fields"""
        if 'name' not in attrs:
            raise serializers.ValidationError({"name": "Practitioner.name is required."})
        return attrs
    
    def to_representation(self, instance):
        """
        Build complete FHIR Practitioner resource from health professional instance.
        This is returned on GET requests.
        """
        return {
            "resourceType": "Practitioner",
            "id": str(instance.id),
            "identifier": self._build_identifiers(instance),
            "active": instance.is_active,
            "name": self._build_name(instance),
            "telecom": self._build_telecom(instance),
            "qualification": self._build_qualifications(instance),
        }
    
    def create(self, validated_data):
        """Parse FHIR JSON on POST and create health professional"""
        identifier_data = validated_data.pop('identifier', [])
        name_data = validated_data.pop('name', [])
        telecom_data = validated_data.pop('telecom', [])
        qualification_data = validated_data.pop('qualification', [])
        
        # Extract name
        official_name = next((n for n in name_data if n.get('use') == 'official'), name_data[0] if name_data else {})
        validated_data['first_name'] = (official_name.get('given') or [''])[0]
        validated_data['last_name'] = official_name.get('family', '')
        validated_data['full_name'] = official_name.get('text') or \
            f"{validated_data['first_name']} {validated_data['last_name']}".strip()
        
        # Extract telecom
        for t in telecom_data:
            if t.get('system') == 'phone':
                validated_data['contact_number'] = t.get('value')
            elif t.get('system') == 'email':
                validated_data['email'] = t.get('value')
        
        return HealthProfessional.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Parse FHIR JSON on PATCH/PUT and update health professional"""
        identifier_data = validated_data.pop('identifier', None)
        name_data = validated_data.pop('name', None)
        telecom_data = validated_data.pop('telecom', None)
        qualification_data = validated_data.pop('qualification', None)
        
        if name_data:
            official_name = next((n for n in name_data if n.get('use') == 'official'), name_data[0] if name_data else {})
            instance.first_name = (official_name.get('given') or [instance.first_name])[0]
            instance.last_name = official_name.get('family', instance.last_name)
            instance.full_name = official_name.get('text') or \
                f"{instance.first_name} {instance.last_name}".strip()
        
        if telecom_data:
            for t in telecom_data:
                if t.get('system') == 'phone':
                    instance.contact_number = t.get('value')
                elif t.get('system') == 'email':
                    instance.email = t.get('value')
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
    
    #Helper methods for building FHIR structures
    
    def _build_identifiers(self, instance):
        """Build FHIR Identifier array"""
        identifiers = [
            {
                'use': 'official',
                'type': IdentifierTypes.medical_license(),
                'system': FHIRSystems.license_number(),
                'value': instance.license_number,
            },
            {
                'use': 'secondary',
                'type': IdentifierTypes.employee_number(),
                'system': FHIRSystems.staff_id(),
                'value': instance.staff_id,
            }
        ]
        return identifiers
    
    def _build_name(self, instance):
        """Build FHIR HumanName array"""
        return [
            {
                'use': 'official',
                'family': instance.last_name or '',
                'given': [instance.first_name] if instance.first_name else [],
                'text': instance.full_name
            }
        ]
    
    def _build_telecom(self, instance):
        """Build FHIR Telecom array"""
        telecom = []
        
        if instance.email:
            telecom.append({
                'system': 'email',
                'value': instance.email,
                'use': 'work'
            })
        
        if instance.contact_number:
            telecom.append({
                'system': 'phone',
                'value': instance.contact_number,
                'use': 'work'
            })
        
        return telecom
    
    def _build_qualifications(self, instance):
        """Build FHIR Qualification array"""
        qualifications = []
        
        # Add specialization as a qualification
        qualifications.append({
            'identifier': [
                {
                    'system': FHIRSystems.license_number(),
                    'value': instance.license_number
                }
            ],
            'code': {
                'coding': [
                    {
                        'system': CodeSystems.snomed_ct(),
                        'code': instance.specialization,
                        'display': instance.get_specialization_display()
                    }
                ],
                'text': instance.get_specialization_display()
            },
            'period': {
                'start': instance.created_at.isoformat() if instance.created_at else None
            }
        })
        
        return qualifications


class PractitionerRoleSerializer(serializers.Serializer):

    # FHIR input fields
    identifier = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="FHIR: PractitionerRole.identifier"
    )
    
    class Meta:
        fields = ['identifier']
    
    def to_representation(self, instance):
        """Build complete FHIR PractitionerRole resource"""
        health_prof = instance
        
        return {
            "resourceType": "PractitionerRole",
            "id": {health_prof.id},
            "identifier": self._build_identifiers(health_prof),
            "active": health_prof.is_active and health_prof.hospital.is_active,
            "period": self._build_period(health_prof),
            "practitioner": self._build_practitioner_ref(health_prof),
            "organization": self._build_organization_ref(health_prof),
            "role": self._build_role(health_prof),
            "specialty": self._build_specialty(health_prof),
            "department": self._build_department(health_prof),
        }
    
    # ============ Helper methods for building FHIR structures ============
    
    def _build_identifiers(self, instance):
        """Build FHIR Identifier array for the role"""
        return [
            {
                'system': FHIRSystems.practitioner_role_id(),
                'value': f"{instance.staff_id}@{instance.hospital.hospital_id}"
            }
        ]
    
    def _build_period(self, instance):
        """Build FHIR Period"""
        return {
            'start': instance.created_at.isoformat() if instance.created_at else None
        }
    
    def _build_practitioner_ref(self, instance):
        """Build reference to Practitioner resource"""
        return {
            'reference': f"Practitioner/{instance.id}",
            'type': 'Practitioner',
            'display': instance.full_name
        }
    
    def _build_organization_ref(self, instance):
        """Build reference to Organization resource"""
        return {
            'reference': f"Organization/{instance.hospital.id}",
            'type': 'Organization',
            'display': instance.hospital.name
        }
    
    def _build_role(self, instance):
        """Build FHIR Role array with SNOMED-CT codes"""
        role_info = PractitionerSpecializationMapping.get_role(instance.specialization)
        
        return [
            {
                'coding': [
                    {
                        'system': CodeSystems.snomed_ct(),
                        'code': role_info['code'],
                        'display': role_info['display']
                    }
                ],
                'text': instance.get_specialization_display()
            }
        ]
    
    def _build_specialty(self, instance):
        """Build FHIR Specialty array with SNOMED-CT codes"""
        specialty_info = PractitionerSpecializationMapping.get_specialty(instance.specialization)
        
        return [
            {
                'coding': [
                    {
                        'system': CodeSystems.snomed_ct(),
                        'code': specialty_info['code'],
                        'display': specialty_info['display']
                    }
                ],
                'text': instance.get_specialization_display()
            }
        ]
    
    def _build_department(self, instance):
        """Build FHIR Department reference"""
        if not instance.department:
            return []
        
        return [
            {
                'reference': f"Organization/{instance.hospital.id}",
                'display': instance.department
            }
        ]


class HealthProfessionalDetailSerializer(serializers.Serializer):
    """
    Complete FHIR bundle-like representation of HealthProfessional.
    Returns Practitioner + PractitionerRole + Organization references.
    Useful for single resource retrieval with full context.
    """
    
    practitioner = serializers.SerializerMethodField()
    practitioner_role = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    
    def get_practitioner(self, obj):
        """Get Practitioner representation"""
        serializer = PractitionerSerializer(obj)
        return serializer.to_representation(obj)
    
    def get_practitioner_role(self, obj):
        """Get PractitionerRole representation"""
        serializer = PractitionerRoleSerializer(obj)
        return serializer.to_representation(obj)
    
    def get_organization(self, obj):
        """Get Organization representation"""
        from hospitals.serializers import OrganizationSerializer
        serializer = OrganizationSerializer(obj.hospital)
        return serializer.to_representation(obj.hospital)
