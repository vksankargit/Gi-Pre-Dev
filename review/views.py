from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import ReviewMeeting, ReviewParticipant, ReviewNote, ReviewDecision, ReviewAction, ReviewIssue
from organizations.models import Team
from implement.models import Action, Issue


class ReviewHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'review/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get teams where user is manager
        managed_teams = Team.objects.filter(manager=user, is_active=True)
        
        # Get recent review meetings
        recent_reviews = ReviewMeeting.objects.filter(
            team__in=managed_teams
        ).select_related('team', 'manager').order_by('-meeting_date')[:10]
        
        context.update({
            'managed_teams': managed_teams,
            'recent_reviews': recent_reviews,
            'review_types': [('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Handle search functionality
        team_id = request.POST.get('team')
        review_type = request.POST.get('review_type')
        month_year = request.POST.get('month_year')
        
        context = self.get_context_data()
        
        # Filter reviews based on search criteria
        reviews = ReviewMeeting.objects.filter(team__manager=request.user)
        
        if team_id:
            reviews = reviews.filter(team_id=team_id)
        if review_type:
            reviews = reviews.filter(review_type=review_type)
        # Add month_year filtering logic here
        
        context['filtered_reviews'] = reviews.select_related('team', 'manager').order_by('-meeting_date')
        
        return render(request, self.template_name, context)


class ReviewCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'review/create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        managed_teams = Team.objects.filter(manager=user, is_active=True)
        review_types = [('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')]
        
        context.update({
            'managed_teams': managed_teams,
            'review_types': review_types,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        team_id = request.POST.get('team')
        review_type = request.POST.get('review_type')
        meeting_date = request.POST.get('meeting_date')
        manager_name = request.POST.get('manager_name')
        participants = request.POST.getlist('participants')
        
        if not all([team_id, review_type, meeting_date]):
            messages.error(request, 'Please fill all required fields.')
            return self.get(request, *args, **kwargs)
        
        team = get_object_or_404(Team, id=team_id, manager=request.user)
        
        # Create review meeting
        review_meeting = ReviewMeeting.objects.create(
            team=team,
            review_type=review_type,
            meeting_date=meeting_date,
            manager=request.user,
            created_by=request.user
        )
        
        # Add participants
        for participant_id in participants:
            if participant_id:
                ReviewParticipant.objects.create(
                    review_meeting=review_meeting,
                    participant_id=participant_id
                )
        
        messages.success(request, 'Review meeting created successfully.')
        return redirect('review:meeting', pk=review_meeting.pk)


class ReviewMeetingView(LoginRequiredMixin, TemplateView):
    template_name = 'review/meeting.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review_meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])
        
        # Check if user has access to this review
        if review_meeting.team.manager != self.request.user:
            messages.error(self.request, 'Access denied.')
            return context
        
        # Get all related data
        commitments = Action.objects.filter(
            team=review_meeting.team,
            status__in=['not_started', 'in_progress', 'at_risk', 'danger', 'done']
        ).order_by('original_due_date')
        
        context.update({
            'review_meeting': review_meeting,
            'participants': review_meeting.participants.all(),
            'commitments': commitments,
            'notes': review_meeting.notes.all().order_by('serial_number'),
            'decisions': review_meeting.decisions.all().order_by('serial_number'),
            'actions': review_meeting.review_actions.all(),
            'issues': review_meeting.review_issues.all(),
        })
        
        return context


class ReviewParticipantsView(LoginRequiredMixin, TemplateView):
    template_name = 'review/participants.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review_meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])
        
        context.update({
            'review_meeting': review_meeting,
            'participants': review_meeting.participants.all(),
        })
        
        return context


class ReviewNotesView(LoginRequiredMixin, TemplateView):
    template_name = 'review/notes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review_meeting = get_object_or_404(ReviewMeeting, pk=kwargs['meeting_id'])
        
        context.update({
            'review_meeting': review_meeting,
            'notes': review_meeting.notes.all().order_by('serial_number'),
        })
        
        return context
    
    def post(self, request, meeting_id):
        review_meeting = get_object_or_404(ReviewMeeting, pk=meeting_id)
        action = request.POST.get('action')
        
        if action == 'add':
            note_text = request.POST.get('note')
            if note_text:
                # Get next serial number
                last_note = review_meeting.notes.order_by('-serial_number').first()
                next_serial = (last_note.serial_number + 1) if last_note else 1
                
                ReviewNote.objects.create(
                    review_meeting=review_meeting,
                    serial_number=next_serial,
                    note=note_text
                )
                messages.success(request, 'Note added successfully.')
        
        elif action == 'edit':
            note_id = request.POST.get('note_id')
            note_text = request.POST.get('note')
            try:
                note = ReviewNote.objects.get(id=note_id, review_meeting=review_meeting)
                note.note = note_text
                note.save()
                messages.success(request, 'Note updated successfully.')
            except ReviewNote.DoesNotExist:
                messages.error(request, 'Note not found.')
        
        elif action == 'delete':
            note_id = request.POST.get('note_id')
            try:
                note = ReviewNote.objects.get(id=note_id, review_meeting=review_meeting)
                note.delete()
                # Renumber remaining notes
                remaining_notes = review_meeting.notes.order_by('serial_number')
                for i, remaining_note in enumerate(remaining_notes, 1):
                    remaining_note.serial_number = i
                    remaining_note.save()
                messages.success(request, 'Note deleted successfully.')
            except ReviewNote.DoesNotExist:
                messages.error(request, 'Note not found.')
        
        return redirect('review:notes', meeting_id=meeting_id)


class ReviewDecisionsView(LoginRequiredMixin, TemplateView):
    template_name = 'review/decisions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review_meeting = get_object_or_404(ReviewMeeting, pk=kwargs['meeting_id'])
        
        context.update({
            'review_meeting': review_meeting,
            'decisions': review_meeting.decisions.all().order_by('serial_number'),
        })
        
        return context
    
    def post(self, request, meeting_id):
        review_meeting = get_object_or_404(ReviewMeeting, pk=meeting_id)
        action = request.POST.get('action')
        
        if action == 'add':
            decision_text = request.POST.get('decision')
            if decision_text:
                # Get next serial number
                last_decision = review_meeting.decisions.order_by('-serial_number').first()
                next_serial = (last_decision.serial_number + 1) if last_decision else 1
                
                ReviewDecision.objects.create(
                    review_meeting=review_meeting,
                    serial_number=next_serial,
                    decision=decision_text
                )
                messages.success(request, 'Decision added successfully.')
        
        # Similar logic for edit and delete as in notes
        
        return redirect('review:decisions', meeting_id=meeting_id)


class ReviewActionsView(LoginRequiredMixin, TemplateView):
    template_name = 'review/actions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review_meeting = get_object_or_404(ReviewMeeting, pk=kwargs['meeting_id'])
        
        context.update({
            'review_meeting': review_meeting,
            'actions': review_meeting.review_actions.all(),
        })
        
        return context


class ReviewIssuesView(LoginRequiredMixin, TemplateView):
    template_name = 'review/issues.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review_meeting = get_object_or_404(ReviewMeeting, pk=kwargs['meeting_id'])
        
        context.update({
            'review_meeting': review_meeting,
            'issues': review_meeting.review_issues.all(),
        })
        
        return context