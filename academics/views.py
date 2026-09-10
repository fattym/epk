from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from django.http import FileResponse, Http404
import json
import urllib.request
import urllib.error
from .models import (
    Grade, Pathway, Stream, LearningArea, TeacherAssignment, Timetable, Term,
    Strand, SubStrand, LearningOutcome, RubricDescriptor, ClassTeacher, Enrollment, Assignment,
    LearnerGroup, TimetableConfig, TimetableSlot
)
from .serializers import (
    GradeSerializer, PathwaySerializer, StreamSerializer, LearningAreaSerializer,
    StrandSerializer, SubStrandSerializer, LearningOutcomeSerializer, RubricDescriptorSerializer,
    TeacherAssignmentSerializer, ClassTeacherSerializer, EnrollmentSerializer,
    TimetableSerializer, AssignmentSerializer, TermSerializer, LearnerGroupSerializer,
    TimetableConfigSerializer, TimetableSlotSerializer
)


class SchoolScopedViewSetMixin:
    permission_classes = [permissions.IsAuthenticated]
    school_filter_field = 'school'

    def get_queryset(self):
        return self.queryset.model.objects.filter(**{self.school_filter_field: self.request.user.school})


class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated]


class PathwayViewSet(viewsets.ModelViewSet):
    queryset = Pathway.objects.all()
    serializer_class = PathwaySerializer
    permission_classes = [permissions.IsAuthenticated]


class StreamViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Stream.objects.all()
    serializer_class = StreamSerializer


class LearningAreaViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = LearningArea.objects.all()
    serializer_class = LearningAreaSerializer


class StrandViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Strand.objects.all()
    serializer_class = StrandSerializer
    school_filter_field = 'learning_area__school'


class SubStrandViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = SubStrand.objects.all()
    serializer_class = SubStrandSerializer
    school_filter_field = 'strand__learning_area__school'


class LearningOutcomeViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = LearningOutcome.objects.all()
    serializer_class = LearningOutcomeSerializer
    school_filter_field = 'sub_strand__strand__learning_area__school'


class RubricDescriptorViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = RubricDescriptor.objects.all()
    serializer_class = RubricDescriptorSerializer
    school_filter_field = 'outcome__sub_strand__strand__learning_area__school'


class TeacherAssignmentViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = TeacherAssignment.objects.all()
    serializer_class = TeacherAssignmentSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    @action(detail=False, methods=['get'])
    def my_teachers(self, request):
        user = request.user
        student_id = request.query_params.get('student_id')

        if user.role == 'PARENT':
            from accounts.models import ParentLearner
            if student_id:
                if not ParentLearner.objects.filter(parent=user, learner_id=student_id).exists():
                    return Response({'detail': 'Not authorized.'}, status=403)
                enrollments = Enrollment.objects.filter(student_id=student_id, is_active=True)
            else:
                learner_ids = ParentLearner.objects.filter(parent=user).values_list('learner_id', flat=True)
                enrollments = Enrollment.objects.filter(student_id__in=learner_ids, is_active=True)
        elif user.role == 'STUDENT':
            enrollments = Enrollment.objects.filter(student=user, is_active=True)
        else:
            return Response({'detail': 'Not applicable.'}, status=400)

        stream_ids = enrollments.values_list('stream_id', flat=True)
        assignments = self.get_queryset().filter(stream_id__in=stream_ids, is_active=True)
        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_students(self, request):
        user = request.user
        if user.role != 'TEACHER':
            return Response({'detail': 'Only teachers can access this.'}, status=403)
            
        assignments = self.get_queryset().filter(teacher=user, is_active=True)
        stream_ids = assignments.values_list('stream_id', flat=True)
        enrollments = Enrollment.objects.filter(stream_id__in=stream_ids, is_active=True)
        
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)


class ClassTeacherViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = ClassTeacher.objects.all()
    serializer_class = ClassTeacherSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class EnrollmentViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class TimetableViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_timetable(self, request):
        """
        Auto-generate a timetable for all streams in the school based on TimetableConfig.
        """
        try:
            school = request.user.school
            
            # Get or create TimetableConfig
            config, created = TimetableConfig.objects.get_or_create(
                school=school,
                defaults={
                    'school_start_time': '08:00:00',
                    'school_end_time': '15:30:00',
                    'lecture_duration_minutes': 45,
                    'working_days': ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'],
                    'breaks': [
                        {'name': 'Morning Break', 'start_time': '10:30:00', 'end_time': '10:45:00'},
                        {'name': 'Lunch Break', 'start_time': '12:30:00', 'end_time': '13:15:00'},
                    ],
                    'academic_year': '2024-2025',
                }
            )
            
            # Get all streams for this school
            streams = Stream.objects.filter(school=school)
            
            if not streams.exists():
                return Response({'message': 'No streams found for this school.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get all teacher assignments for this school
            teacher_assignments = TeacherAssignment.objects.filter(school=school, is_active=True)
            
            if not teacher_assignments.exists():
                return Response({'message': 'No teacher assignments found.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Build day slots from config
            working_days = config.working_days or ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']
            breaks = config.breaks or []
            school_start = config.school_start_time
            school_end = config.school_end_time
            lecture_duration = config.lecture_duration_minutes
            
            # Parse break times to minutes
            break_ranges = []
            for brk in breaks:
                brk_start = brk.get('start_time', '00:00')
                brk_end = brk.get('end_time', '00:00')
                bs_h, bs_m = map(int, brk_start.split(':')[:2])
                be_h, be_m = map(int, brk_end.split(':')[:2])
                break_ranges.append({
                    'name': brk.get('name', 'Break'),
                    'start_min': bs_h * 60 + bs_m,
                    'end_min': be_h * 60 + be_m,
                    'start_time': brk_start,
                    'end_time': brk_end,
                })
            
            # Build day slots
            day_slots = []
            for day in working_days:
                slots = []
                current_minutes = school_start.hour * 60 + school_start.minute
                end_minutes = school_end.hour * 60 + school_end.minute
                
                while current_minutes < end_minutes:
                    # Check if current time is within a break
                    active_break = None
                    for brk in break_ranges:
                        if brk['start_min'] <= current_minutes < brk['end_min']:
                            active_break = brk
                            break
                    
                    if active_break:
                        slots.append({
                            'type': 'break',
                            'break_name': active_break['name'],
                            'start_time': active_break['start_time'],
                            'end_time': active_break['end_time'],
                        })
                        current_minutes = active_break['end_min']
                        continue
                    
                    # Find next break start
                    next_break_start = None
                    for brk in break_ranges:
                        if brk['start_min'] > current_minutes:
                            if next_break_start is None or brk['start_min'] < next_break_start:
                                next_break_start = brk['start_min']
                    
                    if next_break_start is not None:
                        slot_end = min(next_break_start, end_minutes)
                    else:
                        slot_end = end_minutes
                    
                    # Only add lecture slots with reasonable duration
                    if slot_end - current_minutes >= lecture_duration // 2:
                        start_h = current_minutes // 60
                        start_m = current_minutes % 60
                        end_h = slot_end // 60
                        end_m = slot_end % 60
                        
                        slots.append({
                            'type': 'lecture',
                            'start_time': f"{start_h:02d}:{start_m:02d}",
                            'end_time': f"{end_h:02d}:{end_m:02d}",
                            'duration': slot_end - current_minutes,
                        })
                    
                    current_minutes = slot_end
                
                day_slots.append({
                    'day': day,
                    'slots': slots
                })
            
            # Build class needs based on teacher assignments
            # Group by stream and subject
            class_needs = {}
            for assignment in teacher_assignments:
                stream = assignment.stream
                learning_area = assignment.learning_area
                teacher = assignment.teacher
                
                if stream and learning_area and teacher:
                    stream_id = stream.id
                    if stream_id not in class_needs:
                        class_needs[stream_id] = []
                    
                    # Calculate weekly lectures needed (default 5 per week)
                    weekly_lectures = 5
                    
                    class_needs[stream_id].append({
                        'stream_id': stream_id,
                        'stream': stream,
                        'subject_id': learning_area.id,
                        'subject': learning_area,
                        'teacher_id': teacher.id,
                        'teacher': teacher,
                        'weekly_lectures': weekly_lectures,
                        'remaining': weekly_lectures,
                        'weightage': 100,
                    })
            
            # Sort needs by weightage
            for stream_id in class_needs:
                class_needs[stream_id].sort(key=lambda x: x['weightage'], reverse=True)
            
            # Track teacher busy slots
            num_slots = len(day_slots[0]['slots']) if day_slots and day_slots[0]['slots'] else 8
            teacher_busy = {}
            for stream_id in class_needs:
                for need in class_needs[stream_id]:
                    t_id = need['teacher_id']
                    if t_id not in teacher_busy:
                        teacher_busy[t_id] = {}
                        for day in working_days:
                            teacher_busy[t_id][day] = [False] * num_slots
            
            # Generate timetable slots
            generated_slots = []
            for stream_id, needs in class_needs.items():
                for day_idx, day_config in enumerate(day_slots):
                    day = day_config['day']
                    for slot_idx, slot_config in enumerate(day_config['slots']):
                        if slot_config['type'] == 'break':
                            continue
                        
                        # Try to allocate from needs
                        allocated = False
                        for need in needs:
                            if need['remaining'] <= 0:
                                continue
                            
                            teacher_id = need['teacher_id']
                            
                            # Check if teacher is free
                            if teacher_busy.get(teacher_id, {}).get(day, [False] * num_slots)[slot_idx]:
                                continue
                            
                            # Check daily burden (max 3 periods/day)
                            daily_load = sum(1 for b in teacher_busy.get(teacher_id, {}).get(day, []) if b)
                            if daily_load >= 3:
                                continue
                            
                            # Check consecutive burden (max 3 consecutive)
                            consecutive = 1
                            step = 1
                            while slot_idx - step >= 0 and teacher_busy.get(teacher_id, {}).get(day, [False] * num_slots)[slot_idx - step]:
                                consecutive += 1
                                step += 1
                            step = 1
                            while slot_idx + step < num_slots and teacher_busy.get(teacher_id, {}).get(day, [False] * num_slots)[slot_idx + step]:
                                consecutive += 1
                                step += 1
                            
                            if consecutive > 3:
                                continue
                            
                            # Allocate this slot
                            generated_slots.append({
                                'stream_id': stream_id,
                                'day': day,
                                'slot_idx': slot_idx,
                                'subject_id': need['subject_id'],
                                'teacher_id': teacher_id,
                                'start_time': slot_config['start_time'],
                                'end_time': slot_config['end_time'],
                                'is_break': False,
                            })
                            
                            # Mark teacher as busy
                            teacher_busy[teacher_id][day][slot_idx] = True
                            need['remaining'] -= 1
                            allocated = True
                            break
                        
                        # Backfill if no standard allocation
                        if not allocated:
                            # Find any available teacher for this stream
                            available = []
                            for need in needs:
                                teacher_id = need['teacher_id']
                                if not teacher_busy.get(teacher_id, {}).get(day, [False] * num_slots)[slot_idx]:
                                    if need['remaining'] > 0:
                                        available.append(need)
                            
                            if available:
                                # Sort by daily load (lowest first)
                                available.sort(key=lambda x: sum(1 for b in teacher_busy.get(x['teacher_id'], {}).get(day, []) if b))
                                best = available[0]
                                generated_slots.append({
                                    'stream_id': stream_id,
                                    'day': day,
                                    'slot_idx': slot_idx,
                                    'subject_id': best['subject_id'],
                                    'teacher_id': best['teacher_id'],
                                    'start_time': slot_config['start_time'],
                                    'end_time': slot_config['end_time'],
                                    'is_break': False,
                                })
                                teacher_busy[best['teacher_id']][day][slot_idx] = True
            
            # Add break slots
            for stream in streams:
                for day_idx, day_config in enumerate(day_slots):
                    day = day_config['day']
                    for slot_idx, slot_config in enumerate(day_config['slots']):
                        if slot_config['type'] == 'break':
                            generated_slots.append({
                                'stream_id': stream.id,
                                'day': day,
                                'slot_idx': slot_idx,
                                'subject_id': None,
                                'teacher_id': None,
                                'start_time': slot_config['start_time'],
                                'end_time': slot_config['end_time'],
                                'is_break': True,
                                'break_name': slot_config.get('break_name', 'Break'),
                            })
            
            # Save to database
            TimetableSlot.objects.filter(school=school).delete()
            
            created_count = 0
            for slot_data in generated_slots:
                TimetableSlot.objects.create(
                    school=school,
                    stream_id=slot_data['stream_id'],
                    day_of_week=slot_data['day'],
                    start_time=slot_data['start_time'],
                    end_time=slot_data['end_time'],
                    subject_id=slot_data['subject_id'],
                    teacher_id=slot_data['teacher_id'],
                    is_break=slot_data['is_break'],
                    break_name=slot_data.get('break_name', ''),
                    room='',
                )
                created_count += 1
            
            return Response({
                'message': 'Timetable generated successfully!',
                'slots_created': created_count,
                'streams_processed': streams.count(),
                'slots_per_day': len(day_slots[0]['slots']) if day_slots else 0
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'message': f'Error generating timetable: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TimetableConfigViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = TimetableConfig.objects.all()
    serializer_class = TimetableConfigSerializer
    
    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class TimetableSlotViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = TimetableSlot.objects.all()
    serializer_class = TimetableSlotSerializer
    
    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class AssignmentViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school, assigned_by=self.request.user)


class TermViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Term.objects.all()
    serializer_class = TermSerializer


class LearnerGroupViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = LearnerGroup.objects.all()
    serializer_class = LearnerGroupSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school, created_by=self.request.user)


class AITeacherAssistView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        task = request.data.get('task', 'general_help')
        context = request.data.get('context', {}) or {}

        user = request.user
        if user.role not in ['TEACHER', 'ADMIN']:
            return Response({'detail': 'Only teachers and admins can use AI assist.'}, status=status.HTTP_403_FORBIDDEN)

        suggestion = self.generate_suggestion(task, context, user)
        return Response({
            'task': task,
            'suggestion': suggestion,
            'note': 'This is an AI-generated draft suggestion. Review and apply it manually — it is not auto-committed.',
        })

    def generate_suggestion(self, task, context, user):
        if task == 'scheme_drafting':
            return self.scheme_drafting(context)
        if task == 'lesson_ideas':
            return self.lesson_ideas(context)
        if task == 'report_narrative':
            return self.report_narrative(context)
        if task == 'weekly_timetable':
            return self.weekly_timetable(context)
        return self.general_help(context)

    def call_external_ai(self, messages):
        api_url = getattr(settings, 'AI_ASSIST_API_URL', '')
        api_key = getattr(settings, 'AI_ASSIST_API_KEY', '')
        model = getattr(settings, 'AI_ASSIST_MODEL', 'claude-3-5-sonnet-20240620')
        if not api_url or not api_key:
            return None
        try:
            payload = json.dumps({'model': model, 'messages': messages}).encode('utf-8')
            req = urllib.request.Request(
                api_url,
                data=payload,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            return data.get('choices', [{}])[0].get('message', {}).get('content') or data.get('content', [{}])[0].get('text')
        except Exception:
            return None

    def scheme_drafting(self, context):
        sub_strand = context.get('sub_strand_name', 'this sub-strand')
        learning_area = context.get('learning_area_name', 'the learning area')
        grade = context.get('grade_name', 'the grade')
        outcomes = context.get('learning_outcomes', '')
        week = context.get('week_number', '')
        prompt = f"I am a Kenyan CBC teacher planning a lesson for {learning_area} - {grade}. The sub-strand is '{sub_strand}'. Learning outcomes: {outcomes}. Please draft: 1) A Key Inquiry Question that stimulates critical thinking. 2) 3-4 Learning Experiences/activities aligned to CBC pedagogy (discovery, collaborative, practical). 3) A list of Learning Resources available in a typical Kenyan school. 4) An Assessment Method suitable for competency-based assessment."
        answer = self.call_external_ai([{'role': 'user', 'content': prompt}])
        if answer:
            return answer
        return (
            f"Key Inquiry Question: How does {sub_strand} apply to everyday life in Kenya?\n\n"
            f"Learning Experiences:\n"
            f"1. Starter (5 mins): Quick class discussion on prior knowledge of {sub_strand}.\n"
            f"2. Discovery activity (15 mins): Guided inquiry into key concepts using local examples.\n"
            f"3. Collaborative task (15 mins): Learners work in pairs/groups to practise the skill or concept.\n"
            f"4. Recap & reflection (10 mins): Learners share findings; teacher summarises.\n\n"
            f"Learning Resources: Chart paper, markers, textbook, locally sourced materials, digital projector if available, worksheet.\n\n"
            f"Assessment Method: Observation checklist + learner self-assessment + short written response aligned to the rubric levels (BE/AE/ME/EE)."
        )

    def lesson_ideas(self, context):
        sub_strand = context.get('sub_strand_name', 'the topic')
        outcomes = context.get('learning_outcomes', '')
        prompt = f"Suggest 3 creative, hands-on CBC lesson activities for Kenyan lower-primary learners about '{sub_strand}'. Outcomes: {outcomes}. Keep materials simple and locally available."
        answer = self.call_external_ai([{'role': 'user', 'content': prompt}])
        if answer:
            return answer
        return (
            f"1. Storytelling & drama: Learners act out a short story related to {sub_strand} to build vocabulary and comprehension.\n"
            f"2. Hands-on sorting/classification: Use everyday objects (leaves, stones, or pictures) to sort by properties and explain reasoning.\n"
            f"3. Local community connection: A class walk or interview with a community helper to see {sub_strand} in real life, followed by a drawing/writing task."
        )

    def report_narrative(self, context):
        learner = context.get('learner_name', 'the learner')
        area = context.get('learning_area_name', 'this learning area')
        competencies = context.get('competency_summary', 'steady progress')
        prompt = f"Write a short, encouraging Kenyan CBC report-card narrative for {learner} in {area}. Summarise progress as: {competencies}. Tone: supportive, family-friendly."
        answer = self.call_external_ai([{'role': 'user', 'content': prompt}])
        if answer:
            return answer
        return (
            f"{learner} has shown {competencies} in {area} this term. The learner participates actively in class discussions and is growing in applying concepts independently. "
            "For the next term, focus on consolidating weaker areas through additional practice at home and consistent reading. Keep up the good work — well done!"
        )

    def weekly_timetable(self, context):
        assignments = context.get('assignments', [])
        constraints = context.get('constraints', 'standard school timetable with 8 periods/day, Mon-Fri')
        prompt = f"Draft a weekly timetable given these teacher assignments: {assignments}. Constraints: {constraints}. Avoid conflicts, spread subjects evenly, give Maths and English morning slots."
        answer = self.call_external_ai([{'role': 'user', 'content': prompt}])
        if answer:
            return answer
        return (
            "Suggested structure (Mon-Fri, 8 periods):\n"
            "Mon: Eng-Lang 1, Maths 2, Science/Integra 3, CRE/His 4, Games/PE 5, Creative Arts 6, Kiswahili 7, Class reading 8\n"
            "Tue: Maths 1, Eng-Lang 2, Social Studies 3, Science 4, Kiswahili 5, Music/Drama 6, Games 7, Remedial/Support 8\n"
            "Wed: Eng-Lang 1, Maths 2, Science 3, CRE/IEBC 4, Creative Arts 5, Physical Health 6, Kiswahili 7, Reading time 8\n"
            "Thu: Maths 1, Eng-Lang 2, Social Studies 3, Science/Integra 4, Games 5, Agriculture/Pre-tech 6, Kiswahili 7, Assessment 8\n"
            "Fri: Eng-Lang 1, Maths 2, CRE/His 3, Science/Integra 4, Music/Art 5, Games/Club 6, Class meeting/wrap-up 7, Clean-up/Reading 8"
        )

    def general_help(self, context):
        question = context.get('question', 'teaching strategies')
        prompt = f"As a Kenyan CBC teacher, answer this practical question: {question}. Keep answers concise, actionable, and aligned to CBC pedagogy."
        answer = self.call_external_ai([{'role': 'user', 'content': prompt}])
        if answer:
            return answer
        return (
            "Here are practical tips aligned to CBC:\n"
            "1. Start from what learners already know (prior knowledge).\n"
            "2. Use questioning to guide discovery rather than lecturing.\n"
            "3. Give learners voice and choice where possible.\n"
            "4. Assess during learning using observation and conversation, not only end-of-term tests.\n"
            "5. Connect tasks to Kenyan home and community contexts."
        )