from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from django.http import FileResponse, Http404
from academics.models import SubStrand, LearningOutcome, Strand
from .models import ReferenceDocument, SchemeOfWork, SchemeWeek
from .serializers import ReferenceDocumentSerializer, SchemeOfWorkSerializer, SchemeGenerateSerializer, SchemeUploadSerializer
import csv
import os
import re


STANDARD_FIELDS = [
    'week_number',
    'strand_name',
    'sub_strand_name',
    'specific_learning_outcomes',
    'key_inquiry_question',
    'learning_experiences',
    'learning_resources',
    'assessment_method',
]

COLUMN_ALIASES = {
    'week_number': ['week', 'week no', 'week number', 'wk', 'no', 'week_no', 'weeknumber'],
    'strand_name': ['strand', 'topic', 'main topic', 'broad topic', 'strand/topic', 'strand_name'],
    'sub_strand_name': ['sub-strand', 'substrand', 'sub topic', 'lesson topic', 'sub_strand', 'sub strand', 'sub-topic'],
    'specific_learning_outcomes': ['outcomes', 'learning outcomes', 'specific outcomes', 'objectives', 'learning outcome', 'specific_learning_outcomes'],
    'key_inquiry_question': ['inquiry question', 'key question', 'question', 'key inquiry', 'key_inquiry_question'],
    'learning_experiences': ['experiences', 'activities', 'learning activities', 'learning experiences', 'lesson activities'],
    'learning_resources': ['resources', 'materials', 'teaching aids', 'learning resources', 'required resources'],
    'assessment_method': ['assessment', 'assessment method', 'evaluation', 'assessment_method', 'method'],
}


def normalize_header(header):
    if header is None:
        return ''
    return re.sub(r'[^a-z0-9]', '', str(header).lower())


def detect_column(header):
    normalized = normalize_header(header)
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if normalize_header(alias) == normalized:
                return field, 1.0
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized or normalized in alias:
                return field, 0.7
    return None, 0.0


def parse_scheme_file(uploaded_file):
    file_name = uploaded_file.name.lower()
    rows = []
    headers = []

    if file_name.endswith('.csv'):
        decoded_file = uploaded_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)
        rows = list(reader)
    elif file_name.endswith('.xlsx') or file_name.endswith('.xls'):
        uploaded_file.seek(0)
        import openpyxl
        wb = openpyxl.load_workbook(uploaded_file)
        ws = wb.active
        rows = []
        for row in ws.iter_rows(values_only=True):
            rows.append(list(row))
    else:
        return None, None, {'detail': 'Unsupported file type. Upload CSV or Excel.'}

    if not rows:
        return None, None, {'detail': 'File is empty.'}

    headers = [str(h) if h is not None else '' for h in rows[0]]
    data_rows = rows[1:] if len(rows) > 1 else []

    column_mapping = {}
    unmapped_headers = []
    for idx, header in enumerate(headers):
        field, confidence = detect_column(header)
        if field:
            column_mapping[field] = {'index': idx, 'header': header, 'confidence': confidence}
        else:
            unmapped_headers.append({'index': idx, 'header': header})

    preview = []
    for row in data_rows[:20]:
        mapped_row = {}
        for field, mapping in column_mapping.items():
            value = row[mapping['index']] if mapping['index'] < len(row) else ''
            mapped_row[field] = str(value) if value is not None else ''
        preview.append(mapped_row)

    return headers, column_mapping, {'preview': preview, 'unmapped_headers': unmapped_headers, 'total_rows': len(data_rows)}


class ReferenceDocumentViewSet(viewsets.ModelViewSet):
    queryset = ReferenceDocument.objects.all()
    serializer_class = ReferenceDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return ReferenceDocument.objects.filter(school=user.school)
        return ReferenceDocument.objects.filter(school=user.school)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user, school=self.request.user.school)


