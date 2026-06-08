import django.core.validators
from django.db import migrations, models


def drop_pk_and_add_id(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        # Find the actual PK constraint name (avoids hardcoding it)
        cursor.execute("""
            SELECT conname FROM pg_constraint
            WHERE conrelid = 'editor_portaluser'::regclass AND contype = 'p'
        """)
        row = cursor.fetchone()
        if row:
            cursor.execute(f'ALTER TABLE "editor_portaluser" DROP CONSTRAINT "{row[0]}"')
        cursor.execute('ALTER TABLE "editor_portaluser" ALTER COLUMN "racf_id" DROP NOT NULL')
        cursor.execute('ALTER TABLE "editor_portaluser" ADD COLUMN "id" BIGSERIAL PRIMARY KEY')


def restore_pk(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('ALTER TABLE "editor_portaluser" DROP CONSTRAINT "editor_portaluser_pkey"')
        cursor.execute('ALTER TABLE "editor_portaluser" DROP COLUMN "id"')
        cursor.execute('ALTER TABLE "editor_portaluser" ALTER COLUMN "racf_id" SET NOT NULL')
        cursor.execute('ALTER TABLE "editor_portaluser" ADD PRIMARY KEY ("racf_id")')


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0027_portaluser_infomail_erweiterung'),
    ]

    operations = [
        # Rename email_user → user (preserves all data)
        migrations.RenameField(
            model_name='portaluser',
            old_name='email_user',
            new_name='user',
        ),
        # Change user from EmailField to CharField and add unique constraint
        migrations.AlterField(
            model_name='portaluser',
            name='user',
            field=models.CharField(max_length=254, unique=True),
        ),
        # Handle PK swap via RunPython to dynamically find the constraint name
        migrations.RunPython(
            drop_pk_and_add_id,
            reverse_code=restore_pk,
        ),
        # Update migration state to match the DB changes above
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='portaluser',
                    name='racf_id',
                    field=models.CharField(
                        blank=True,
                        max_length=4,
                        null=True,
                        validators=[django.core.validators.MinLengthValidator(4)],
                        verbose_name='RACF-ID',
                    ),
                ),
                migrations.AddField(
                    model_name='portaluser',
                    name='id',
                    field=models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
            ],
            database_operations=[],
        ),
        # Update funktion: optional, new choices, larger max_length
        migrations.AlterField(
            model_name='portaluser',
            name='funktion',
            field=models.CharField(
                blank=True,
                choices=[
                    ('Staatsförster', 'Staatsförster'),
                    ('Gemeindeförster', 'Gemeindeförster'),
                    ('Forstfachperson Kliwa', 'Forstfachperson Kliwa'),
                    ('Käfervogt', 'Käfervogt'),
                    ('andere', 'andere (siehe Bemerkung)'),
                ],
                max_length=30,
            ),
        ),
        # Add Extern to abteilung choices
        migrations.AlterField(
            model_name='portaluser',
            name='abteilung',
            field=models.CharField(
                choices=[
                    ('AFR', 'AFR'),
                    ('WAA', 'WAA'),
                    ('WAV', 'WAV'),
                    ('WAM', 'WAM'),
                    ('WABJ', 'WABJ'),
                    ('AWE', 'AWE'),
                    ('SFB', 'SFB'),
                    ('NGA', 'NGA'),
                    ('Extern', 'Extern'),
                ],
                max_length=10,
            ),
        ),
    ]
