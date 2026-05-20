import csv
import io
from datetime import date

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from ..models import PortalUser
from ..admin import PortalUserAdminForm


def make_portal_user(**kwargs):
    defaults = {
        'name': 'Muster',
        'vorname': 'Max',
        'email_kontakt': 'kontakt@example.com',
        'email_user': 'user@example.com',
        'abteilung': 'AFR',
        'eintritt_am': date(2020, 1, 1),
        'status': 'aktiv',
        'intern': True,
        'rolle': 'Viewer',
        'racf_id': 'ABCD',
    }
    defaults.update(kwargs)
    return PortalUser.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class PortalUserModelTest(TestCase):
    def test_benutzertyp_defaults_to_creator(self):
        user = make_portal_user()
        self.assertEqual(user.benutzertyp, 'Creator')

    def test_intern_defaults_to_true(self):
        user = make_portal_user()
        self.assertTrue(user.intern)

    def test_racf_id_is_primary_key(self):
        user = make_portal_user(racf_id='AA01')
        self.assertEqual(user.pk, 'AA01')

    def test_typ_account_stores_multiple_values(self):
        user = make_portal_user(typ_account=['AD', 'BE-Login'])
        user.refresh_from_db()
        self.assertEqual(user.typ_account, ['AD', 'BE-Login'])


# ---------------------------------------------------------------------------
# Admin form tests
# ---------------------------------------------------------------------------

class PortalUserAdminFormTest(TestCase):
    def _form_data(self, **kwargs):
        defaults = {
            'name': 'Muster', 'vorname': 'Max',
            'email_kontakt': 'k@example.com', 'email_user': 'u@example.com',
            'abteilung': 'AFR', 'funktion': 'andere',
            'eintritt_am': '2020-01-01', 'status': 'aktiv',
            'intern': True, 'rolle': 'Viewer', 'racf_id': 'AA01',
            'typ_account': [], 'ews': False, 'bkt': False, 'prod': False,
            'status_nb': '', 'bemerkung': '',
        }
        defaults.update(kwargs)
        return defaults

    def test_duplicate_racf_id_on_new_user_raises_error(self):
        make_portal_user(racf_id='AA01')
        form = PortalUserAdminForm(data=self._form_data(racf_id='AA01'))
        self.assertFalse(form.is_valid())
        self.assertIn('racf_id', form.errors)

    def test_unique_racf_id_on_new_user_is_valid(self):
        form = PortalUserAdminForm(data=self._form_data(racf_id='AA01'))
        self.assertTrue(form.is_valid())

    def test_editing_existing_user_same_racf_id_is_valid(self):
        user = make_portal_user(racf_id='AA01')
        form = PortalUserAdminForm(data=self._form_data(racf_id='AA01'), instance=user)
        self.assertTrue(form.is_valid())


# ---------------------------------------------------------------------------
# Admin action tests
# ---------------------------------------------------------------------------

class PortalUserAdminActionTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client.login(username='admin', password='password')
        self.changelist_url = reverse('admin:editor_portaluser_changelist')

    def _post_action(self, action, users):
        return self.client.post(self.changelist_url, {
            'action': action,
            '_selected_action': [str(u.pk) for u in users],
        })

    def test_export_zu_bestellen_csv_only_includes_zu_bestellen(self):
        u1 = make_portal_user(racf_id='AA01', status='zu bestellen', name='Alpha')
        make_portal_user(racf_id='AA02', status='aktiv', name='Beta')
        response = self._post_action('export_zu_bestellen_csv', [u1])
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        rows = list(csv.reader(response.content.decode('utf-8').splitlines()))
        self.assertEqual(len(rows), 2)  # header + 1 row
        self.assertIn('Alpha', rows[1])

    def test_export_zu_bestellen_csv_headers(self):
        make_portal_user(racf_id='AA01', status='zu bestellen')
        response = self._post_action('export_zu_bestellen_csv', [])
        rows = list(csv.reader(response.content.decode('utf-8').splitlines()))
        self.assertEqual(rows[0], ['E-Mail', 'Rolle', 'Benutzertyp', 'Vorname', 'Nachname', 'Benutzerkennung'])

    def test_export_zu_bestellen_csv_data_row(self):
        make_portal_user(racf_id='AA01', status='zu bestellen',
                         email_user='u@example.com', rolle='Viewer',
                         benutzertyp='Creator', vorname='Max', name='Muster')
        response = self._post_action('export_zu_bestellen_csv', [])
        rows = list(csv.reader(response.content.decode('utf-8').splitlines()))
        self.assertEqual(rows[1], ['u@example.com', 'Viewer', 'Creator', 'Max', 'Muster', 'AA01'])

    def test_export_zu_bestellen_csv_filename(self):
        response = self._post_action('export_zu_bestellen_csv', [])
        disposition = response['Content-Disposition']
        self.assertRegex(disposition, r'\d{4}_\d{2}_\d{2}_GIS_Hub_Erfassung_User_AD_BE-Login\.csv')

    def test_benutzerliste_erstellen_csv_headers_and_rows(self):
        u1 = make_portal_user(racf_id='AA01')
        response = self._post_action('benutzerliste_erstellen', [u1])
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        rows = list(csv.reader(response.content.decode('utf-8').splitlines()))
        self.assertEqual(rows[0][0], 'name')
        self.assertEqual(len(rows), 2)  # header + 1 row

    def test_benutzerliste_erstellen_filename(self):
        u1 = make_portal_user(racf_id='AA01')
        response = self._post_action('benutzerliste_erstellen', [u1])
        self.assertIn('Benutzerliste_GIS_Hub.csv', response['Content-Disposition'])

    def test_benutzerliste_erstellen_only_exports_selected(self):
        u1 = make_portal_user(racf_id='AA01', name='Selected')
        make_portal_user(racf_id='AA02', name='NotSelected')
        response = self._post_action('benutzerliste_erstellen', [u1])
        rows = list(csv.reader(response.content.decode('utf-8').splitlines()))
        names = [row[0] for row in rows[1:]]
        self.assertIn('Selected', names)
        self.assertNotIn('NotSelected', names)

    def test_infomail_stoerung_returns_all_users(self):
        make_portal_user(racf_id='AA01', intern=False, email_kontakt='stoerung@example.com')
        u2 = make_portal_user(racf_id='AA02', intern=True, email_kontakt='erw@example.com')
        response = self._post_action('infomail_stoerung', [u2])  # selection is ignored
        content = response.content.decode('utf-8')
        self.assertIn('stoerung@example.com', content)
        self.assertIn('erw@example.com', content)

    def test_infomail_erweiterung_returns_only_intern_users(self):
        make_portal_user(racf_id='AA01', intern=True, email_kontakt='erw@example.com')
        u2 = make_portal_user(racf_id='AA02', intern=False, email_kontakt='extern@example.com')
        response = self._post_action('infomail_erweiterung', [u2])  # selection is ignored
        content = response.content.decode('utf-8')
        self.assertIn('erw@example.com', content)
        self.assertNotIn('extern@example.com', content)


