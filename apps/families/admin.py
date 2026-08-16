from django.contrib import admin

from apps.families.models import Family, FamilyInvitation, FamilyMembership


class MembershipInline(admin.TabularInline):
    model = FamilyMembership
    extra = 0


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "created_at"]
    search_fields = ["name", "owner__email"]
    inlines = [MembershipInline]


@admin.register(FamilyInvitation)
class FamilyInvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "family", "role", "status", "expires_at"]
    list_filter = ["status", "role"]
