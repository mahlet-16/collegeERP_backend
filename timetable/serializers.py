from rest_framework import serializers

from .models import ExamSchedule, TimetableEntry


class TimetableEntrySerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)
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

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")

        if not all([day, start_time, end_time, room, term, course]):
            return attrs

        conflicts = TimetableEntry.objects.filter(term=term, day=day).exclude(pk=getattr(self.instance, "pk", None))
        conflicts = conflicts.filter(start_time__lt=end_time, end_time__gt=start_time)
        room_conflict = conflicts.filter(room__iexact=room).first()
        if room_conflict:
            raise serializers.ValidationError(f"Room conflict with {room_conflict.course.code}.")

        if course.teacher_id:
            teacher_conflict = conflicts.filter(course__teacher_id=course.teacher_id).first()
            if teacher_conflict:
                raise serializers.ValidationError(f"Teacher conflict with {teacher_conflict.course.code}.")

        return attrs


class ExamScheduleSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)
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

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")

        if not all([date, start_time, end_time, room, course, term]):
            return attrs

        conflicts = ExamSchedule.objects.filter(term=term, date=date).exclude(pk=getattr(self.instance, "pk", None))
        conflicts = conflicts.filter(start_time__lt=end_time, end_time__gt=start_time)
        room_conflict = conflicts.filter(room__iexact=room).first()
        if room_conflict:
            raise serializers.ValidationError(f"Exam room conflict with {room_conflict.course.code}.")

        if course.teacher_id:
            teacher_conflict = conflicts.filter(course__teacher_id=course.teacher_id).first()
            if teacher_conflict:
                raise serializers.ValidationError(f"Teacher conflict with {teacher_conflict.course.code}.")

        return attrs
