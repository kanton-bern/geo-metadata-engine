# Datenmigration: kopiert den bestehenden FK Ebene.dienst in die neue
# Zwischentabelle EbeneDienst. Der FK selbst wird erst in 0034 entfernt.
#
# Rückweg (backwards) ist verlustbehaftet, sobald eine Ebene mehrere
# Dienste hat: pro Ebene bleibt dann nur der Dienst mit der kleinsten
# EbeneDienst-ID erhalten.

from django.db import migrations


def forwards(apps, schema_editor):
    Ebene = apps.get_model("editor", "Ebene")
    EbeneDienst = apps.get_model("editor", "EbeneDienst")
    EbeneDienst.objects.bulk_create(
        [
            EbeneDienst(ebene_id=e.pk, dienst_id=e.dienst_id)
            for e in Ebene.objects.exclude(dienst__isnull=True).only("pk", "dienst_id")
        ],
        ignore_conflicts=True,
    )


def backwards(apps, schema_editor):
    Ebene = apps.get_model("editor", "Ebene")
    EbeneDienst = apps.get_model("editor", "EbeneDienst")
    for ed in EbeneDienst.objects.order_by("ebene_id", "pk"):
        Ebene.objects.filter(pk=ed.ebene_id, dienst__isnull=True).update(
            dienst_id=ed.dienst_id
        )


class Migration(migrations.Migration):

    dependencies = [
        ("editor", "0032_ebenedienst_m2m"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]