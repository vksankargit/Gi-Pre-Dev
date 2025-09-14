from django import forms
from .models import Organization, Team
from accounts.models import User


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter organization name',
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = "Organization Name"


class TeamForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        help_text="Select team members"
    )

    class Meta:
        model = Team
        fields = ['name', 'organization', 'manager', 'members']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter team name',
            }),
            'organization': forms.Select(attrs={
                'class': 'form-control',
            }),
            'manager': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter organizations based on user role
        if self.user:
            if self.user.role == 'admin':
                self.fields['organization'].queryset = Organization.objects.filter(is_active=True)
            elif self.user.role == 'coordinator':
                # Show only organizations this coordinator manages
                self.fields['organization'].queryset = Organization.objects.filter(
                    coordinators__coordinator=self.user,
                    coordinators__is_active=True,
                    is_active=True
                )

        # Show only general users as potential managers and members
        general_users = User.objects.filter(role='general', is_active=True)
        self.fields['manager'].queryset = general_users
        self.fields['members'].queryset = general_users

        # If editing existing team, populate current members
        if self.instance and self.instance.pk:
            current_members = self.instance.members.filter(is_active=True).values_list('member_id', flat=True)
            self.fields['members'].initial = current_members

    def save(self, commit=True):
        team = super().save(commit=commit)

        if commit and 'members' in self.cleaned_data:
            # Clear existing memberships
            team.members.all().update(is_active=False)

            # Add selected members
            selected_members = self.cleaned_data['members']
            for member in selected_members:
                from .models import TeamMember
                team_member, created = TeamMember.objects.get_or_create(
                    team=team,
                    member=member,
                    defaults={'is_active': True}
                )
                if not created:
                    team_member.is_active = True
                    team_member.save()

        return team