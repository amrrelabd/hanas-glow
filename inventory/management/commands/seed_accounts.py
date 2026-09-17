from django.core.management.base import BaseCommand

from inventory.models import Account

DEFAULT_ACCOUNTS = [
    ('1000', 'Cash', Account.Type.ASSET),
    ('1010', 'Accounts Receivable', Account.Type.ASSET),
    ('1020', 'Inventory', Account.Type.ASSET),
    ('2000', 'Accounts Payable', Account.Type.LIABILITY),
    ('3000', "Owner's Equity", Account.Type.EQUITY),
    ('4000', 'Sales Revenue', Account.Type.INCOME),
    ('5000', 'Cost of Goods Sold', Account.Type.EXPENSE),
    ('5010', 'Operating Expenses', Account.Type.EXPENSE),
    ('5020', 'Damaged/Lost Inventory', Account.Type.EXPENSE),
]


class Command(BaseCommand):
    help = 'Seed the default chart of accounts'

    def handle(self, *args, **options):
        created = 0
        for code, name, acc_type in DEFAULT_ACCOUNTS:
            _, was_created = Account.objects.get_or_create(code=code, defaults={'name': name, 'type': acc_type})
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Accounts created: {created} (of {len(DEFAULT_ACCOUNTS)} total)'))
