from .models import (
    Thema, Geopaeckli, Ebene, Attribut, Wertetabelle,
    Dienst, View, Tag, Trigger, PortalUser,
    # Map, App, Workflow — models bleiben erhalten, vorerst nicht registriert
)
from .models.portal_user import TYP_ACCOUNT_CHOICES
from django.contrib import admin
from django import forms
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from datetime import datetime
import csv
import io
from django.db import IntegrityError

admin.site.site_header = "GEO Metadaten Engine"
admin.site.site_title = "GEO Metadaten Engine"
admin.site.index_title = "Administration"


# ---------------------------------------------------------------------------
# Wertetabelle Inline — erscheint unter Attribut
# ---------------------------------------------------------------------------
class WertetabelleInline(admin.TabularInline):
    model = Attribut.wertetabellen.through
    extra = 0
    verbose_name = "Wertetabelle"
    verbose_name_plural = "Wertetabellen"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'wertetabelle':
            geop_id = _geopaeckli_id_from_request(request, 'attribut')
            if geop_id:
                kwargs['queryset'] = Wertetabelle.objects.filter(
                    geopaeckli_id=geop_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ---------------------------------------------------------------------------
# Attribut Inline — erscheint unter Geopäckli
# ---------------------------------------------------------------------------
class AttributInline(admin.StackedInline):
    model = Attribut
    extra = 0
    show_change_link = True
    fields = (
        'name_attribut', 'kurzbezeichnung_de', 'kurzbezeichnung_fr',
        'beschreibung_de', 'attributtyp', 'attributlaenge',
        'pflicht', 'unique', 'index',
    )


# ---------------------------------------------------------------------------
# Hilfsfunktion: Geopäckli-ID aus Request-Pfad lesen
# ---------------------------------------------------------------------------
def _geopaeckli_id_from_request(request, model_name):
    try:
        parts = request.path.strip('/').split('/')
        if 'change' in parts:
            pk = int(parts[parts.index('change') - 1])
            if model_name == 'attribut':
                obj = Attribut.objects.filter(pk=pk).first()
                return obj.geopaeckli_id if obj else None
            if model_name == 'ebene':
                obj = Ebene.objects.filter(pk=pk).first()
                return obj.geopaeckli_id if obj else None
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Ebene Form — filtert Attribut-Auswahl auf dasselbe Geopäckli
# ---------------------------------------------------------------------------
class EbeneForm(forms.ModelForm):
    class Meta:
        model = Ebene
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        geop_id = None

        if self.data.get('geopaeckli'):
            try:
                geop_id = int(self.data['geopaeckli'])
            except (ValueError, TypeError):
                pass

        if not geop_id and self.instance and self.instance.pk:
            geop_id = self.instance.geopaeckli_id

        if geop_id:
            self.fields['attribute'].queryset = Attribut.objects.filter(
                geopaeckli_id=geop_id
            )
        else:
            self.fields['attribute'].queryset = Attribut.objects.none()

    def clean(self):
        cleaned = super().clean()
        attribute = cleaned.get('attribute')
        geopaeckli = cleaned.get('geopaeckli')
        if attribute and geopaeckli:
            falsche = [a for a in attribute if a.geopaeckli != geopaeckli]
            if falsche:
                raise forms.ValidationError({
                    'attribute': (
                        "Folgende Attribute gehören nicht zum gewählten Geopäckli: "
                        + ", ".join(str(a) for a in falsche)
                    )
                })
        return cleaned


# ---------------------------------------------------------------------------
# Ebene
# ---------------------------------------------------------------------------
class EbeneAdmin(admin.ModelAdmin):
    form = EbeneForm
    list_display = ('name', 'geopaeckli', 'dienst', 'featurekategorie')
    list_filter = ('geopaeckli', 'featurekategorie', 'zugangsberechtigung')
    search_fields = ('name', 'titel_de')
    filter_horizontal = ('attribute', 'tags', 'triggers', 'views')
    fieldsets = (
        (None, {
            'fields': (
                'name', 'titel_de', 'titel_fr',
                'kurzbeschreibung_de', 'kurzbeschreibung_fr',
                'featurekategorie', 'zugangsberechtigung', 'foerderprogramm',
                'editierbar', 'datenstand_date', 'dokumentation',
                'geopaeckli', 'dienst',
            ),
        }),
        ('Attribute', {
            'fields': ('attribute',),
            'description': 'Nur Attribute des gewählten Geopäcklis werden angezeigt.',
        }),
        ('Tags', {
            'fields': ('tags',),
        }),
        ('Weitere Verknüpfungen', {
            'classes': ('collapse',),
            'fields': ('triggers', 'views'),
        }),
    )


# ---------------------------------------------------------------------------
# Attribut — mit Wertetabellen-Inline
# ---------------------------------------------------------------------------
class AttributAdmin(admin.ModelAdmin):
    inlines = [WertetabelleInline]
    list_display = ('name_attribut', 'geopaeckli',
                    'attributtyp', 'anzahl_wertetabellen')
    list_filter = ('geopaeckli', 'attributtyp')
    search_fields = ('name_attribut',)

    def anzahl_wertetabellen(self, obj):
        return obj.wertetabellen.count()
    anzahl_wertetabellen.short_description = "# Wertetabellen"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'geopaeckli':
            kwargs['queryset'] = Geopaeckli.objects.order_by('name_de')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ---------------------------------------------------------------------------
# Wertetabelle
# ---------------------------------------------------------------------------
class WertetabelleAdmin(admin.ModelAdmin):
    list_display = ('name_tabelle', 'geopaeckli', 'anzahl_attribute')
    list_filter = ('geopaeckli',)
    search_fields = ('name_tabelle',)

    def anzahl_attribute(self, obj):
        return obj.attribute.count()
    anzahl_attribute.short_description = "# Attribute"


# ---------------------------------------------------------------------------
# Geopäckli — Attribute als Inline
# ---------------------------------------------------------------------------
class GeopaeckliAdmin(admin.ModelAdmin):
    inlines = [AttributInline]
    list_display = ('name_de', 'technischer_name', 'thema')
    prepopulated_fields = {'technischer_name': ('name_de',)}
    search_fields = ('name_de', 'technischer_name')
    list_filter = ('thema',)


# ---------------------------------------------------------------------------
# Sonstige
# ---------------------------------------------------------------------------
class DienstAdmin(admin.ModelAdmin):
    list_display = ('technischer_name_dienst', 'name_dienst_de', 'owner')
    search_fields = ('technischer_name_dienst', 'name_dienst_de')


class TagAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_fr')
    search_fields = ('name_de',)

# ---------------------------------------------------------------------------
# View - Dienste als Filter & Anzahl Dienste anzeigen
# ---------------------------------------------------------------------------
class ViewAdmin(admin.ModelAdmin):
    filter_horizontal = ('dienste',)
    list_display = ('name_view', 'anzahl_dienste')
    search_fields = ('name_view',)
 
    def anzahl_dienste(self, obj):
        return obj.dienste.count()
    anzahl_dienste.short_description = "# Dienste"

# ---------------------------------------------------------------------------
# Portal User
# ---------------------------------------------------------------------------
class PortalUserAdminForm(forms.ModelForm):
    typ_account = forms.MultipleChoiceField(
        choices=TYP_ACCOUNT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = PortalUser
        fields = '__all__'



def _export_zu_bestellen_csv(system):
    def action(modeladmin, request, queryset):
        users = PortalUser.objects.filter(
            status='zu bestellen', **{system: True}
        ).order_by('name')
        response = HttpResponse(content_type='text/csv')
        filename = datetime.now().strftime('%Y_%m_%d') + \
            f'_GIS_Hub_Erfassung_User_AD_BE-Login_{system.upper()}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['User', 'Rolle', 'Benutzertyp',
                        'Vorname', 'Nachname', 'Benutzerkennung'])
        for u in users:
            writer.writerow([u.user, u.rolle, u.benutzertyp,
                            u.vorname, u.name, u.racf_id or ''])
        return response
    action.__name__ = f'export_zu_bestellen_{system}_csv'
    action.short_description = f'CSV Export: User zu bestellen ({system.upper()})'
    return action


