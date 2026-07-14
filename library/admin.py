from django.contrib import admin
from .models import Book, Loan, Reservation


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'category', 'total_copies', 'available_copies', 'school')
    list_filter = ('category', 'school')


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower', 'borrowed_at', 'due_date', 'returned_at', 'fine_amount', 'school')
    list_filter = ('returned_at', 'school')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower', 'reserved_at', 'fulfilled', 'school')
    list_filter = ('fulfilled', 'school')
