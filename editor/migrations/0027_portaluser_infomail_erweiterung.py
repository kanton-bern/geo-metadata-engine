from django.db import migrations, models


def copy_intern_to_infomail_erweiterung(apps, schema_editor):
    PortalUser = apps.get_model('editor', 'PortalUser')
    PortalUser.objects.all().update(infomail_erweiterung=models.F('intern'))


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0026_remove_view_dienst_view_dienste'),
    ]

    operations = [
        migrations.AddField(
            model_name='portaluser',
            name='infomail_erweiterung',
            field=models.BooleanField(default=True, verbose_name='Infomail Erweiterung'),
        ),
        migrations.RunPython(
            copy_intern_to_infomail_erweiterung,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
