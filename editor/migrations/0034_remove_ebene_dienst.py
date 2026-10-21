# Entfernt den alten FK Ebene.dienst. Ab hier ist Ebene.dienste (M2M über
# EbeneDienst) der einzige und führende Dienstbezug der Ebene.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("editor", "0033_copy_dienst_to_m2m"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="ebene",
            name="dienst",
        ),
    ]