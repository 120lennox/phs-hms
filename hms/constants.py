"""
FHIR Constants and System URLs for HMS
Defines standard identifier systems, coding systems, and other FHIR-related constants
for consistent interoperability with other health systems like CPR.
"""


class FHIRSystems:
    """FHIR Identifier System URLs"""
    
    @staticmethod
    def hospital_registration_number():
        """Government/Official hospital registration number system"""
        return "http://example.com/phs-hms/registration-number"
    
    @staticmethod
    def hospital_id():
        """HMS internal hospital identifier (HOSP-{registration_number})"""
        return "http://example.com/phs-hms/hospital-id"
    
    @staticmethod
    def cpr_institution_id():
        """CPR Central Patient Registry institution identifier"""
        return "http://example.com/cpr/institution-id"
    
    @staticmethod
    def staff_id():
        """HMS internal health professional staff ID (HP-{license_number})"""
        return "http://example.com/phs-hms/staff-id"
    
    @staticmethod
    def license_number():
        """Official professional medical/healthcare license number"""
        return "http://example.com/phs-hms/license-number"
    
    @staticmethod
    def practitioner_role_id():
        """Composite practitioner-organization role identifier"""
        return "http://example.com/phs-hms/practitioner-role"


class CodeSystems:
    """HL7/SNOMED-CT Code System URLs"""
    
    @staticmethod
    def v2_0203():
        """HL7 v2 Identifier Type Coding System"""
        return "http://terminology.hl7.org/CodeSystem/v2-0203"
    
    @staticmethod
    def organization_type():
        """HL7 Organization Type Coding System"""
        return "http://terminology.hl7.org/CodeSystem/organization-type"
    
    @staticmethod
    def snomed_ct():
        """SNOMED Clinical Terms"""
        return "http://snomed.info/sct"
    
    @staticmethod
    def practitioner_role_sct():
        """SNOMED-CT Role Codes for Practitioners"""
        return "http://snomed.info/sct"


class IdentifierTypes:
    """Identifier Type Definitions following FHIR v2-0203"""
    
    @staticmethod
    def registation_number():
        """Government Registration Number Type"""
        return {
            "coding": [
                {
                    "system": CodeSystems.v2_0203(),
                    "code": "NIIP",
                    "display": "National Individual Identifier"
                }
            ],
            "text": "Government Registration Number"
        }
    
    @staticmethod
    def internal_id():
        """Internal System ID Type"""
        return {
            "coding": [
                {
                    "system": CodeSystems.v2_0203(),
                    "code": "URN",
                    "display": "Uniform Resource Name"
                }
            ],
            "text": "Internal System ID"
        }
    
    @staticmethod
    def medical_license():
        """Medical License Number Type"""
        return {
            "coding": [
                {
                    "system": CodeSystems.v2_0203(),
                    "code": "MD",
                    "display": "Medical License Number"
                }
            ],
            "text": "Medical License Number"
        }
    
    @staticmethod
    def employee_number():
        """Employee Number Type"""
        return {
            "coding": [
                {
                    "system": CodeSystems.v2_0203(),
                    "code": "EI",
                    "display": "Employee Number"
                }
            ],
            "text": "Employee Number"
        }


class GenderCodeMapping:
    """Maps application gender values to FHIR codes"""
    
    VALID_CODES = ["male", "female", "other", "unknown"]
    
    @staticmethod
    def is_valid(value):
        """Check if gender code is valid FHIR value"""
        return value in GenderCodeMapping.VALID_CODES


class OrganizationCategoryMapping:
    """Maps hospital category to FHIR Organization Type codes"""
    
    MAPPING = {
        'central_hospital': {
            'code': 'hosp',
            'display': 'Hospital',
        },
        'district_hospital': {
            'code': 'hosp',
            'display': 'Hospital',
        },
        'rural_hospital': {
            'code': 'hosp',
            'display': 'Hospital',
        },
        'health_center': {
            'code': 'prov',
            'display': 'Healthcare Provider',
        },
        'clinic': {
            'code': 'clin',
            'display': 'Clinic',
        }
    }
    
    @staticmethod
    def get(category):
        """Get FHIR type mapping for hospital category"""
        return OrganizationCategoryMapping.MAPPING.get(
            category,
            {'code': 'other', 'display': 'Other'}
        )


class PractitionerSpecializationMapping:
    """Maps health professional specialization to SNOMED-CT codes"""
    
    ROLE_MAPPING = {
        'general_medicine': {
            'code': '309295000',
            'display': 'Physician'
        },
        'mental_health': {
            'code': '309453006',
            'display': 'Psychiatrist'
        },
        'surgery': {
            'code': '309468003',
            'display': 'Surgeon'
        },
        'pediatrics': {
            'code': '309472002',
            'display': 'Pediatrician'
        },
        'orthopedics': {
            'code': '309474001',
            'display': 'Orthopedic Surgeon'
        },
        'cardiology': {
            'code': '309447006',
            'display': 'Cardiologist'
        },
        'neurology': {
            'code': '309466004',
            'display': 'Neurologist'
        },
        'dermatology': {
            'code': '309454012',
            'display': 'Dermatologist'
        },
        'gynecology': {
            'code': '309459001',
            'display': 'Obstetrician and Gynecologist'
        },
        'laboratory': {
            'code': '159001',
            'display': 'Laboratory technologist'
        },
        'other': {
            'code': '309343006',
            'display': 'Physician'
        }
    }
    
    SPECIALTY_MAPPING = {
        'general_medicine': {
            'code': '394802001',
            'display': 'General medicine'
        },
        'mental_health': {
            'code': '394587001',
            'display': 'Psychiatry'
        },
        'surgery': {
            'code': '394610002',
            'display': 'Surgery'
        },
        'pediatrics': {
            'code': '394537008',
            'display': 'Pediatrics'
        },
        'orthopedics': {
            'code': '394677002',
            'display': 'Orthopedic surgery'
        },
        'cardiology': {
            'code': '394579002',
            'display': 'Cardiology'
        },
        'neurology': {
            'code': '394591006',
            'display': 'Neurology'
        },
        'dermatology': {
            'code': '394582007',
            'display': 'Dermatology'
        },
        'gynecology': {
            'code': '394576009',
            'display': 'Obstetrics and gynaecology'
        },
        'laboratory': {
            'code': '394914008',
            'display': 'Pathology'
        },
        'other': {
            'code': '394914008',
            'display': 'Pathology'
        }
    }
    
    @staticmethod
    def get_role(specialization):
        """Get SNOMED-CT role code for specialization"""
        return PractitionerSpecializationMapping.ROLE_MAPPING.get(
            specialization,
            {'code': '309343006', 'display': 'Physician'}
        )
    
    @staticmethod
    def get_specialty(specialization):
        """Get SNOMED-CT specialty code for specialization"""
        return PractitionerSpecializationMapping.SPECIALTY_MAPPING.get(
            specialization,
            {'code': '394802001', 'display': 'General medicine'}
        )
