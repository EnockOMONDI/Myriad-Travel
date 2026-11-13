import uuid

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ExistingMICEInquiryMigrationTests(TransactionTestCase):
    """The service-workflow migration must retain existing corporate enquiries."""

    migrate_from = [('users', '0013_quoterequest_estimated_value_and_more')]
    migrate_to = [('users', '0015_alter_flightinquiry_preferred_contact_and_more')]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        OldMICEInquiry = old_apps.get_model('users', 'MICEInquiry')
        self.old_pk = OldMICEInquiry.objects.create(
            company_name='Existing Company',
            contact_person='Existing Client',
            email='existing@example.com',
            phone_number='+254700000000',
            event_type='Meeting',
            attendees=25,
            event_details='Existing event brief',
        ).pk

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_record_is_preserved_and_gets_unique_reference(self):
        MICEInquiry = self.apps.get_model('users', 'MICEInquiry')
        inquiry = MICEInquiry.objects.get(pk=self.old_pk)
        self.assertEqual(inquiry.company_name, 'Existing Company')
        self.assertEqual(inquiry.status, 'new')
        self.assertIsInstance(inquiry.reference, uuid.UUID)
