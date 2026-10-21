# Handgeschriebene Migration: Zwischentabelle EbeneDienst + M2M Ebene.dienste.
# Der bestehende FK Ebene.dienst bleibt vorerst stehen (wird in 0034 entfernt).
# Der AlterField-Schritt ändert nur den related_name (state-only, kein SQL),
# damit FK und M2M während der Übergangsphase nicht beide "ebenen" heissen.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("editor", "0031_alter_portaluser_racf_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ebene",
            name="dienst",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ebenen_alt",
                to="editor.dienst",
            ),
        ),
        migrations.CreateModel(
            name="EbeneDienst",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "dienst",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="editor.dienst",
                    ),
                ),
                (
                    "ebene",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="editor.ebene",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ebene-Dienst-Zuordnung",
                "verbose_name_plural": "Ebene-Dienst-Zuordnungen",
            },
        ),
        migrations.AddField(
            model_name="ebene",
            name="dienste",
            field=models.ManyToManyField(
                blank=True,
                related_name="ebenen",
                through="editor.EbeneDienst",
                to="editor.dienst",
            ),
        ),
        migrations.AddConstraint(
            model_name="ebenedienst",
            constraint=models.UniqueConstraint(
                fields=("ebene", "dienst"), name="uq_ebene_dienst"
            ),
        ),
    ]