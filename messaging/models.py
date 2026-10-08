from django.db import models
from tenants.models import School
from accounts.models import User


class Announcement(models.Model):
    TARGET_AUDIENCE_CHOICES = [
        ('ALL', 'All'),
        ('TEACHERS', 'Teachers'),
        ('STUDENTS', 'Students'),
        ('PARENTS', 'Parents'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    target_audience = models.CharField(
        max_length=20,
        choices=TARGET_AUDIENCE_CHOICES,
        default='ALL',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='announcements',
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    featured_products = models.ManyToManyField('shop.Product', blank=True, related_name='featured_in_announcements')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class DirectMessage(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
    )
    subject = models.CharField(max_length=255)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='direct_messages')

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return self.subject


class Conversation(models.Model):
    CONVERSATION_TYPE_CHOICES = [
        ('DIRECT', 'Direct Message'),
        ('GROUP', 'Group Message'),
    ]
    GROUP_TARGET_CHOICES = [
        ('PARENTS', 'Parents'),
        ('LEARNERS', 'Learners'),
    ]

    name = models.CharField(max_length=255, blank=True, null=True)
    conversation_type = models.CharField(
        max_length=10,
        choices=CONVERSATION_TYPE_CHOICES,
        default='DIRECT',
    )
    group_target = models.CharField(
        max_length=10,
        choices=GROUP_TARGET_CHOICES,
        blank=True,
        null=True,
        help_text='Only set for group conversations. Determines if the group targets parents or learners.',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_conversations',
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name or f'Conversation {self.id}'

    @property
    def display_name(self):
        if self.is_group:
            return self.name or 'Group Chat'
        return self.name or 'Direct Message'

    @property
    def is_group(self):
        return self.conversation_type == 'GROUP'


class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(
        'Conversation',
        on_delete=models.CASCADE,
        related_name='participants',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversation_participations',
    )
    unread_count = models.PositiveIntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['conversation', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f'{self.user.email} in conversation {self.conversation.id}'


class ConversationMessage(models.Model):
    conversation = models.ForeignKey(
        'Conversation',
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversation_messages',
    )
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(
        User,
        through='ConversationMessageRead',
        related_name='read_messages',
        blank=True,
    )

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f'Message in conversation {self.conversation.id} by {self.sender.email}'


class ConversationMessageRead(models.Model):
    message = models.ForeignKey(ConversationMessage, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user']


class Notification(models.Model):
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='notifications')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