# ---------------------------------------------------------------------------
# Import view tests
# ---------------------------------------------------------------------------

class PortalUserImportTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client.login(username='admin', password='password')
        self.import_url = reverse('admin:portaluser_import_csv')

    def _make_csv(self, rows):
        output = io.StringIO()
        fieldnames = [
            'name', 'vorname', 'email_kontakt', 'email_user',
            'abteilung', 'funktion', 'eintritt_am', 'status',
            'intern', 'rolle', 'racf_id', 'typ_account',
            'ews', 'bkt', 'prod', 'benutzertyp', 'status_nb', 'bemerkung',
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    def _default_row(self, **kwargs):
        row = {
            'name': 'Muster', 'vorname': 'Max',
            'email_kontakt': 'k@example.com', 'email_user': 'u@example.com',
            'abteilung': 'AFR', 'funktion': '', 'eintritt_am': '2020-01-01',
            'status': 'aktiv', 'intern': 'True', 'rolle': 'Viewer',
            'racf_id': 'ABCD', 'typ_account': 'AD',
            'ews': 'False', 'bkt': 'False', 'prod': 'False',
            'benutzertyp': 'Creator', 'status_nb': '', 'bemerkung': '',
        }
        row.update(kwargs)
        return row

    def _upload(self, csv_content):
        f = SimpleUploadedFile('users.csv', csv_content.encode('utf-8'), content_type='text/csv')
        return self.client.post(self.import_url, {'csv_file': f}, follow=True)

    def test_get_shows_import_form(self):
        response = self.client.get(self.import_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'csv_file')

    def test_import_creates_new_user(self):
        response = self._upload(self._make_csv([self._default_row()]))
        self.assertRedirects(response, reverse('admin:editor_portaluser_changelist'))
        self.assertEqual(PortalUser.objects.count(), 1)

    def test_import_updates_existing_user_by_racf_id(self):
        make_portal_user(racf_id='ABCD', name='Alt')
        self._upload(self._make_csv([self._default_row(name='Neu')]))
        self.assertEqual(PortalUser.objects.count(), 1)
        self.assertEqual(PortalUser.objects.get(racf_id='ABCD').name, 'Neu')

    def test_import_accepts_german_date_format(self):
        self._upload(self._make_csv([self._default_row(eintritt_am='15.03.2021')]))
        self.assertEqual(PortalUser.objects.get(racf_id='ABCD').eintritt_am, date(2021, 3, 15))

    def test_import_invalid_date_reports_error_and_skips_row(self):
        response = self._upload(self._make_csv([self._default_row(eintritt_am='kein-datum')]))
        self.assertEqual(PortalUser.objects.count(), 0)
        messages = [m.level_tag for m in response.context['messages']]
        self.assertIn('error', messages)

    def test_import_no_file_reports_error(self):
        response = self.client.post(self.import_url, {}, follow=True)
        messages = [m.level_tag for m in response.context['messages']]
        self.assertIn('error', messages)

    def test_import_success_message_shows_counts(self):
        response = self._upload(self._make_csv([self._default_row()]))
        messages = [str(m) for m in response.context['messages']]
        self.assertTrue(any('erstellt' in m for m in messages))
