from rest_framework import serializers

from .models import TimetableEntry


class TimetableEntrySerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)

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
            "assigned_by",
            "published",
        ]
        read_only_fields = ["assigned_by"]
