from django.contrib import admin
from .models import Organization, OrganizationCoordinator, Team, TeamMember, TeamMeetingType


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(OrganizationCoordinator)
class OrganizationCoordinatorAdmin(admin.ModelAdmin):
    list_display = ('organization', 'coordinator', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'organization')
    search_fields = ('organization__name', 'coordinator__username', 'coordinator__email')
    ordering = ('organization', 'coordinator')


@admin.register(TeamMeetingType)
class TeamMeetingTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'is_active', 'created_at')
    list_filter = ('is_active', 'organization')
    search_fields = ('name', 'organization__name')
    ordering = ('organization', 'name')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'meeting_type', 'cadence', 'manager', 'is_active', 'created_at')
    list_filter = ('is_active', 'cadence', 'created_at', 'organization', 'meeting_type')
    search_fields = ('name', 'organization__name', 'manager__username')
    ordering = ('organization', 'name')


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('team', 'member', 'is_active', 'joined_at')
    list_filter = ('is_active', 'joined_at', 'team__organization')
    search_fields = ('team__name', 'member__username', 'member__email')
    ordering = ('team', 'member')