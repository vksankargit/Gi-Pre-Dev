from django.db import models
from django.conf import settings


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations'
        ordering = ['name']
        
    def __str__(self):
        return self.name


class OrganizationCoordinator(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='coordinators')
    coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coordinated_organizations')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'organization_coordinators'
        unique_together = ['organization', 'coordinator']
        
    def __str__(self):
        return f"{self.coordinator.get_full_name()} - {self.organization.name}"


class Team(models.Model):
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='teams')
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='managed_teams')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'teams'
        unique_together = ['organization', 'name']
        ordering = ['organization', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='team_memberships')
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'team_members'
        unique_together = ['team', 'member']
        
    def __str__(self):
        return f"{self.member.get_full_name()} - {self.team.name}"