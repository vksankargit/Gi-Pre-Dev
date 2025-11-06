
class UpdateProjectStatusView(LoginRequiredMixin, View):
    """Handle project status updates for PPI and Improvement projects"""

    def post(self, request, pk):
        meeting = get_object_or_404(ReviewMeeting, pk=pk)

        project_id = request.POST.get('project_id')
        project_type = request.POST.get('project_type')
        action = request.POST.get('action')  # complete, undo, hold, resume, drop, activate

        try:
            if project_type == 'PPI':
                from plans.models import PPIProject
                from implement.models import ProjectStatus

                project = PPIProject.objects.get(id=project_id)

                # Get the latest status record
                latest_status_obj = ProjectStatus.objects.filter(
                    project=project
                ).order_by('-updated_at').first()

                # Get previous status (second latest)
                previous_status_obj = ProjectStatus.objects.filter(
                    project=project
                ).order_by('-updated_at')[1:2].first()

                previous_status = previous_status_obj.status if previous_status_obj else 'on_track'

                # Determine new status based on action
                if action == 'complete':
                    new_status = 'completed'
                elif action == 'undo':
                    new_status = previous_status
                elif action == 'hold':
                    new_status = 'on_hold'
                elif action == 'resume':
                    new_status = previous_status
                elif action == 'drop':
                    new_status = 'dropped'
                elif action == 'activate':
                    new_status = previous_status
                else:
                    return JsonResponse({'success': False, 'error': 'Invalid action'})

                # Create new status record
                ProjectStatus.objects.create(
                    project=project,
                    status=new_status,
                    completion_percentage=latest_status_obj.completion_percentage if latest_status_obj else 0,
                    revised_due_date=latest_status_obj.revised_due_date if latest_status_obj else None,
                    challenge='',
                    comments=f'Status changed to {new_status} via review meeting',
                    updated_by=request.user
                )

            elif project_type == 'Improvement':
                from improve.models import ImprovementProject, ImprovementProjectStatus

                project = ImprovementProject.objects.get(id=project_id)

                # Get the latest status record
                latest_status_obj = ImprovementProjectStatus.objects.filter(
                    project=project
                ).order_by('-updated_at').first()

                # Get previous status (second latest)
                previous_status_obj = ImprovementProjectStatus.objects.filter(
                    project=project
                ).order_by('-updated_at')[1:2].first()

                previous_status = previous_status_obj.status if previous_status_obj else 'on_track'

                # Determine new status based on action
                if action == 'complete':
                    new_status = 'completed'
                elif action == 'undo':
                    new_status = previous_status
                elif action == 'hold':
                    new_status = 'on_hold'
                elif action == 'resume':
                    new_status = previous_status
                elif action == 'drop':
                    new_status = 'dropped'
                elif action == 'activate':
                    new_status = previous_status
                else:
                    return JsonResponse({'success': False, 'error': 'Invalid action'})

                # Update project status
                project.status = new_status
                project.save()

                # Create status history record
                ImprovementProjectStatus.objects.create(
                    project=project,
                    status=new_status,
                    completion_percentage=latest_status_obj.completion_percentage if latest_status_obj else 0,
                    revised_due_date=latest_status_obj.revised_due_date if latest_status_obj else None,
                    challenge='',
                    comments=f'Status changed to {new_status} via review meeting',
                    updated_by=request.user
                )
            else:
                return JsonResponse({'success': False, 'error': 'Invalid project type'})

            return JsonResponse({
                'success': True,
                'message': f'Project status updated to {new_status}',
                'new_status': new_status
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })