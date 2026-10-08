from django.db import transaction, models
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.apps import apps

from accounts.models import User
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
    permission_classes = [permissions.IsAuthenticated]
    queryset = Announcement.objects.none()

    def get_queryset(self):
        return Announcement.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, school=self.request.user.school)


class DirectMessageViewSet(viewsets.ModelViewSet):
    serializer_class = DirectMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DirectMessage.objects.none()

    def get_queryset(self):
        user = self.request.user
        return DirectMessage.objects.filter(school=user.school).filter(
            Q(sender=user) | Q(recipient=user)
        )

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user, school=self.request.user.school)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notification.objects.none()

    def get_queryset(self):
        return Notification.objects.filter(
            school=self.request.user.school,
            recipient=self.request.user,
        )

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


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
        ).distinct().prefetch_related('participants', 'messages')
        page = self.paginate_queryset(conversations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(conversations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def start_chat(self, request):
        user = request.user
        parent_id = request.data.get('parent_id')
        if not parent_id:
            return Response(
                {'detail': 'parent_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            recipient = User.objects.get(id=parent_id, school=user.school, role='PARENT')
        except User.DoesNotExist:
            return Response(
                {'detail': 'Parent not found.'},
                status=status.HTTP_404_NOT_FOUND,
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

            parent = recipient.parent_links.first()
            learner_name = ''
            if parent and parent.learner_id:
                learner = User.objects.get(id=parent.learner_id)
                learner_name = learner.get_full_name() or learner.email
            conversation.name = f'{user.get_full_name() or user.email} ↔ {recipient.get_full_name() or "Parent"}'
            if learner_name:
                conversation.name += f' (re: {learner_name})'
            conversation.save()

        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def create_group(self, request):
        user = request.user
        name = request.data.get('name', '').strip()
        target = request.data.get('target')
        participant_ids = request.data.get('participant_ids', [])

        if not name:
            return Response(
                {'detail': 'name is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if target not in ('PARENTS', 'LEARNERS'):
            return Response(
                {'detail': 'target must be PARENTS or LEARNERS.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            conversation = Conversation.objects.create(
                name=name,
                conversation_type='GROUP',
                group_target=target,
                created_by=user,
                school=user.school,
            )
            ConversationParticipant.objects.create(conversation=conversation, user=user)

            user_ids = set()
            if participant_ids:
                user_ids.update(participant_ids)
            else:
                if target == 'PARENTS':
                    parents = User.objects.filter(role='PARENT', school=user.school)
                    user_ids.update(p.id for p in parents)
                elif target == 'LEARNERS':
                    students = User.objects.filter(role='STUDENT', school=user.school)
                    user_ids.update(s.id for s in students)

            for uid in user_ids:
                if uid != user.id:
                    ConversationParticipant.objects.get_or_create(
                        conversation=conversation,
                        user_id=uid
                    )

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
        added = []
        for uid in participant_ids:
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
        ])
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
        if user.role not in ('TEACHER', 'STAFF', 'ADMIN'):
            return Response(
                {'detail': 'Only teachers and staff can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response({
            'students': self._get_teacher_students(user),
            'parents': self._get_teacher_parents(user),
        })

    def _get_teacher_students(self, teacher):
        TeacherAssignment = apps.get_model('academics', 'TeacherAssignment')
        Enrollment = apps.get_model('academics', 'Enrollment')
        school = teacher.school
        streams = TeacherAssignment.objects.filter(
            teacher=teacher, school=school, is_active=True
        ).values_list('stream', flat=True).distinct()
        student_ids = Enrollment.objects.filter(
            stream__in=streams, school=school, is_active=True
        ).values_list('student_id', flat=True).distinct()
        students = User.objects.filter(id__in=student_ids, role='STUDENT', school=school)
        return UserMiniSerializer(students, many=True).data

    def _get_teacher_parents(self, teacher):
        ParentLearner = apps.get_model('accounts', 'ParentLearner')
        students_data = self._get_teacher_students(teacher)
        student_ids = [s['id'] for s in students_data]
        parent_link_ids = ParentLearner.objects.filter(
            learner_id__in=student_ids
        ).values_list('parent_id', flat=True).distinct()
        parents = User.objects.filter(id__in=parent_link_ids, role='PARENT', school=teacher.school)
        return UserMiniSerializer(parents, many=True).data


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
