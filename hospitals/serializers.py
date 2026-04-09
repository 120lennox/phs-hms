from rest_framework import serializers
from .models import Hospital
from hms.constants import (
    FHIRSystems,
    CodeSystems,
    IdentifierTypes,
    OrganizationCategoryMapping
)
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Serializes Hospital model to FHIR R4 Organization resource.
    Maps hospital data to FHIR standard for interoperability with CPR and other systems.
    Compatible with CPR microservice.
    """
    
    # FHIR input fields (write_only for receiving FHIR JSON)
    identifier = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="FHIR: Organization.identifier — [{system, value, use}]"
    )
    telecom = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="FHIR: Organization.telecom — [{system: phone|email, value}]"
    )
    address = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="FHIR: Organization.address — [{use, text, line[], city, district, country}]"
    )
    
    class Meta:
        model = Hospital
        fields = [
            'id',
            'name',
            'category',
            'is_active',
            'identifier',
            'telecom',
            'address'
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'name': {'required': True},
            'category': {'required': True},
        }
    
    def validate_name(self, value):
        """Validate hospital name is provided"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Hospital name is required.")
        return value
    
    def validate_category(self, value):
        """Validate hospital category is valid"""
        valid_categories = [choice[0] for choice in Hospital.HOSPITAL_CATEGORY_CHOICES]
        if value not in valid_categories:
            raise serializers.ValidationError(
                f"Hospital category must be one of: {', '.join(valid_categories)}."
            )
        return value
    
    def validate(self, attrs):
        """Validate required fields"""
        if 'name' not in attrs:
            raise serializers.ValidationError({"name": "Hospital name is required."})
        if 'category' not in attrs:
            raise serializers.ValidationError({"category": "Hospital category is required."})
        return attrs
    
    def to_representation(self, instance):
        """
        Build complete FHIR Organization resource from hospital instance.
        This is returned on GET requests.
        """
        return {
            "resourceType": "Organization",
            "id": str(instance.id),
            "identifier": self._build_identifiers(instance),
            "type": self._build_type(instance),
            "name": instance.name,
            "active": instance.is_active,
            "telecom": self._build_telecom(instance),
            "address": self._build_address(instance),
        }
    
    def create(self, validated_data):
        """Parse FHIR JSON on POST and create hospital"""
        identifier_data = validated_data.pop('identifier', [])
        telecom_data = validated_data.pop('telecom', [])
        address_data = validated_data.pop('address', [])
        
        # Extract contact number from telecom
        for t in telecom_data:
            if t.get('system') == 'phone':
                validated_data['contact_number'] = t.get('value')
        
        # Extract address info
        if address_data:
            addr = address_data[0]
            validated_data['address'] = addr.get('text', '')
            validated_data['district'] = addr.get('district', '')
        
        return Hospital.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Parse FHIR JSON on PATCH/PUT and update hospital"""
        identifier_data = validated_data.pop('identifier', None)
        telecom_data = validated_data.pop('telecom', None)
        address_data = validated_data.pop('address', None)
        
        # Update contact from telecom
        if telecom_data:
            for t in telecom_data:
                if t.get('system') == 'phone':
                    instance.contact_number = t.get('value')
        
        # Update address info
        if address_data:
            addr = address_data[0]
            instance.address = addr.get('text', instance.address)
            instance.district = addr.get('district', instance.district)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
    
    # ============ Helper methods for building FHIR structures ============
    
    def _build_identifiers(self, instance):
        """Build FHIR Identifier array"""
        identifiers = [
            {
                'use': 'official',
                'type': IdentifierTypes.registation_number(),
                'system': FHIRSystems.hospital_registration_number(),
                'value': instance.registration_number,
            },
            {
                'use': 'secondary',
                'type': IdentifierTypes.internal_id(),
                'system': FHIRSystems.hospital_id(),
                'value': instance.hospital_id,
            }
        ]
        
        # Add CPR institution reference if available
        if instance.cpr_institution_id:
            identifiers.append({
                'use': 'secondary',
                'type': IdentifierTypes.medical_license(),
                'system': FHIRSystems.cpr_institution_id(),
                'value': str(instance.cpr_institution_id),
            })
        
        return identifiers
    
    def _build_type(self, instance):
        """Build FHIR Organization Type array with SNOMED-CT coding"""
        category_info = OrganizationCategoryMapping.get(instance.category)
        
        return [
            {
                'coding': [
                    {
                        'system': CodeSystems.organization_type(),
                        'code': category_info['code'],
                        'display': category_info['display']
                    }
                ],
                'text': instance.get_category_display()
            }
        ]
    
    def _build_telecom(self, instance):
        """Build FHIR Telecom array"""
        telecom = []
        
        if instance.contact_number:
            telecom.append({
                'system': 'phone',
                'value': instance.contact_number,
                'use': 'work'
            })
        
        return telecom
    
    def _build_address(self, instance):
        """Build FHIR Address array"""
        return [
            {
                'use': 'work',
                'type': 'both',
                'text': instance.address or '',
                'district': instance.district or '',
                'country': 'NG'  # Nigeria
            }
        ]

class HospitalAdminRegisterSerializer(serializers.ModelSerializer):
    """Serializer for hospital admin registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password2',
            'first_name',
            'last_name',
        ]
        extra_kwargs = {
            'first_name': {'required': True},   
            'last_name': {'required': True},
            'email': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password2')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_staff=True
        )
        
        return user