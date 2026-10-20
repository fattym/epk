from django.db import transaction, models
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.apps import apps

from accounts.models import User
from accounts.permissions import IsAdminOrStaffOrTeacher
from .models import (
    Announcement, DirectMessage, Notification,
    Conversation, ConversationParticipant, ConversationMessage, ConversationMessageRead,
)
from .serializers import (
    AnnouncementSerializer, DirectMessageSerializer, NotificationSerializer,
    ConversationSerializer, ConversationMessageSerializer, ConversationParticipantSerializer, UserMiniSerializer,
)


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAdminOrStaffOrTeacher]
    queryset = Announcement.objects.none()

    def get_queryset(self):
        return Announcement.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, school=self.request.user.school)


class DirectMessageViewSet(viewsets.ModelViewSet):
    serializer_class = DirectMessageSerializer
    permission_classes = [IsAdminOrStaffOrTeacher]
    queryset = DirectMessage.objects.none()

    def get_queryset(self):
        user = self.request.user
        return DirectMessage.objects.filter(school=user.school).filter(
            Q(sender=user) | Q(recipient=user)
        )

    def perform_create(self, serializer):
        recipient = serializer.validated_data.get('recipient')
        user = self.request.user
        
        if user.role == 'STUDENT':
            raise PermissionDenied('Students cannot initiate direct messages.')
        if user.role == 'PARENT':
            from accounts.models import ParentLearner
            if not ParentLearner.objects.filter(parent=user, learner=recipient).exists():
                raise PermissionDenied('Parents can only message their own children.')
        
        serializer.save(sender=user, school=user.school)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminOrStaffOrTeacher]
    queryset = Notification.objects.none()

    def get_queryset(self):
        return Notification.objects.filter(
            school=self.request.user.school,
            recipient=self.request.user,
        )

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


def get_teacher_grade_ids(teacher):
    """Returns list of Grade IDs taught by the given teacher."""
    if not teacher or not teacher.school:
        return []
    school = teacher.school
    TeacherAssignment = apps.get_model('academics', 'TeacherAssignment')
    ClassTeacher = apps.get_model('academics', 'ClassTeacher')
    Stream = apps.get_model('academics', 'Stream')

    stream_ids = set(
        TeacherAssignment.objects.filter(
            teacher=teacher, school=school, is_active=True
        ).values_list('stream_id', flat=True)
    )
    stream_ids.update(
        ClassTeacher.objects.filter(
            teacher=teacher, school=school
        ).values_list('stream_id', flat=True)
    )
    return list(
        Stream.objects.filter(
            id__in=stream_ids, school=school
        ).values_list('grade_id', flat=True).distinct()
    )


