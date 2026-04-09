"""
health_professionals/management/commands/fix_practitioner_passwords.py
────────────────────────────────────────────────────────────────────────
One-off command to re-activate and re-hash passwords for practitioner
accounts that were created with a potentially broken password state.

Usage:
    python manage.py fix_practitioner_passwords --license <license_number> --password <new_password>

Or to list all practitioners with a possibly broken user account:
    python manage.py fix_practitioner_passwords --list
"""
from django.core.management.base import BaseCommand
from health_professionals.models import HealthProfessional


class Command(BaseCommand):
    help = 'Fix or reset a practitioner login account'

    def add_arguments(self, parser):
        parser.add_argument('--license', type=str, help='License number of the practitioner')
        parser.add_argument('--password', type=str, help='New password to set')
        parser.add_argument('--list', action='store_true', help='List all practitioners and their user state')
        parser.add_argument('--activate-all', action='store_true', help='Activate all linked user accounts')

    def handle(self, *args, **options):
        if options['list']:
            self._list()
        elif options['activate_all']:
            self._activate_all()
        elif options['license'] and options['password']:
            self._reset(options['license'], options['password'])
        else:
            self.stderr.write(self.style.ERROR(
                'Provide --list, --activate-all, or both --license and --password'
            ))

    def _list(self):
        hps = HealthProfessional.objects.select_related('user').all()
        self.stdout.write(f"\n{'License':<20} {'Name':<30} {'Has User':<10} {'Active':<10}")
        self.stdout.write('-' * 70)
        for hp in hps:
            has_user = hp.user is not None
            active   = hp.user.is_active if has_user else 'N/A'
            self.stdout.write(f"{hp.license_number:<20} {hp.full_name:<30} {str(has_user):<10} {str(active):<10}")

    def _activate_all(self):
        hps = HealthProfessional.objects.select_related('user').filter(user__isnull=False)
        count = 0
        for hp in hps:
            if not hp.user.is_active:
                hp.user.is_active = True
                hp.user.save(update_fields=['is_active'])
                count += 1
                self.stdout.write(self.style.WARNING(
                    f'Activated user for: {hp.license_number} ({hp.full_name})'
                ))
        self.stdout.write(self.style.SUCCESS(f'\nActivated {count} account(s).'))

    def _reset(self, license_number, password):
        try:
            hp = HealthProfessional.objects.select_related('user').get(
                license_number=license_number.strip()
            )
        except HealthProfessional.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'No practitioner found with license: {license_number}'))
            return

        if hp.user is None:
            self.stderr.write(self.style.ERROR(f'Practitioner {license_number} has no linked user account.'))
            return

        hp.user.set_password(password)
        hp.user.is_active = True
        hp.user.save(update_fields=['password', 'is_active'])
        self.stdout.write(self.style.SUCCESS(
            f'Password reset and account activated for: {hp.license_number} ({hp.full_name})'
        ))
