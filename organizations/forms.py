from django import forms
from .models import Organization, Team, TeamMeetingType
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
        required=True,
        help_text="Select at least one team meeting member (required)"
    )

    class Meta:
        model = Team
        fields = ['name', 'organization', 'meeting_type', 'cadence',
                  'day_of_week', 'week_number', 'month_in_quarter', 'quarter', 'meeting_time',
                  'manager', 'members']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter team meeting name',
            }),
            'organization': forms.Select(attrs={
                'class': 'form-control',
            }),
            'meeting_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'cadence': forms.Select(attrs={
                'class': 'form-control',
            }),
            'day_of_week': forms.Select(attrs={
                'class': 'form-control',
            }),
            'week_number': forms.Select(attrs={
                'class': 'form-control',
            }),
            'month_in_quarter': forms.Select(attrs={
                'class': 'form-control',
            }),
            'quarter': forms.Select(attrs={
                'class': 'form-control',
            }),
            'meeting_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
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

        # Filter meeting types based on selected organization
        # When form is bound (has data), we need to include ALL active meeting types
        # because meeting types are loaded dynamically via AJAX when organization is selected
        if self.instance and self.instance.pk and self.instance.organization:
            self.fields['meeting_type'].queryset = TeamMeetingType.objects.filter(
                organization=self.instance.organization,
                is_active=True
            )
        elif self.is_bound and self.data.get('organization'):
            # For new teams, include meeting types for the selected organization
            self.fields['meeting_type'].queryset = TeamMeetingType.objects.filter(
                organization_id=self.data.get('organization'),
                is_active=True
            )
        else:
            self.fields['meeting_type'].queryset = TeamMeetingType.objects.none()

        # Show only general users as potential managers and members
        # When form is bound (has data), we need to include ALL general users
        # because members may be loaded dynamically via AJAX
        general_users = User.objects.filter(role='general', is_active=True)
        self.fields['manager'].queryset = general_users

        # For members, always use all general users queryset to handle dynamic loading
        self.fields['members'].queryset = general_users

        # Make scheduling fields not required initially (will be validated based on cadence)
        self.fields['meeting_type'].required = False
        self.fields['cadence'].required = False
        self.fields['day_of_week'].required = False
        self.fields['week_number'].required = False
        self.fields['month_in_quarter'].required = False
        self.fields['quarter'].required = False
        self.fields['meeting_time'].required = False

        # If editing existing team, populate current members
        if self.instance and self.instance.pk:
            current_members = self.instance.members.filter(is_active=True).values_list('member_id', flat=True)
            self.fields['members'].initial = current_members

    def clean_members(self):
        members = self.cleaned_data.get('members')
        if not members:
            raise forms.ValidationError("At least one team meeting member is required.")
        return members

    def clean(self):
        cleaned_data = super().clean()
        manager = cleaned_data.get('manager')
        members = cleaned_data.get('members')
        cadence = cleaned_data.get('cadence')

        if manager and members and manager in members:
            raise forms.ValidationError("The team meeting manager cannot be included in the team meeting members list.")

        # Validate scheduling fields based on cadence
        if cadence:
            if cadence == 'weekly':
                if cleaned_data.get('day_of_week') is None:
                    raise forms.ValidationError("Day of the week is required for weekly cadence.")

            elif cadence == 'monthly':
                if not cleaned_data.get('week_number'):
                    raise forms.ValidationError("Week number is required for monthly cadence.")
                if cleaned_data.get('day_of_week') is None:
                    raise forms.ValidationError("Day of the week is required for monthly cadence.")

            elif cadence == 'quarterly':
                if not cleaned_data.get('month_in_quarter'):
                    raise forms.ValidationError("Month in quarter is required for quarterly cadence.")
                if not cleaned_data.get('week_number'):
                    raise forms.ValidationError("Week number is required for quarterly cadence.")
                if cleaned_data.get('day_of_week') is None:
                    raise forms.ValidationError("Day of the week is required for quarterly cadence.")

            elif cadence == 'annually':
                if not cleaned_data.get('quarter'):
                    raise forms.ValidationError("Quarter is required for annual cadence.")
                if not cleaned_data.get('month_in_quarter'):
                    raise forms.ValidationError("Month in quarter is required for annual cadence.")
                if not cleaned_data.get('week_number'):
                    raise forms.ValidationError("Week number is required for annual cadence.")
                if cleaned_data.get('day_of_week') is None:
                    raise forms.ValidationError("Day of the week is required for annual cadence.")

        return cleaned_data

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