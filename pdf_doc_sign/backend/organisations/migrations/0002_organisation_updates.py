# Generated migration to backfill missing owner memberships

from django.db import migrations


def create_missing_owner_memberships(apps, schema_editor):
    """
    Create OrganisationMembership records for owners who don't have one.
    This fixes organisations created before the auto-membership feature was added.
    """
    Organisation = apps.get_model('organisations', 'Organisation')
    OrganisationMembership = apps.get_model('organisations', 'OrganisationMembership')
    
    created_count = 0
    for org in Organisation.objects.all():
        # Check if owner already has a membership
        existing = OrganisationMembership.objects.filter(
            user=org.owner,
            organisation=org
        ).first()
        
        if not existing:
            OrganisationMembership.objects.create(
                user=org.owner,
                organisation=org,
                role='OWNER',
                is_active=True
            )
            created_count += 1
            print(f"  Created OWNER membership: {org.owner.email} → {org.name}")
    
    if created_count:
        print(f"\n✅ Created {created_count} missing owner membership(s)")
    else:
        print("✅ All owners already have memberships")


def reverse_noop(apps, schema_editor):
    """No reverse - memberships should remain."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('organisations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_missing_owner_memberships, reverse_noop),
    ]
