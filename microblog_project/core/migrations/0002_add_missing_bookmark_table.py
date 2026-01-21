from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS core_bookmark (
                id BIGSERIAL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
                post_id BIGINT NOT NULL REFERENCES core_post(id) ON DELETE CASCADE,
                UNIQUE (user_id, post_id)
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS core_bookmark;"
        ),
    ]