def get_parents_with_learners(school, allowed_grade_ids=None):
    """
    Returns list of dicts for parents with their linked learners.
    If allowed_grade_ids is given (for a teacher), only includes parents who have
    at least one learner enrolled in those grades, and only includes those learners.
    """
    if not school:
        return []

    ParentLearner = apps.get_model('accounts', 'ParentLearner')
    Enrollment = apps.get_model('academics', 'Enrollment')
    User = apps.get_model('accounts', 'User')

    enrollment_qs = Enrollment.objects.filter(
        school=school, is_active=True
    ).select_related('student', 'stream', 'stream__grade')

    if allowed_grade_ids is not None:
        enrollment_qs = enrollment_qs.filter(stream__grade_id__in=allowed_grade_ids)

    student_enrollments = {}
    for enr in enrollment_qs:
        student_enrollments.setdefault(enr.student_id, []).append({
            'student_id': enr.student_id,
            'student_name': enr.student.get_full_name() or enr.student.email,
            'grade_id': enr.stream.grade_id,
            'grade_name': enr.stream.grade.name if enr.stream.grade else '',
            'stream_id': enr.stream_id,
            'stream_name': enr.stream.name,
        })

    link_qs = ParentLearner.objects.filter(
        school=school,
        learner_id__in=student_enrollments.keys()
    ).select_related('parent', 'learner')

    parent_map = {}
    seen_learner_links = set()

    for link in link_qs:
        parent = link.parent
        if parent.id not in parent_map:
            parent_map[parent.id] = {
                'id': parent.id,
                'first_name': parent.first_name,
                'last_name': parent.last_name,
                'email': parent.email,
                'phone': parent.phone,
                'learners': [],
                'grade_ids': set(),
                'grade_names': set(),
            }

        link_key = (parent.id, link.learner_id)
        if link_key not in seen_learner_links:
            seen_learner_links.add(link_key)
            learner_info = student_enrollments.get(link.learner_id, [])
            for info in learner_info:
                parent_map[parent.id]['learners'].append({
                    'id': link.learner_id,
                    'name': info['student_name'],
                    'grade_id': info['grade_id'],
                    'grade_name': info['grade_name'],
                    'stream_name': info['stream_name'],
                    'relationship': link.relationship,
                })
                parent_map[parent.id]['grade_ids'].add(info['grade_id'])
                parent_map[parent.id]['grade_names'].add(info['grade_name'])

    if allowed_grade_ids is None:
        all_parents = User.objects.filter(role='PARENT', school=school)
        for p in all_parents:
            if p.id not in parent_map:
                parent_map[p.id] = {
                    'id': p.id,
                    'first_name': p.first_name,
                    'last_name': p.last_name,
                    'email': p.email,
                    'phone': p.phone,
                    'learners': [],
                    'grade_ids': set(),
                    'grade_names': set(),
                }

    result = []
    for p_id in sorted(parent_map.keys(), key=lambda x: (parent_map[x]['first_name'] or parent_map[x]['email'])):
        item = parent_map[p_id]
        item['grade_ids'] = sorted(list(item['grade_ids']))
        item['grade_names'] = sorted(list(item['grade_names']))
        result.append(item)

    return result


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Conversation.objects.none()

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(
            school=user.school,
            participants__user=user,
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, school=self.request.user.school)

    @action(detail=False, methods=['get'])
    def my_conversations(self, request):
        user = request.user
        conversations = Conversation.objects.filter(
            school=user.school,
            participants__user=user,
        ).distinct().annotate(
            latest_msg_time=models.Max('messages__sent_at')
        ).order_by(
            models.F('latest_msg_time').desc(nulls_last=True),
            '-created_at'
        ).prefetch_related('participants', 'messages')

        page = self.paginate_queryset(conversations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(conversations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def start_chat(self, request):
        user = request.user
        recipient_id = request.data.get('parent_id') or request.data.get('recipient_id')
        if not recipient_id:
            return Response(
                {'detail': 'parent_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            recipient = User.objects.get(id=recipient_id, school=user.school)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Recipient not found in your school.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        ParentLearner = apps.get_model('accounts', 'ParentLearner')

        # Role-based messaging rules:
        if user.role == 'TEACHER':
            if recipient.role != 'PARENT':
                return Response(
                    {'detail': 'Teachers can only message parents.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            assigned_grade_ids = get_teacher_grade_ids(user)
            if not assigned_grade_ids:
                return Response(
                    {'detail': 'You are not currently assigned to any grades or streams.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            allowed = ParentLearner.objects.filter(
                parent=recipient,
                school=user.school,
                learner__enrollments__stream__grade_id__in=assigned_grade_ids,
                learner__enrollments__is_active=True,
                learner__enrollments__school=user.school,
            ).exists()
            if not allowed:
                return Response(
                    {'detail': 'Teachers can only message parents of pupils in their assigned grades.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif user.role in ('ADMIN', 'STAFF'):
            # School admin/staff can communicate to all parents in the school
            pass
        elif user.role == 'PARENT':
            if recipient.role not in ('TEACHER', 'ADMIN', 'STAFF'):
                return Response(
                    {'detail': 'Parents can only message teachers or school administrators.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            return Response(
                {'detail': 'Your role is not authorized to start direct chats.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        existing = Conversation.objects.filter(
            school=user.school,
            conversation_type='DIRECT',
            participants__user=user,
        ).filter(participants__user=recipient)
        if existing.exists():
            conv = existing.first()
            serializer = self.get_serializer(conv)
            return Response(serializer.data)

        with transaction.atomic():
            conversation = Conversation.objects.create(
                conversation_type='DIRECT',
                created_by=user,
                school=user.school,
            )
            ConversationParticipant.objects.create(conversation=conversation, user=user)
            ConversationParticipant.objects.create(conversation=conversation, user=recipient)

            learner_name = ''
            if recipient.role == 'PARENT':
                parent_link = recipient.learner_links.filter(school=user.school).select_related('learner').first()
                if parent_link and parent_link.learner:
                    learner_name = parent_link.learner.get_full_name() or parent_link.learner.email
            elif user.role == 'PARENT':
                parent_link = user.learner_links.filter(school=user.school).select_related('learner').first()
                if parent_link and parent_link.learner:
                    learner_name = parent_link.learner.get_full_name() or parent_link.learner.email

            conversation.name = f'{user.get_full_name() or user.email} ↔ {recipient.get_full_name() or recipient.email}'
            if learner_name:
                conversation.name += f' (re: {learner_name})'
            conversation.save()

        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def create_group(self, request):
        user = request.user
        name = request.data.get('name', '').strip()
        target = request.data.get('target', 'PARENTS')
        grade_id = request.data.get('grade_id')
        participant_ids = request.data.get('participant_ids', [])

        if not name:
            return Response(
                {'detail': 'Group name is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.role not in ('TEACHER', 'STAFF', 'ADMIN'):
            return Response(
                {'detail': 'Only teachers and school administrators can create group messages.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        Enrollment = apps.get_model('academics', 'Enrollment')
        ParentLearner = apps.get_model('accounts', 'ParentLearner')
        target_parent_ids = set()

        if user.role == 'TEACHER':
            assigned_grade_ids = get_teacher_grade_ids(user)
            if not assigned_grade_ids:
                return Response(
                    {'detail': 'You are not currently assigned to any grades or streams.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if grade_id:
                try:
                    grade_id = int(grade_id)
                except (ValueError, TypeError):
                    return Response({'detail': 'Invalid grade_id.'}, status=status.HTTP_400_BAD_REQUEST)
                if grade_id not in assigned_grade_ids:
                    return Response(
                        {'detail': 'Teachers can only create group messages for their assigned pupils\' grades.'},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                pupil_ids = Enrollment.objects.filter(
                    stream__grade_id=grade_id,
                    school=user.school,
                    is_active=True,
                ).values_list('student_id', flat=True)
                grade_parent_ids = set(ParentLearner.objects.filter(
                    learner_id__in=pupil_ids,
                    school=user.school,
                ).values_list('parent_id', flat=True))

                if participant_ids:
                    selected_ids = set(int(p) for p in participant_ids)
                    target_parent_ids = grade_parent_ids.intersection(selected_ids)
                else:
                    target_parent_ids = grade_parent_ids
            else:
                pupil_ids = Enrollment.objects.filter(
                    stream__grade_id__in=assigned_grade_ids,
                    school=user.school,
                    is_active=True,
                ).values_list('student_id', flat=True)
                allowed_parent_ids = set(ParentLearner.objects.filter(
                    learner_id__in=pupil_ids,
                    school=user.school,
                ).values_list('parent_id', flat=True))

                if participant_ids:
                    selected_ids = set(int(p) for p in participant_ids)
                    disallowed = selected_ids - allowed_parent_ids
                    if disallowed:
                        return Response(
                            {'detail': 'One or more selected parents are not in your assigned pupils\' grades.'},
                            status=status.HTTP_403_FORBIDDEN,
                        )
                    target_parent_ids = selected_ids
                else:
                    target_parent_ids = allowed_parent_ids

        elif user.role in ('ADMIN', 'STAFF'):
            if grade_id:
                try:
                    grade_id = int(grade_id)
                except (ValueError, TypeError):
                    return Response({'detail': 'Invalid grade_id.'}, status=status.HTTP_400_BAD_REQUEST)
                pupil_ids = Enrollment.objects.filter(
                    stream__grade_id=grade_id,
                    school=user.school,
                    is_active=True,
                ).values_list('student_id', flat=True)
                grade_parent_ids = set(ParentLearner.objects.filter(
                    learner_id__in=pupil_ids,
                    school=user.school,
                ).values_list('parent_id', flat=True))

                if participant_ids:
                    target_parent_ids = grade_parent_ids.intersection(set(int(p) for p in participant_ids))
                else:
                    target_parent_ids = grade_parent_ids
            elif participant_ids:
                target_parent_ids = set(User.objects.filter(
                    id__in=[int(p) for p in participant_ids],
                    role='PARENT',
                    school=user.school,
                ).values_list('id', flat=True))
            else:
                target_parent_ids = set(User.objects.filter(
                    role='PARENT',
                    school=user.school,
                ).values_list('id', flat=True))

        if not target_parent_ids:
            return Response(
                {'detail': 'No eligible parents found for this group.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            conversation = Conversation.objects.create(
                name=name,
                conversation_type='GROUP',
                group_target='PARENTS',
                created_by=user,
                school=user.school,
            )
            ConversationParticipant.objects.create(conversation=conversation, user=user)

            participants_to_create = [
                ConversationParticipant(conversation=conversation, user_id=pid)
                for pid in target_parent_ids
                if pid != user.id
            ]
            ConversationParticipant.objects.bulk_create(participants_to_create, ignore_conflicts=True)

        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def add_participants(self, request, pk=None):
        conversation = self.get_object()
        user = request.user
        if conversation.created_by != user:
            return Response(
                {'detail': 'Only the conversation creator can add participants.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        participant_ids = request.data.get('participant_ids', [])
        if not participant_ids:
            return Response({'detail': 'participant_ids is required.'}, status=status.HTTP_400_BAD_REQUEST)

        ParentLearner = apps.get_model('accounts', 'ParentLearner')
        Enrollment = apps.get_model('academics', 'Enrollment')
        selected_ids = set(int(p) for p in participant_ids)

        if user.role == 'TEACHER':
            assigned_grade_ids = get_teacher_grade_ids(user)
            pupil_ids = Enrollment.objects.filter(
                stream__grade_id__in=assigned_grade_ids,
                school=user.school,
                is_active=True,
            ).values_list('student_id', flat=True)
            allowed_parent_ids = set(ParentLearner.objects.filter(
                learner_id__in=pupil_ids,
                school=user.school,
            ).values_list('parent_id', flat=True))
            disallowed = selected_ids - allowed_parent_ids
            if disallowed:
                return Response(
                    {'detail': 'One or more selected parents are not in your assigned pupils\' grades.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        added = []
        for uid in selected_ids:
            obj, created = ConversationParticipant.objects.get_or_create(
                conversation=conversation,
                user_id=uid
            )
            if created:
                added.append(uid)
        return Response({'added': added})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        conversation = self.get_object()
        user = request.user
        messages = conversation.messages.exclude(read_by=user)
        ConversationMessageRead.objects.bulk_create([
            ConversationMessageRead(message=msg, user=user)
            for msg in messages
        ], ignore_conflicts=True)
        participant, _ = ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=user
        )
        participant.unread_count = 0
        participant.save()
        return Response({'status': 'marked as read'})

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        user = request.user
        if not conversation.participants.filter(user=user).exists():
            return Response(
                {'detail': 'You are not a participant in this conversation.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        msgs = conversation.messages.all()
        page = self.paginate_queryset(msgs)
        if page is not None:
            serializer = ConversationMessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = ConversationMessageSerializer(msgs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        conversation = self.get_object()
        user = request.user
        if not conversation.participants.filter(user=user).exists():
            return Response(
                {'detail': 'You are not a participant in this conversation.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        participants = conversation.participants.all()
        serializer = ConversationParticipantSerializer(participants, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        conversation = self.get_object()
        user = request.user
        conversation.participants.filter(user=user).delete()
        return Response({'status': 'left conversation'})

    @action(detail=False, methods=['get'])
    def teacher_contacts(self, request):
        user = request.user
        school = user.school
        Grade = apps.get_model('academics', 'Grade')
        Enrollment = apps.get_model('academics', 'Enrollment')
        ParentLearner = apps.get_model('accounts', 'ParentLearner')

        if user.role == 'TEACHER':
            assigned_grade_ids = get_teacher_grade_ids(user)
            grades_qs = Grade.objects.filter(id__in=assigned_grade_ids).order_by('order')
            parents = get_parents_with_learners(school, allowed_grade_ids=assigned_grade_ids)

            # Pupils in assigned grades
            pupil_ids = Enrollment.objects.filter(
                stream__grade_id__in=assigned_grade_ids,
                school=school,
                is_active=True,
            ).values_list('student_id', flat=True)
            students = UserMiniSerializer(
                User.objects.filter(id__in=pupil_ids, role='STUDENT', school=school),
                many=True
            ).data

            grades_data = []
            for g in grades_qs:
                p_count = sum(1 for p in parents if g.id in p.get('grade_ids', []))
                grades_data.append({
                    'id': g.id,
                    'name': g.name,
                    'stage': g.stage,
                    'parent_count': p_count,
                })

            return Response({
                'role': 'TEACHER',
                'can_broadcast_all': False,
                'scope_label': f"Pupils' Grade Scope: {', '.join(g.name for g in grades_qs) if grades_qs.exists() else 'No grades assigned'}",
                'grades': grades_data,
                'parents': parents,
                'students': students,
            })

        elif user.role in ('ADMIN', 'STAFF'):
            grades_qs = Grade.objects.filter(streams__school=school).distinct().order_by('order')
            if not grades_qs.exists():
                grades_qs = Grade.objects.all().order_by('order')

            parents = get_parents_with_learners(school, allowed_grade_ids=None)
            students = UserMiniSerializer(
                User.objects.filter(role='STUDENT', school=school),
                many=True
            ).data

            grades_data = []
            for g in grades_qs:
                p_count = sum(1 for p in parents if g.id in p.get('grade_ids', []))
                grades_data.append({
                    'id': g.id,
                    'name': g.name,
                    'stage': g.stage,
                    'parent_count': p_count,
                })

            return Response({
                'role': user.role,
                'can_broadcast_all': True,
                'scope_label': 'Scope: Entire School (All Grades)',
                'grades': grades_data,
                'parents': parents,
                'students': students,
            })

        elif user.role == 'PARENT':
            # Parent can communicate with teachers of their children or school staff
            learner_ids = user.learner_links.filter(school=school).values_list('learner_id', flat=True)
            streams = Enrollment.objects.filter(student_id__in=learner_ids, school=school, is_active=True).values_list('stream_id', flat=True)
            TeacherAssignment = apps.get_model('academics', 'TeacherAssignment')
            ClassTeacher = apps.get_model('academics', 'ClassTeacher')
            teacher_ids = set(TeacherAssignment.objects.filter(stream_id__in=streams, is_active=True, school=school).values_list('teacher_id', flat=True))
            teacher_ids.update(ClassTeacher.objects.filter(stream_id__in=streams, school=school).values_list('teacher_id', flat=True))

            teachers = UserMiniSerializer(User.objects.filter(id__in=teacher_ids, school=school), many=True).data
            school_staff = UserMiniSerializer(User.objects.filter(role__in=('ADMIN', 'STAFF'), school=school), many=True).data

            return Response({
                'role': 'PARENT',
                'can_broadcast_all': False,
                'scope_label': 'My Children\'s Teachers and School Administration',
                'grades': [],
                'parents': [],
                'students': [],
                'teachers': teachers,
                'school_staff': school_staff,
            })

        return Response(
            {'detail': 'Only teachers, parents, and school staff can access messaging contacts.'},
            status=status.HTTP_403_FORBIDDEN,
        )


class ConversationMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ConversationMessage.objects.none()

    def get_queryset(self):
        user = self.request.user
        return ConversationMessage.objects.filter(
            conversation__school=user.school,
            conversation__participants__user=user,
        ).distinct()

    def perform_create(self, serializer):
        user = self.request.user
        conversation = serializer.validated_data['conversation']
        if not conversation.participants.filter(user=user).exists():
            raise PermissionDenied({'detail': 'You are not a participant in this conversation.'})
        message = serializer.save(sender=user)
        other_participants = conversation.participants.exclude(user=user)
        conversation.participants.filter(user__in=other_participants.values('user')).update(
            unread_count=models.F('unread_count') + 1
        )
