from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.apps import apps
from .models import User, ParentLearner, StudentProfile
from .serializers import UserSerializer, UserCreateSerializer, ParentLearnerSerializer
from .permissions import IsAdminOrReadOnly


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(email=request.data['email'])
            response.data['user'] = UserSerializer(user).data
        return response


class StudentLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        student_id = request.data.get('student_id')
        pin_code = request.data.get('pin_code')
        
        if not student_id or not pin_code:
            return Response({'detail': 'student_id and pin_code are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            profile = StudentProfile.objects.get(admission_number=student_id)
            user = profile.user
            if user.check_password(pin_code) and user.role == 'STUDENT':
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                })
            else:
                return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        except StudentProfile.DoesNotExist:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filterset_fields = ['role', 'school']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return User.objects.filter(school=user.school)
        return User.objects.filter(id=user.id)

    def perform_create(self, serializer):
        if not serializer.validated_data.get('school'):
            serializer.save(school=self.request.user.school)
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def parents(self, request):
        parents = User.objects.filter(role='PARENT', school=request.user.school)
        serializer = self.get_serializer(parents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def students(self, request):
        students = User.objects.filter(role='STUDENT', school=request.user.school)
        serializer = self.get_serializer(students, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def teachers(self, request):
        teachers = User.objects.filter(role='TEACHER', school=request.user.school)
        serializer = self.get_serializer(teachers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        if request.user.role != 'ADMIN':
            return Response(
                {'detail': 'Only admins can bulk import students.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        rows = request.data.get('students') or []
        if not isinstance(rows, list) or not rows:
            return Response(
                {'detail': 'A non-empty "students" list is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Stream = apps.get_model('academics', 'Stream')
        Enrollment = apps.get_model('academics', 'Enrollment')
        school = request.user.school

        created = []
        errors = []
        for i, row in enumerate(rows):
            try:
                if not isinstance(row, dict):
                    raise ValueError('Each row must be an object.')
                email = (row.get('email') or '').strip().lower()
                if not email:
                    raise ValueError('email is required.')
                if User.objects.filter(email=email, school=school).exists():
                    raise ValueError('A student with this email already exists.')

                user = User(
                    email=email,
                    first_name=row.get('first_name', '') or '',
                    last_name=row.get('last_name', '') or '',
                    phone=row.get('phone', '') or '',
                    role='STUDENT',
                    school=school,
                )
                user.set_password(row.get('password') or 'Pass@1234')
                user.save()

                stream_name = (row.get('class') or row.get('stream') or '').strip()
                if stream_name:
                    stream = Stream.objects.filter(school=school, name__iexact=stream_name).first()
                    if stream:
                        Enrollment.objects.get_or_create(
                            student=user, stream=stream, school=school,
                            defaults={'is_active': True},
                        )
                created.append({'id': user.id, 'email': email})
            except Exception as e:
                errors.append({'row': i + 1, 'email': row.get('email') if isinstance(row, dict) else None, 'error': str(e)})

        return Response({
            'created': len(created),
            'created_rows': created,
            'errors': errors,
        })


class ParentLearnerViewSet(viewsets.ModelViewSet):
    queryset = ParentLearner.objects.all()
    serializer_class = ParentLearnerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return ParentLearner.objects.filter(school=user.school)
        return ParentLearner.objects.filter(parent=user)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)
