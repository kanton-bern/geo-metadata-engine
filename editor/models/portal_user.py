from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinLengthValidator
from django.db import models

STATUS_CHOICES = [
    ('zu bestellen', 'zu bestellen'),
    ('bestellt', 'bestellt'),
    ('aktiv', 'aktiv'),
    ('zu löschen', 'zu löschen'),
    ('inaktiv', 'inaktiv'),
]

ABTEILUNG_CHOICES = [
    ('AFR', 'AFR'),
    ('WAA', 'WAA'),
    ('WAV', 'WAV'),
    ('WAM', 'WAM'),
    ('WABJ', 'WABJ'),
    ('AWE', 'AWE'),
    ('SFB', 'SFB'),
    ('NGA', 'NGA'),
]

FUNKTION_CHOICES = [
    ('Hauptförster', 'Hauptförster'),
    ('Nebenförster', 'Nebenförster'),
    ('Käfervogt', 'Käfervogt'),
    ('Kontroller', 'Kontroller'),
]

ROLLE_CHOICES = [
    ('Viewer', 'Viewer'),
    ('Dateneditor', 'Dateneditor'),
    ('Publisher', 'Publisher'),
]

TYP_ACCOUNT_CHOICES = [
    ('AD', 'AD'),
    ('BE-Login', 'BE-Login'),
    ('Built-In', 'Built-In'),
]

TYP_INFOMAIL_CHOICES = [
    ('Störung', 'Störung'),
    ('Erweiterung/Störung', 'Erweiterung/Störung'),
]


class PortalUser(models.Model):
    name = models.CharField(max_length=100)
    vorname = models.CharField(max_length=100)
    email_kontakt = models.EmailField()
    email_user = models.EmailField()
    abteilung = models.CharField(max_length=10, choices=ABTEILUNG_CHOICES)
    funktion = models.CharField(
        max_length=20, choices=FUNKTION_CHOICES, blank=True)
    eintritt_am = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    intern = models.BooleanField("Intern", default=True)
    rolle = models.CharField(max_length=20, choices=ROLLE_CHOICES)
    racf_id = models.CharField("RACF-ID",
                               max_length=4,
                               validators=[MinLengthValidator(4)],
                               )
    typ_account = ArrayField(
        models.CharField(max_length=20, choices=TYP_ACCOUNT_CHOICES),
        blank=True,
        default=list,
    )
    typ_infomail = models.CharField(
        max_length=30, choices=TYP_INFOMAIL_CHOICES)
    ews = models.BooleanField("EWS", default=False)
    bkt = models.BooleanField("BKT", default=False)
    prod = models.BooleanField("PROD", default=False)
    benutzertyp = models.CharField(
        max_length=50, default='Creator', editable=False)
    nb_pdf = models.FileField(
        "Nutzungsbedingungen PDF", upload_to='nb_pdfs/', blank=True, null=True)
    status_nb = models.CharField(
        "Status Nutzungsbedingungen", max_length=100, blank=True)
    bemerkung = models.TextField(blank=True)

    class Meta:
        verbose_name = "Portal User"
        verbose_name_plural = "Portal Users"
        ordering = ["name"]

    def __str__(self):
        return f"{self.vorname} {self.name} ({self.racf_id})"

    def save(self, *args, **kwargs):
        self.typ_infomail = 'Erweiterung/Störung' if self.intern else 'Störung'
        super().save(*args, **kwargs)
