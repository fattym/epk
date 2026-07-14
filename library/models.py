from django.db import models
from accounts.models import User
from tenants.models import School


class Book(models.Model):
    FICTION = 'FICTION'
    NON_FICTION = 'NON_FICTION'
    TEXTBOOK = 'TEXTBOOK'
    REFERENCE = 'REFERENCE'
    MAGAZINE = 'MAGAZINE'
    OTHER = 'OTHER'

    CATEGORY_CHOICES = (
        (FICTION, 'Fiction'),
        (NON_FICTION, 'Non-Fiction'),
        (TEXTBOOK, 'Textbook'),
        (REFERENCE, 'Reference'),
        (MAGAZINE, 'Magazine'),
        (OTHER, 'Other'),
    )

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='books')

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Loan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loans')
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    returned_at = models.DateTimeField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='loans')

    class Meta:
        ordering = ['-borrowed_at']

    def __str__(self):
        return f'{self.book.title} - {self.borrower.email}'


class Reservation(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    reserved_at = models.DateTimeField(auto_now_add=True)
    fulfilled = models.BooleanField(default=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='reservations')

    class Meta:
        ordering = ['-reserved_at']

    def __str__(self):
        return f'{self.book.title} - {self.borrower.email}'
