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
    ('Extern', 'Extern'),
]

FUNKTION_CHOICES = [
    ('Staatsförster', 'Staatsförster'),
    ('Gemeindeförster', 'Gemeindeförster'),
    ('Forstfachperson Kliwa', 'Forstfachperson Kliwa'),
    ('Käfervogt', 'Käfervogt'),
    ('andere', 'andere (siehe Bemerkung)'),
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


class PortalUser(models.Model):
    name = models.CharField(max_length=200)
    vorname = models.CharField(max_length=200)
    email_kontakt = models.EmailField()
    user = models.CharField(max_length=254, unique=True)
    abteilung = models.CharField(max_length=10, choices=ABTEILUNG_CHOICES)
    funktion = models.CharField(
        max_length=30, choices=FUNKTION_CHOICES, blank=True)
    eintritt_am = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    intern = models.BooleanField("Intern", default=True)
    infomail_erweiterung = models.BooleanField(
        "Infomail Erweiterung", default=True)
    rolle = models.CharField(max_length=20, choices=ROLLE_CHOICES)
    racf_id = models.CharField("RACF-ID",
                               max_length=20,
                               blank=True,
                               null=True,
                               validators=[MinLengthValidator(4)],
                               )
    typ_account = ArrayField(
        models.CharField(max_length=20, choices=TYP_ACCOUNT_CHOICES),
        blank=True,
        default=list,
    )
    ews = models.BooleanField("EWS", default=False)
    bkt = models.BooleanField("BKT", default=False)
    prod = models.BooleanField("PROD", default=False)
    benutzertyp = models.CharField(
        max_length=50, default='Creator', editable=False)
    nb_pdf = models.FileField(
        "Nutzungsbedingungen PDF", upload_to='nb_pdfs/', blank=True, null=True)
    status_nb = models.CharField(
        "Status Nutzungsbedingungen", max_length=200, blank=True)
    bemerkung = models.TextField(blank=True)

    class Meta:
        verbose_name = "Portal User"
        verbose_name_plural = "Portal Users"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=['racf_id'],
                condition=models.Q(racf_id__isnull=False),
                name='unique_racf_id_when_not_null',
            )
        ]

    def __str__(self):
        return f"{self.vorname} {self.name} ({self.user})"
