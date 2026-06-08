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
    racf_id = kwargs.get('racf_id', 'ABCD')
    user_suffix = str(racf_id).lower() if racf_id is not None else 'noracf'
    defaults = {
        'name': 'Muster',
        'vorname': 'Max',
        'email_kontakt': 'kontakt@example.com',
        'user': f'{user_suffix}@example.com',
        'abteilung': 'AFR',
        'eintritt_am': date(2020, 1, 1),
        'status': 'aktiv',
        'intern': True,
        'rolle': 'Viewer',
        'racf_id': racf_id,
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

    def test_infomail_erweiterung_defaults_to_true(self):
        user = make_portal_user()
        self.assertTrue(user.infomail_erweiterung)

    def test_id_is_auto_primary_key(self):
        user = make_portal_user()
        self.assertIsNotNone(user.pk)
        self.assertIsInstance(user.pk, int)

    def test_racf_id_is_optional(self):
        user = make_portal_user(racf_id=None)
        self.assertIsNone(user.racf_id)

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
            'email_kontakt': 'k@example.com', 'user': 'u@example.com',
            'abteilung': 'AFR', 'funktion': '',
            'eintritt_am': '2020-01-01', 'status': 'aktiv',
            'intern': True, 'rolle': 'Viewer',
            'typ_account': [], 'ews': False, 'bkt': False, 'prod': False,
            'status_nb': '', 'bemerkung': '',
        }
        defaults.update(kwargs)
        return defaults

    def test_duplicate_user_on_new_user_raises_error(self):
        make_portal_user(user='u@example.com')
        form = PortalUserAdminForm(data=self._form_data(user='u@example.com'))
        self.assertFalse(form.is_valid())
        self.assertIn('user', form.errors)

    def test_unique_user_on_new_user_is_valid(self):
        form = PortalUserAdminForm(data=self._form_data(user='unique@example.com'))
        self.assertTrue(form.is_valid())

    def test_editing_existing_user_same_user_value_is_valid(self):
        portal_user = make_portal_user(user='u@example.com')
        form = PortalUserAdminForm(data=self._form_data(user='u@example.com'), instance=portal_user)
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

    def test_export_zu_bestellen_ews_csv_only_includes_ews_users(self):
        u1 = make_portal_user(racf_id='AA01', status='zu bestellen', ews=True, name='Alpha')
        make_portal_user(racf_id='AA02', status='zu bestellen', ews=False, name='Beta')
        make_portal_user(racf_id='AA03', status='aktiv', ews=True, name='Gamma')
        response = self._post_action('export_zu_bestellen_ews_csv', [u1])
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        rows = list(csv.reader(response.content.decode('utf-8').splitlines()))
        names = [row[4] for row in rows[1:]]
        self.assertIn('Alpha', names)
        self.assertNotIn('Beta', names)
        self.assertNotIn('Gamma', names)

    def test_export_zu_bestellen_bkt_csv_only_includes_bkt_users(self):
        u1 = make_portal_user(racf_id='AA01', status='zu bestellen', bkt=True, name='Alpha')
        make_portal_user(racf_id='AA02', status='zu bestellen', bkt=False, name='Beta')
        response = self._post_action('export_zu_bestellen_bkt_csv', [u1])
        rows = list(csv.reader(response.content.decode('utf-8').splitlines()))
        names = [row[4] for row in rows[1:]]
        self.assertIn('Alpha', names)
        self.assertNotIn('Beta', names)

    def test_export_zu_bestellen_prod_csv_only_includes_prod_users(self):
        u1 = make_portal_user(racf_id='AA01', status='zu bestellen', prod=True, name='Alpha')
        make_portal_user(racf_id='AA02', status='zu bestellen', prod=False, name='Beta')
        response = self._post_action('export_zu_bestellen_prod_csv', [u1])
        rows = list(csv.reader(response.content.decode('utf-8').splitlines()))
        names = [row[4] for row in rows[1:]]
        self.assertIn('Alpha', names)
        self.assertNotIn('Beta', names)

    def test_export_zu_bestellen_csv_headers(self):
        u1 = make_portal_user(racf_id='AA01', status='zu bestellen', ews=True)
        response = self._post_action('export_zu_bestellen_ews_csv', [u1])
        rows = list(csv.reader(response.content.decode('utf-8').splitlines()))
        self.assertEqual(rows[0], ['User', 'Rolle', 'Benutzertyp', 'Vorname', 'Nachname', 'Benutzerkennung'])

    def test_export_zu_bestellen_csv_data_row(self):
        u1 = make_portal_user(racf_id='AA01', status='zu bestellen', ews=True,
                              user='u@example.com', rolle='Viewer',
                              benutzertyp='Creator', vorname='Max', name='Muster')
        response = self._post_action('export_zu_bestellen_ews_csv', [u1])
        rows = list(csv.reader(response.content.decode('utf-8').splitlines()))
        self.assertEqual(rows[1], ['u@example.com', 'Viewer', 'Creator', 'Max', 'Muster', 'AA01'])

    def test_export_zu_bestellen_csv_filename(self):
        u1 = make_portal_user(racf_id='AA01', status='zu bestellen', ews=True)
        response = self._post_action('export_zu_bestellen_ews_csv', [u1])
        disposition = response['Content-Disposition']
        self.assertRegex(disposition, r'\d{4}_\d{2}_\d{2}_GIS_Hub_Erfassung_User_AD_BE-Login_EWS\.csv')

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

    def test_email_string_kontakt_returns_selected_addresses(self):
        u1 = make_portal_user(racf_id='AA01', email_kontakt='a@example.com')
        u2 = make_portal_user(racf_id='AA02', email_kontakt='b@example.com')
        make_portal_user(racf_id='AA03', email_kontakt='c@example.com')
        response = self._post_action('email_string_kontakt', [u1, u2])
        emails = response.content.decode('utf-8').split(';')
        self.assertIn('a@example.com', emails)
        self.assertIn('b@example.com', emails)
        self.assertNotIn('c@example.com', emails)

    def test_infomail_stoerung_returns_all_active_users(self):
        make_portal_user(racf_id='AA01', email_kontakt='active@example.com', status='aktiv')
        make_portal_user(racf_id='AA02', email_kontakt='inaktiv@example.com', status='inaktiv')
        u1 = make_portal_user(racf_id='AA03', email_kontakt='other@example.com')
        response = self._post_action('infomail_stoerung', [u1])  # selection is ignored
        content = response.content.decode('utf-8')
        self.assertIn('active@example.com', content)
        self.assertIn('other@example.com', content)
        self.assertNotIn('inaktiv@example.com', content)

    def test_infomail_erweiterung_returns_only_active_infomail_erweiterung_users(self):
        make_portal_user(racf_id='AA01', infomail_erweiterung=True, email_kontakt='erw@example.com', status='aktiv')
        make_portal_user(racf_id='AA02', infomail_erweiterung=False, email_kontakt='noerw@example.com')
        make_portal_user(racf_id='AA03', infomail_erweiterung=True, email_kontakt='inaktiv@example.com', status='inaktiv')
        u1 = make_portal_user(racf_id='AA04', email_kontakt='other@example.com')
        response = self._post_action('infomail_erweiterung', [u1])  # selection is ignored
        content = response.content.decode('utf-8')
        self.assertIn('erw@example.com', content)
        self.assertNotIn('noerw@example.com', content)
        self.assertNotIn('inaktiv@example.com', content)


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
            'name', 'vorname', 'email_kontakt', 'user',
            'abteilung', 'funktion', 'eintritt_am', 'status',
            'intern', 'infomail_erweiterung', 'rolle', 'racf_id', 'typ_account',
            'ews', 'bkt', 'prod', 'benutzertyp', 'status_nb', 'bemerkung',
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    def _default_row(self, **kwargs):
        row = {
            'name': 'Muster', 'vorname': 'Max',
            'email_kontakt': 'k@example.com', 'user': 'u@example.com',
            'abteilung': 'AFR', 'funktion': '', 'eintritt_am': '2020-01-01',
            'status': 'aktiv', 'intern': 'True', 'infomail_erweiterung': 'True', 'rolle': 'Viewer',
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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PortalUser.objects.count(), 1)

    def test_import_updates_existing_user_by_user(self):
        make_portal_user(user='u@example.com', name='Alt')
        self._upload(self._make_csv([self._default_row(name='Neu')]))
        self.assertEqual(PortalUser.objects.count(), 1)
        self.assertEqual(PortalUser.objects.get(user='u@example.com').name, 'Neu')

    def test_import_accepts_german_date_format(self):
        self._upload(self._make_csv([self._default_row(eintritt_am='15.03.2021')]))
        self.assertEqual(PortalUser.objects.get(user='u@example.com').eintritt_am, date(2021, 3, 15))

    def test_import_invalid_date_reports_error_and_skips_row(self):
        response = self._upload(self._make_csv([self._default_row(eintritt_am='kein-datum')]))
        self.assertEqual(PortalUser.objects.count(), 0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['error_details']), 1)

    def test_import_no_file_reports_error(self):
        response = self.client.post(self.import_url, {}, follow=True)
        messages = [m.level_tag for m in response.context['messages']]
        self.assertIn('error', messages)

    def test_import_result_shows_counts(self):
        response = self._upload(self._make_csv([self._default_row()]))
        result = response.context['result']
        self.assertEqual(result['created'], 1)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(result['errors'], 0)
