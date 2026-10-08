from django.db import models
from tenants.models import School
from accounts.models import User


class Route(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='routes')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'school']

    def __str__(self):
        return self.name


class BusStop(models.Model):
    route = models.ForeignKey(
        'Route', on_delete=models.CASCADE, related_name='stops'
    )
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name='bus_stops'
    )
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['route', 'order']

    def __str__(self):
        return f'{self.name} ({self.route.name})'


class Bus(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='buses')
    driver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'DRIVER'},
        related_name='buses',
    )
    route = models.ForeignKey(
        'Route', on_delete=models.SET_NULL, null=True, blank=True, related_name='buses'
    )
    plate_number = models.CharField(max_length=20)
    model = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    current_latitude = models.FloatField(null=True, blank=True)
    current_longitude = models.FloatField(null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['plate_number']
        unique_together = ['plate_number', 'school']

    def __str__(self):
        return f'{self.plate_number}'


class BusAssignment(models.Model):
    bus = models.ForeignKey('Bus', on_delete=models.CASCADE, related_name='assignments')
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'STUDENT'},
        related_name='bus_assignments',
    )
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name='bus_assignments'
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        unique_together = ['bus', 'student', 'start_date']

    def __str__(self):
        return f'{self.student} -> Bus {self.bus.plate_number}'
