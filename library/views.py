from rest_framework import viewsets, permissions
from .models import Book, Loan, Reservation
from .serializers import BookSerializer, LoanSerializer, ReservationSerializer


class SchoolScopedViewSetMixin:
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.model.objects.filter(school=self.request.user.school)


class BookViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class LoanViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer


class ReservationViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