export_zu_bestellen_ews_csv = _export_zu_bestellen_csv('ews')
export_zu_bestellen_bkt_csv = _export_zu_bestellen_csv('bkt')
export_zu_bestellen_prod_csv = _export_zu_bestellen_csv('prod')


def email_string_kontakt(modeladmin, request, queryset):
    addresses = queryset.order_by('name').values_list('email_kontakt', flat=True)
    return HttpResponse(';'.join(addresses), content_type='text/plain; charset=utf-8')


email_string_kontakt.short_description = 'E-Mail-String: Kontakt'


def infomail_stoerung(modeladmin, request, queryset):
    addresses = PortalUser.objects.exclude(status='inaktiv').order_by(
        'name').values_list('email_kontakt', flat=True)
    return HttpResponse(';'.join(addresses), content_type='text/plain; charset=utf-8')


infomail_stoerung.short_description = 'E-Mail-String: Störung (alle)'


def infomail_erweiterung(modeladmin, request, queryset):
    addresses = PortalUser.objects.filter(infomail_erweiterung=True).exclude(
        status='inaktiv').order_by('name').values_list('email_kontakt', flat=True)
    return HttpResponse(';'.join(addresses), content_type='text/plain; charset=utf-8')


infomail_erweiterung.short_description = 'E-Mail-String: Erweiterung'


