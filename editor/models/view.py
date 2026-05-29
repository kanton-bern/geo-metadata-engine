from django.db import models

class View(models.Model):
    name_view = models.CharField(max_length=255)
    beschreibung_de = models.TextField()
    dienste = models.ManyToManyField("Dienst", related_name="views", blank=True)
 
    def __str__(self):
        return self.name_view
 
    class Meta:
        verbose_name = "View"
        verbose_name_plural = "Views"
        ordering = ["name_view"]