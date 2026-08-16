from django.db import migrations

EXPENSE_CATEGORIES = [
    "Food", "Groceries", "Transport", "Fuel", "Shopping", "Entertainment",
    "Bills", "Utilities", "Rent", "Education", "Healthcare", "Insurance",
    "Travel", "Subscriptions", "Personal Care", "Family", "Other",
]

INCOME_CATEGORIES = ["Salary", "Freelance", "Business", "Interest", "Investment", "Gift", "Other"]

CATEGORIZATION_RULES = [
    ("SWIGGY", "Food"), ("ZOMATO", "Food"), ("UBER EATS", "Food"),
    ("UBER", "Transport"), ("OLA", "Transport"), ("RAPIDO", "Transport"),
    ("NETFLIX", "Subscriptions"), ("SPOTIFY", "Subscriptions"), ("PRIME VIDEO", "Subscriptions"),
    ("AMAZON", "Shopping"), ("FLIPKART", "Shopping"), ("MYNTRA", "Shopping"),
    ("BIGBASKET", "Groceries"), ("BLINKIT", "Groceries"), ("ZEPTO", "Groceries"),
    ("ELECTRICITY", "Utilities"), ("BROADBAND", "Utilities"), ("WIFI", "Utilities"),
    ("HOSPITAL", "Healthcare"), ("PHARMACY", "Healthcare"), ("CLINIC", "Healthcare"),
    ("SALARY", "Salary"), ("PAYROLL", "Salary"),
]


def seed(apps, schema_editor):
    Category = apps.get_model("categories", "Category")
    CategoryRule = apps.get_model("categories", "CategoryRule")

    category_lookup = {}
    for name in EXPENSE_CATEGORIES:
        cat, _ = Category.objects.get_or_create(
            name=name, kind="expense", owner=None, defaults={"is_system_default": True}
        )
        category_lookup[("expense", name)] = cat

    for name in INCOME_CATEGORIES:
        cat, _ = Category.objects.get_or_create(
            name=name, kind="income", owner=None, defaults={"is_system_default": True}
        )
        category_lookup[("income", name)] = cat

    for keyword, category_name in CATEGORIZATION_RULES:
        category = category_lookup.get(("expense", category_name))
        if category:
            CategoryRule.objects.get_or_create(keyword=keyword, category=category, owner=None)


def unseed(apps, schema_editor):
    Category = apps.get_model("categories", "Category")
    Category.objects.filter(is_system_default=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("categories", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