class SchemeOfWorkViewSet(viewsets.ModelViewSet):
    queryset = SchemeOfWork.objects.all()
    serializer_class = SchemeOfWorkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return SchemeOfWork.objects.filter(school=user.school)

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user, school=self.request.user.school)

    @action(detail=False, methods=['get'])
    def download_template(self, request):
        template_path = os.path.join(os.path.dirname(__file__), '..', 'media', 'scheme_template.csv')
        if not os.path.exists(template_path):
            from django.conf import settings
            template_path = os.path.join(settings.BASE_DIR, 'media', 'scheme_template.csv')
        if not os.path.exists(template_path):
            raise Http404('Template not found')
        response = FileResponse(open(template_path, 'rb'), as_attachment=True, filename='scheme_of_work_template.csv')
        return response

    @action(detail=False, methods=['post'])
    def parse(self, request):
        if 'file' not in request.FILES:
            return Response({'detail': 'file is required.'}, status=status.HTTP_400_BAD_REQUEST)
        uploaded_file = request.FILES['file']
        headers, column_mapping, result = parse_scheme_file(uploaded_file)
        if headers is None:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'headers': headers,
            'column_mapping': column_mapping,
            'preview': result['preview'],
            'unmapped_headers': result['unmapped_headers'],
            'total_rows': result['total_rows'],
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        if 'file' not in request.FILES:
            return Response({'detail': 'file is required.'}, status=status.HTTP_400_BAD_REQUEST)
        uploaded_file = request.FILES['file']
        learning_area_id = request.data.get('learning_area')
        term_id = request.data.get('term')
        stream_id = request.data.get('stream')

        if not learning_area_id or not term_id or not stream_id:
            return Response({'detail': 'learning_area, term, and stream are required.'}, status=status.HTTP_400_BAD_REQUEST)

        from academics.models import LearningArea, Term, Stream, Strand, SubStrand
        try:
            learning_area = LearningArea.objects.get(id=learning_area_id)
            term = Term.objects.get(id=term_id)
            stream = Stream.objects.get(id=stream_id)
        except (LearningArea.DoesNotExist, Term.DoesNotExist, Stream.DoesNotExist):
            return Response({'detail': 'Invalid learning area, term, or stream'}, status=status.HTTP_400_BAD_REQUEST)

        scheme, created = SchemeOfWork.objects.get_or_create(
            teacher=request.user,
            learning_area=learning_area,
            term=term,
            stream=stream,
            school=request.user.school,
            defaults={'status': 'draft', 'file': uploaded_file},
        )
        if not created:
            scheme.file = uploaded_file
            scheme.status = 'draft'
            scheme.save()
            SchemeWeek.objects.filter(scheme=scheme).delete()

        headers, column_mapping, result = parse_scheme_file(uploaded_file)
        if headers is None:
            scheme.delete()
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        week_num = 1
        created_count = 0
        for row in result['preview']:
            strand_name = row.get('strand_name', '').strip()
            sub_strand_name = row.get('sub_strand_name', '').strip()
            if not strand_name or not sub_strand_name:
                continue
            strand, _ = Strand.objects.get_or_create(learning_area=learning_area, name=strand_name, defaults={'learning_area': learning_area})
            sub_strand, _ = SubStrand.objects.get_or_create(strand=strand, name=sub_strand_name, defaults={'strand': strand})
            SchemeWeek.objects.create(
                scheme=scheme,
                week_number=week_num,
                strand=strand,
                sub_strand=sub_strand,
                specific_learning_outcomes=row.get('specific_learning_outcomes', ''),
                key_inquiry_question=row.get('key_inquiry_question', ''),
                learning_experiences=row.get('learning_experiences', ''),
                learning_resources=row.get('learning_resources', ''),
                assessment_method=row.get('assessment_method', ''),
            )
            week_num += 1
            created_count += 1

        result_serializer = SchemeOfWorkSerializer(scheme)
        return Response({'scheme': result_serializer.data, 'created_weeks': created_count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        serializer = SchemeGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        learning_area_id = serializer.validated_data['learning_area']
        term_id = serializer.validated_data['term']
        stream_id = serializer.validated_data['stream']

        from academics.models import LearningArea, Term, Stream
        try:
            learning_area = LearningArea.objects.get(id=learning_area_id)
            term = Term.objects.get(id=term_id)
            stream = Stream.objects.get(id=stream_id)
        except (LearningArea.DoesNotExist, Term.DoesNotExist, Stream.DoesNotExist):
            return Response({'detail': 'Invalid learning area, term, or stream'}, status=status.HTTP_400_BAD_REQUEST)

        scheme, created = SchemeOfWork.objects.get_or_create(
            teacher=request.user,
            learning_area=learning_area,
            term=term,
            stream=stream,
            school=request.user.school,
            defaults={'status': 'draft'},
        )

        if created:
            strands = Strand.objects.filter(learning_area=learning_area).prefetch_related('sub_strands')
            week_num = 1
            scheme_weeks = []
            for strand in strands:
                for sub_strand in strand.sub_strands.all():
                    outcomes = LearningOutcome.objects.filter(sub_strand=sub_strand)
                    outcome_text = '; '.join([o.description for o in outcomes[:3]])
                    if not outcome_text:
                        outcome_text = sub_strand.name
                    scheme_weeks.append(SchemeWeek(
                        scheme=scheme,
                        week_number=week_num,
                        strand=strand,
                        sub_strand=sub_strand,
                        specific_learning_outcomes=outcome_text,
                    ))
                    week_num += 1

            SchemeWeek.objects.bulk_create(scheme_weeks)

            matching_course = Course.objects.filter(
                school=request.user.school,
                learning_area=learning_area,
                stream=stream,
                term=term,
                teacher=request.user,
            ).first()

            if matching_course:
                SchemeWeek.objects.filter(scheme=scheme, course__isnull=True).update(course=matching_course)
                for sw in SchemeWeek.objects.filter(scheme=scheme, course=matching_course):
                    sw.save()

        result_serializer = SchemeOfWorkSerializer(scheme)
        return Response(result_serializer.data, status=status.HTTP_200_OK)
