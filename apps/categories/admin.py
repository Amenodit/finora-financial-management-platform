from django.contrib import admin

from apps.categories.models import Category, CategoryRule


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "kind", "owner", "is_system_default"]
    list_filter = ["kind", "is_system_default"]
    search_fields = ["name"]


@admin.register(CategoryRule)
class CategoryRuleAdmin(admin.ModelAdmin):
    list_display = ["keyword", "category", "owner", "priority"]
    search_fields = ["keyword"]
