from rest_framework import serializers

from .models import ExamSchedule, TimetableEntry


class TimetableEntrySerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    section_name = serializers.CharField(source="section.label", read_only=True)
    classroom_name = serializers.CharField(source="classroom.name", read_only=True)
    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = TimetableEntry
        fields = [
            "id",
            "term",
            "day",
            "start_time",
            "end_time",
            "room",
            "course",
            "course_code",
            "course_name",
            "section",
            "section_name",
            "classroom",
            "classroom_name",
            "teacher_name",
            "assigned_by",
            "published",
        ]
        read_only_fields = ["assigned_by"]

    def get_teacher_name(self, obj):
        if not obj.course.teacher:
            return None
        return obj.course.teacher.username

    def validate(self, attrs):
        day = attrs.get("day", getattr(self.instance, "day", None))
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))
        room = attrs.get("room", getattr(self.instance, "room", None))
        course = attrs.get("course", getattr(self.instance, "course", None))
        term = attrs.get("term", getattr(self.instance, "term", None))
        section = attrs.get("section", getattr(self.instance, "section", None))
        classroom = attrs.get("classroom", getattr(self.instance, "classroom", None))

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")

        if course and course.section:
            if section and section.id != course.section_id:
                raise serializers.ValidationError("Timetable section must match the course section.")
            attrs["section"] = course.section
            section = course.section
        if classroom and not room:
            attrs["room"] = classroom.name
            room = classroom.name

        if not all([day, start_time, end_time, room, term, course]):
            return attrs

        conflicts = TimetableEntry.objects.filter(term=term, day=day).exclude(pk=getattr(self.instance, "pk", None))
        conflicts = conflicts.filter(start_time__lt=end_time, end_time__gt=start_time)
        if section:
            section_conflict = conflicts.filter(section=section).first()
            if section_conflict:
                raise serializers.ValidationError(f"Section conflict with {section_conflict.course.code}.")

        room_conflict = conflicts.filter(room__iexact=room).first()
        if room_conflict:
            raise serializers.ValidationError(f"Room conflict with {room_conflict.course.code}.")
        if classroom:
            classroom_conflict = conflicts.filter(classroom=classroom).first()
            if classroom_conflict:
                raise serializers.ValidationError(f"Classroom conflict with {classroom_conflict.course.code}.")

        if course.teacher_id:
            teacher_conflict = conflicts.filter(course__teacher_id=course.teacher_id).first()
            if teacher_conflict:
                raise serializers.ValidationError(f"Teacher conflict with {teacher_conflict.course.code}.")

        return attrs


class ExamScheduleSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    section_name = serializers.CharField(source="section.label", read_only=True)
    classroom_name = serializers.CharField(source="classroom.name", read_only=True)
    teacher_name = serializers.CharField(source="course.teacher.username", read_only=True)

    class Meta:
        model = ExamSchedule
        fields = [
            "id",
            "term",
            "date",
            "start_time",
            "end_time",
            "room",
            "course",
            "course_code",
            "course_name",
            "section",
            "section_name",
            "classroom",
            "classroom_name",
            "description",
            "teacher_name",
            "scheduled_by",
            "published",
        ]
        read_only_fields = ["scheduled_by"]

    def validate(self, attrs):
        date = attrs.get("date", getattr(self.instance, "date", None))
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))
        room = attrs.get("room", getattr(self.instance, "room", None))
        course = attrs.get("course", getattr(self.instance, "course", None))
        term = attrs.get("term", getattr(self.instance, "term", None))
        section = attrs.get("section", getattr(self.instance, "section", None))
        classroom = attrs.get("classroom", getattr(self.instance, "classroom", None))

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")

        if course and course.section:
            if section and section.id != course.section_id:
                raise serializers.ValidationError("Exam section must match the course section.")
            attrs["section"] = course.section
            section = course.section
        if classroom and not room:
            attrs["room"] = classroom.name
            room = classroom.name

        if not all([date, start_time, end_time, room, course, term]):
            return attrs

        conflicts = ExamSchedule.objects.filter(term=term, date=date).exclude(pk=getattr(self.instance, "pk", None))
        conflicts = conflicts.filter(start_time__lt=end_time, end_time__gt=start_time)
        if section:
            section_conflict = conflicts.filter(section=section).first()
            if section_conflict:
                raise serializers.ValidationError(f"Exam section conflict with {section_conflict.course.code}.")

        room_conflict = conflicts.filter(room__iexact=room).first()
        if room_conflict:
            raise serializers.ValidationError(f"Exam room conflict with {room_conflict.course.code}.")
        if classroom:
            classroom_conflict = conflicts.filter(classroom=classroom).first()
            if classroom_conflict:
                raise serializers.ValidationError(f"Exam classroom conflict with {classroom_conflict.course.code}.")

        if course.teacher_id:
            teacher_conflict = conflicts.filter(course__teacher_id=course.teacher_id).first()
            if teacher_conflict:
                raise serializers.ValidationError(f"Teacher conflict with {teacher_conflict.course.code}.")

        return attrs