def benutzerliste_erstellen(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Benutzerliste_GIS_Hub.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'name', 'vorname', 'email_kontakt', 'user',
        'abteilung', 'funktion', 'eintritt_am', 'status',
        'intern', 'infomail_erweiterung', 'rolle', 'racf_id', 'typ_account',
        'ews', 'bkt', 'prod', 'benutzertyp', 'status_nb', 'bemerkung',
    ])
    for u in queryset.order_by('name'):
        writer.writerow([
            u.name, u.vorname, u.email_kontakt, u.user,
            u.abteilung, u.funktion, u.eintritt_am, u.status,
            u.intern, u.infomail_erweiterung, u.rolle, u.racf_id or '',
            ','.join(u.typ_account),
            u.ews, u.bkt, u.prod, u.benutzertyp, u.status_nb, u.bemerkung,
        ])
    return response


benutzerliste_erstellen.short_description = 'CSV Export: Benutzerliste'


class PortalUserAdmin(admin.ModelAdmin):
    form = PortalUserAdminForm
    change_list_template = 'admin/editor/portaluser/change_list.html'
    actions = [
        export_zu_bestellen_ews_csv, export_zu_bestellen_bkt_csv, export_zu_bestellen_prod_csv,
        benutzerliste_erstellen, email_string_kontakt, infomail_stoerung, infomail_erweiterung,
    ]
    list_display = ('name', 'vorname', 'racf_id', 'user',
                    'abteilung', 'status', 'rolle', 'intern', "ews", "bkt", "prod")
    list_filter = ('status', 'abteilung', 'intern', 'infomail_erweiterung', 'rolle', 'ews', 'bkt', 'prod')
    search_fields = ('name', 'vorname', 'racf_id', 'user',
                     'status', 'typ_account')
    fieldsets = (
        (None, {
            'fields': ('name', 'vorname', 'email_kontakt', 'user'),
        }),
        ('Organisation', {
            'fields': ('abteilung', 'funktion', 'eintritt_am'),
        }),
        ('Status & Rolle', {
            'fields': ('status', 'intern', 'infomail_erweiterung', 'rolle'),
        }),
        ('Technisches', {
            'fields': ('racf_id', 'typ_account'),
        }),
        ('Systeme', {
            'fields': ('ews', 'bkt', 'prod'),
        }),
        ('Nutzungsbedingungen', {
            'fields': ('nb_pdf', 'status_nb'),
        }),
        ('Sonstiges', {
            'fields': ('bemerkung',),
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv_view),
                 name='portaluser_import_csv'),
        ]
        return custom_urls + urls

    def import_csv_view(self, request):
        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                self.message_user(
                    request, "Keine Datei ausgewählt.", level='error')
                return redirect(request.path)

            reader = csv.DictReader(io.StringIO(
                csv_file.read().decode('utf-8')))
            created = updated = errors = 0
            error_details = []
            updated_users = []

            def parse_bool(val):
                return str(val).strip().lower() in ('true', '1', 'ja', 'yes')

            for i, row in enumerate(reader, start=2):
                user_id = row.get('user', '').strip()
                label = user_id or f'Zeile {i}'
                try:
                    intern_raw = str(row.get('intern', 'True')).strip().lower()
                    intern = intern_raw in ('true', 'intern', '1', 'ja')

                    typ_account_raw = row.get('typ_account', '')
                    typ_account = [x.strip()
                                   for x in typ_account_raw.split(',') if x.strip()]

                    eintritt_raw = row.get('eintritt_am', '').strip()
                    eintritt_am = None
                    for fmt in ('%Y-%m-%d', '%d.%m.%Y'):
                        try:
                            eintritt_am = datetime.strptime(
                                eintritt_raw, fmt).date()
                            break
                        except ValueError:
                            continue
                    if eintritt_am is None:
                        raise ValueError(f"Ungültiges Datum: '{eintritt_raw}'")

                    if not user_id:
                        raise ValueError("Pflichtfeld 'user' fehlt oder ist leer")

                    _, was_created = PortalUser.objects.update_or_create(
                        user=user_id,
                        defaults={
                            'name': row['name'].strip(),
                            'vorname': row['vorname'].strip(),
                            'email_kontakt': row['email_kontakt'].strip(),
                            'abteilung': row['abteilung'].strip(),
                            'funktion': row.get('funktion', '').strip(),
                            'eintritt_am': eintritt_am,
                            'status': row['status'].strip(),
                            'intern': intern,
                            'infomail_erweiterung': parse_bool(row.get('infomail_erweiterung', True)),
                            'rolle': row['rolle'].strip(),
                            'racf_id': row.get('racf_id', '').strip() or None,
                            'typ_account': typ_account,
                            'ews': parse_bool(row.get('ews', False)),
                            'bkt': parse_bool(row.get('bkt', False)),
                            'prod': parse_bool(row.get('prod', False)),
                            'status_nb': row.get('status_nb', '').strip(),
                            'bemerkung': row.get('bemerkung', '').strip(),
                        },
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1
                        updated_users.append({
                            'user': user_id,
                            'name': f"{row.get('vorname', '').strip()} {row.get('name', '').strip()}".strip(),
                        })
                except IntegrityError as e:
                    errors += 1
                    cause = str(e.__cause__ or e)
                    if 'unique' in cause.lower() or 'duplicate' in cause.lower():
                        detail = next(
                            (l.replace('DETAIL:', '').strip() for l in cause.splitlines() if 'DETAIL:' in l),
                            'Doppelter Wert'
                        )
                        error_details.append({'zeile': i, 'label': label, 'grund': f"Doppelter Wert: {detail}"})
                    else:
                        error_details.append({'zeile': i, 'label': label, 'grund': f"Datenbankfehler: {cause.splitlines()[0]}"})
                except KeyError as e:
                    errors += 1
                    error_details.append({'zeile': i, 'label': label, 'grund': f"Pflichtfeld fehlt: {e}"})
                except ValueError as e:
                    errors += 1
                    error_details.append({'zeile': i, 'label': label, 'grund': str(e)})
                except Exception as e:
                    errors += 1
                    error_details.append({'zeile': i, 'label': label, 'grund': str(e).splitlines()[0]})

            return TemplateResponse(request, 'admin/editor/portaluser/import.html', {
                **self.admin_site.each_context(request),
                'title': 'Portal Users importieren',
                'opts': self.model._meta,
                'result': {'created': created, 'updated': updated, 'errors': errors},
                'error_details': error_details,
                'updated_users': updated_users,
            })

        return TemplateResponse(request, 'admin/editor/portaluser/import.html', {
            **self.admin_site.each_context(request),
            'title': 'Portal Users importieren',
            'opts': self.model._meta,
        })


# ---------------------------------------------------------------------------
# Registrierungen
# ---------------------------------------------------------------------------
admin.site.register(Thema)
admin.site.register(Geopaeckli, GeopaeckliAdmin)
admin.site.register(Ebene, EbeneAdmin)
admin.site.register(Attribut, AttributAdmin)
admin.site.register(Wertetabelle, WertetabelleAdmin)
admin.site.register(Dienst, DienstAdmin)
admin.site.register(View, ViewAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Trigger)
admin.site.register(PortalUser, PortalUserAdmin)
