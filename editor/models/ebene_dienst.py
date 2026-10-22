from django.db import models


class EbeneDienst(models.Model):
    """Zwischentabelle Ebene <-> Dienst.

    Bewusst als explizites through-Modell angelegt: Falls später Angaben
    pro Publikation dazukommen (Layername im Dienst, Reihenfolge,
    Sichtbarkeit, Publikationsdatum), werden sie hier als Felder ergänzt,
    ohne dass die Beziehung nochmals umgebaut werden muss.
    """

    ebene = models.ForeignKey("Ebene", on_delete=models.CASCADE)
    dienst = models.ForeignKey("Dienst", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.ebene} -> {self.dienst}"

    class Meta:
        verbose_name = "Ebene-Dienst-Zuordnung"
        verbose_name_plural = "Ebene-Dienst-Zuordnungen"
        constraints = [
            models.UniqueConstraint(
                fields=["ebene", "dienst"], name="uq_ebene_dienst"
            )
        ]
