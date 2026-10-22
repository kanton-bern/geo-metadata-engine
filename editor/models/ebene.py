from django.db import models


class Ebene(models.Model):
    ZUGANGS_CHOICES = [
        ('A', 'öffentlich zugängliche Geodaten'),
        ('B', 'beschränkt öffentlich zugängliche Geodaten'),
        ('C', 'nicht öffentlich zugängliche Geodaten'),
    ]
    FEATUREKAT_CHOICES = [
        ('Raster', 'Raster'),
        ('Vektor', 'Vektor'),
        ('Tabelle', 'Tabelle'),
    ]
    FOERDERPROGRAMM_CHOICES = [
        ('NFA', 'NFA'),
        ('Kantonales Förderprogramm', 'Kantonales Förderprogramm'),
        ('ohne staatliche Förderung', 'ohne staatliche Förderung'),
        ('---', '---'),
    ]

    name = models.CharField(max_length=100)
    titel_de = models.CharField(max_length=200)
    titel_fr = models.CharField(max_length=200)
    kurzbeschreibung_de = models.TextField()
    kurzbeschreibung_fr = models.TextField()
    editierbar = models.BooleanField()
    featurekategorie = models.CharField(max_length=50, choices=FEATUREKAT_CHOICES)
    zugangsberechtigung = models.CharField(max_length=1, choices=ZUGANGS_CHOICES)
    foerderprogramm = models.CharField(
        max_length=100, choices=FOERDERPROGRAMM_CHOICES, default='---'
    )
    dokumentation = models.TextField(blank=True, null=True)
    datenstand_date = models.DateField()
    geopaeckli = models.ForeignKey(
        "Geopaeckli", on_delete=models.CASCADE, related_name="ebenen"
    )
    # Eine Ebene kann in mehreren Diensten publiziert sein (und umgekehrt).
    # Führender Pfad für den Dienstbezug; vgl. Entscheid Okt. 2026.
    dienste = models.ManyToManyField(
        "Dienst",
        through="EbeneDienst",
        related_name="ebenen",
        blank=True,
    )
    tags = models.ManyToManyField("Tag", related_name="ebenen", blank=True)
    triggers = models.ManyToManyField("Trigger", related_name="ebenen", blank=True)
    views = models.ManyToManyField("View", related_name="ebenen", blank=True)
    # Attribute leben am Geopäckli; M2M hier = Zuweisung, kein Besitz.
    # Attribut überlebt die Löschung einer Ebene.
    attribute = models.ManyToManyField(
        "Attribut",
        related_name="ebenen",
        blank=True,
    )

    def __str__(self):
        return f"{self.name} ({self.geopaeckli})"

    class Meta:
        verbose_name = "Ebene"
        verbose_name_plural = "Ebenen"
        ordering = ["titel_de"]
