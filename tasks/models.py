from django.db import models

class Task(models.Model):
    name = models.CharField(max_length=100, verbose_name='任务名称')
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    cron_expression = models.CharField(max_length=100, verbose_name='Cron表达式')
    command = models.TextField(verbose_name='命令')
    command_type = models.CharField(max_length=20, choices=[
        ('http', 'HTTP'),
        ('shell', 'Shell'),
        ('python', 'Python')
    ], verbose_name='命令类型')
    requirements = models.TextField(blank=True, null=True, verbose_name='依赖包')
    status = models.CharField(max_length=20, choices=[
        ('active', '活跃'),
        ('paused', '暂停'),
        ('deleted', '已删除'),
        ('draft', '草稿')
    ], default='active', verbose_name='状态')
    node = models.ForeignKey(
        'Node',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='执行节点'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Job(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name='任务')
    status = models.CharField(max_length=20, choices=[
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败')
    ], verbose_name='状态')
    start_time = models.DateTimeField(auto_now_add=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    result = models.TextField(null=True, blank=True, verbose_name='执行结果')
    error_message = models.TextField(null=True, blank=True, verbose_name='错误信息')

    class Meta:
        verbose_name = '执行记录'
        verbose_name_plural = '执行记录'
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.task.name} - {self.status}"

class Node(models.Model):
    name = models.CharField(max_length=100, verbose_name='节点名称')
    host = models.CharField(max_length=100, verbose_name='主机地址')
    port = models.IntegerField(verbose_name='端口')
    status = models.CharField(max_length=20, choices=[
        ('active', '活跃'),
        ('inactive', '不活跃')
    ], default='inactive', verbose_name='状态')
    last_heartbeat = models.DateTimeField(null=True, blank=True, verbose_name='最后心跳')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '节点'
        verbose_name_plural = '节点'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})" 