"""
Organisation Serializers - DocSign UK White-Label
"""
from rest_framework import serializers
from .models import Organisation, Branch, OrganisationMembership, OrganisationRequest


class BranchSerializer(serializers.ModelSerializer):
    logo_display_url = serializers.ReadOnlyField()
    display_colour = serializers.ReadOnlyField()

    class Meta:
        model = Branch
        fields = [
            'id', 'name', 'code', 'address', 'city', 'postcode', 'phone',
            'logo', 'logo_url', 'primary_colour', 'logo_display_url',
            'display_colour', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class OrganisationSerializer(serializers.ModelSerializer):
    branches = BranchSerializer(many=True, read_only=True)
    logo_display_url = serializers.ReadOnlyField()
    documents_limit = serializers.ReadOnlyField()
    documents_remaining = serializers.ReadOnlyField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = [
            'id', 'name', 'slug', 'company_number', 'vat_number',
            'address', 'city', 'postcode', 'country', 'phone', 'email', 'website',
            'domain',
            'logo', 'logo_url', 'logo_display_url', 'primary_colour', 'secondary_colour',
            'custom_domain', 'plan', 'status',
            'documents_used_this_month', 'documents_limit', 'documents_remaining',
            'branches', 'member_count', 'created_at',
        ]
        read_only_fields = ['id', 'slug', 'status', 'documents_used_this_month', 'created_at']

    def get_member_count(self, obj):
        return obj.members.filter(is_active=True).count()


class OrganisationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ['name', 'company_number', 'email', 'phone']

    def create(self, validated_data):
        from django.utils.text import slugify
        user = self.context['request'].user
        name = validated_data['name']

        # Generate unique slug
        slug = slugify(name)[:100]
        base_slug = slug
        counter = 1
        while Organisation.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1

        org = Organisation.objects.create(
            owner=user, slug=slug, **validated_data
        )
        # Organisation.save() auto-creates OWNER membership via _ensure_owner_membership()
        # so no need to create it again here

        return org


class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True, default=None)

    class Meta:
        model = OrganisationMembership
        fields = ['id', 'user', 'user_email', 'user_name', 'branch', 'branch_name', 'role', 'is_active', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class InviteMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=['ADMIN', 'MANAGER', 'MEMBER', 'VIEWER'], default='MEMBER')
    branch_id = serializers.UUIDField(required=False, allow_null=True)


class BrandingSerializer(serializers.ModelSerializer):
    """Public-facing branding data for signing pages."""
    logo_display_url = serializers.ReadOnlyField()

    class Meta:
        model = Organisation
        fields = ['name', 'logo_display_url', 'primary_colour', 'secondary_colour']


class OrganisationRequestSerializer(serializers.Serializer):
    """Serializer for submitting organisation request."""
    organisation_name = serializers.CharField(max_length=255)
    organisation_domain = serializers.CharField(
        max_length=255,
        help_text='Email domain for this organisation (e.g., acerhealthcare.co.uk)'
    )
    work_email = serializers.EmailField(
        help_text='Your work email at this organisation (e.g., john@acerhealthcare.co.uk)'
    )
    company_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postcode = serializers.CharField(max_length=10, required=False, allow_blank=True)

    def validate_organisation_domain(self, value):
        """Validate organisation domain format."""
        value = value.lower().strip()
        
        # Remove http/https if accidentally included
        if value.startswith('http://'):
            value = value[7:]
        if value.startswith('https://'):
            value = value[8:]
        
        # Remove www. if included
        if value.startswith('www.'):
            value = value[4:]
        
        # Basic domain validation
        if '.' not in value:
            raise serializers.ValidationError('Please enter a valid domain (e.g., acerhealthcare.co.uk)')
        
        # Check for common free email domains
        free_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'live.com', 
                       'googlemail.com', 'icloud.com', 'me.com', 'aol.com', 'mail.com']
        if value in free_domains:
            raise serializers.ValidationError('Please use your organisation domain, not a personal email domain.')
        
        return value

    def validate_work_email(self, value):
        """Validate work email format."""
        value = value.lower().strip()
        
        # Check for common free email domains
        domain = value.split('@')[1] if '@' in value else ''
        free_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'live.com', 
                       'googlemail.com', 'icloud.com', 'me.com', 'aol.com', 'mail.com']
        
        if domain in free_domains:
            raise serializers.ValidationError(
                'Please use your work email address (e.g., john@yourcompany.com), not a personal email.'
            )
        
        return value


class OrganisationRequestDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for organisation request (for admin)."""
    requested_by_email = serializers.CharField(source='requested_by.email', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.full_name', read_only=True)
    work_email_domain = serializers.ReadOnlyField()
    domain_matches = serializers.ReadOnlyField()
    can_auto_approve = serializers.ReadOnlyField()

    class Meta:
        model = OrganisationRequest
        fields = [
            'id', 'requested_by', 'requested_by_email', 'requested_by_name',
            'organisation_name', 'organisation_domain', 'company_number',
            'address', 'city', 'postcode',
            'work_email', 'work_email_domain', 'work_email_verified', 'work_email_verified_at',
            'domain_matches', 'can_auto_approve',
            'status', 'reviewed_by', 'reviewed_at', 'rejection_reason',
            'created_organisation',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'requested_by', 'created_at', 'updated_at']
