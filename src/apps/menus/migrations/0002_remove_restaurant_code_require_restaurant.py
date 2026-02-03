from django.db import migrations, models
import django.db.models.deletion


def backfill_restaurant(apps, schema_editor):
    Menu = apps.get_model("menus", "Menu")
    Restaurant = apps.get_model("menus", "Restaurant")
    if Menu.objects.filter(restaurant__isnull=True).exists():
        default_restaurant, _ = Restaurant.objects.get_or_create(
            name="(마이그레이션 기본값)",
            defaults={"category": ""},
        )
        Menu.objects.filter(restaurant__isnull=True).update(restaurant=default_restaurant)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("menus", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill_restaurant, noop),
        migrations.AlterField(
            model_name="menu",
            name="restaurant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="menus",
                to="menus.restaurant",
                verbose_name="레스토랑",
            ),
        ),
        migrations.RemoveIndex(
            model_name="menu",
            name="menus_restaur_cd7c28_idx",
        ),
        migrations.RemoveField(
            model_name="menu",
            name="restaurant_code",
        ),
        migrations.AddIndex(
            model_name="menu",
            index=models.Index(fields=["restaurant", "-created_at"], name="menus_restaur_restaur_idx"),
        ),
    ]
