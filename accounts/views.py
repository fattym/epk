from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User, ParentLearner
from .serializers import UserSerializer, UserCreateSerializer, ParentLearnerSerializer
from .permissions import IsAdminOrReadOnly


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(email=request.data['email'])
            response.data['user'] = UserSerializer(user).data
        return response


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
