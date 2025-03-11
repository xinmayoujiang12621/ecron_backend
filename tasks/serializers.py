from rest_framework import serializers
from .models import Task, Job, Node

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class JobSerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source='task.name', read_only=True)

    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ('start_time', 'end_time')

class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'last_heartbeat') 