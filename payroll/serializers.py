from rest_framework import serializers

from .models import LeaveRequest, LeaveType, PayrollSettings, Payslip, StaffProfile


class StaffProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = StaffProfile
        fields = [
            'id', 'user', 'user_email', 'user_name', 'school', 'employee_id',
            'designation', 'department', 'hire_date', 'salary', 'bank_account',
            'bank_name', 'bank_branch', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'school', 'created_at', 'updated_at']

    def get_user_email(self, obj):
        return obj.user.email

    def get_user_name(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ['id', 'school', 'name', 'default_days_per_year', 'is_paid', 'created_at']
        read_only_fields = ['id', 'school', 'created_at']


class LeaveRequestSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    leave_type_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'staff', 'staff_name', 'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'days', 'reason', 'status',
            'approved_by', 'approved_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'staff', 'created_at', 'updated_at']

    def get_staff_name(self, obj):
        return f'{obj.staff.user.first_name} {obj.staff.user.last_name}'

    def get_leave_type_name(self, obj):
        return obj.leave_type.name

    def create(self, validated_data):
        user = self.context['request'].user
        try:
            staff = StaffProfile.objects.get(user=user)
        except StaffProfile.DoesNotExist:
            raise serializers.ValidationError('No staff profile for this user.')
        validated_data['staff'] = staff
        return super().create(validated_data)


class PayslipSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = Payslip
        fields = [
            'id', 'staff', 'staff_name', 'month', 'year', 'gross_salary',
            'basic_salary', 'allowances', 'deductions', 'net_salary',
            'is_paid', 'payment_date', 'generated_at',
        ]
        read_only_fields = ['id', 'generated_at']

    def get_staff_name(self, obj):
        return f'{obj.staff.user.first_name} {obj.staff.user.last_name}'


class PayrollSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollSettings
        fields = ['id', 'school', 'pay_period', 'payable_days', 'default_allowances', 'default_deductions', 'updated_at']
        read_only_fields = ['id', 'school', 'updated_at']
