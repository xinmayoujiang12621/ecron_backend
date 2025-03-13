from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
import requests
from .models import Task, Job, Node
from .serializers import TaskSerializer, JobSerializer, NodeSerializer
import time
import logging
import os

# 配置日志
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backend.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('backend')
logger.info(f"日志级别设置为: {log_level}")

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        task = self.get_object()
        
        # 检查任务状态
        if task.status != 'active':
            logger.warning(f"尝试执行非活动任务: {task.id}")
            return Response(
                {'error': '任务未激活'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查节点状态
        if not task.node or task.node.status != 'active':
            logger.warning(f"尝试在非活动节点上执行任务: {task.id}")
            return Response(
                {'error': '未分配活动节点'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 创建执行记录
        job = Job.objects.create(
            task=task,
            status='running'
        )
        
        logger.info(f"开始执行任务: {task.id}, 节点: {task.node.name}")
        
        try:
            # 直接调用执行节点的立即执行接口
            response = requests.post(
                f"http://{task.node.host}:{task.node.port}/tasks/{task.id}/execute",
                timeout=10,
                headers={'Content-Type': 'application/json; charset=utf-8'}
            )
            
            # 确保响应内容使用UTF-8解码
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                error_msg = f'执行任务失败: {response.text}'
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 更新执行记录
            job.status = 'success'
            job.result = '任务执行已启动'
            job.end_time = timezone.now()
            job.save()
            
            logger.info(f"任务执行已启动: {task.id}")
            
            return Response({
                'status': 'success',
                'message': '任务执行已启动'
            })
            
        except requests.exceptions.RequestException as e:
            # 更新执行记录
            job.status = 'failed'
            job.error_message = str(e)
            job.end_time = timezone.now()
            job.save()
            
            logger.error(f"任务执行请求失败: {task.id}, 错误: {str(e)}")
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except ValueError as e:
            # 更新执行记录
            job.status = 'failed'
            job.error_message = str(e)
            job.end_time = timezone.now()
            job.save()
            
            logger.error(f"任务执行值错误: {task.id}, 错误: {str(e)}")
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        task = self.get_object()
        
        # 检查节点状态
        if not task.node or task.node.status != 'active':
            logger.warning(f"尝试在非活动节点上暂停任务: {task.id}")
            return Response(
                {'error': '未分配活动节点'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"开始暂停任务: {task.id}, 节点: {task.node.name}")
        
        try:
            # 停止任务
            response = requests.post(
                f"http://{task.node.host}:5001/tasks/{task.id}/stop",
                timeout=10,
                headers={'Content-Type': 'application/json; charset=utf-8'}
            )
            
            # 确保响应内容使用UTF-8解码
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                error_msg = f'停止任务失败: {response.text}'
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 更新任务状态
            task.status = 'paused'
            task.save()
            
            logger.info(f"任务已暂停: {task.id}")
            
            return Response({'status': 'success', 'message': '任务已暂停'})
            
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.error(f"暂停任务失败: {task.id}, 错误: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        task = self.get_object()
        
        # 检查节点状态
        if not task.node or task.node.status != 'active':
            logger.warning(f"尝试在非活动节点上恢复任务: {task.id}")
            return Response(
                {'error': '未分配活动节点'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"开始恢复任务: {task.id}, 节点: {task.node.name}")
        
        try:
            # 启动任务
            response = requests.post(
                f"http://{task.node.host}:{task.node.port}/tasks/{task.id}/start",
                timeout=10,
                headers={'Content-Type': 'application/json; charset=utf-8'}
            )
            
            # 确保响应内容使用UTF-8解码
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                error_msg = f'启动任务失败: {response.text}'
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 更新任务状态
            task.status = 'active'
            task.save()
            
            logger.info(f"任务已恢复: {task.id}")
            
            return Response({'status': 'success', 'message': '任务已恢复'})
            
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.error(f"恢复任务失败: {task.id}, 错误: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def assign_node(self, request, pk=None):
        """分配执行节点"""
        task = self.get_object()
        node_id = request.data.get('node_id')

        if not node_id:
            logger.warning(f"分配节点请求缺少节点ID: task_id={task.id}")
            return Response(
                {'error': '节点ID是必填项'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            node = Node.objects.get(id=node_id)
            if node.status != 'active':
                logger.warning(f"尝试分配非活动节点: task_id={task.id}, node_id={node_id}")
                return Response(
                    {'error': '所选节点未激活'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 检查节点健康状态
            try:
                logger.debug(f"检查节点健康状态: task_id={task.id}, node={node.name}")
                health_response = requests.get(
                    f"http://{node.host}:{node.port}/health",
                    timeout=5
                )
                
                if health_response.status_code != 200:
                    error_msg = f'节点健康检查失败: {health_response.text}'
                    logger.error(error_msg)
                    return Response(
                        {'error': error_msg},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                
                health_data = health_response.json()
                if health_data.get('status') != 'active':
                    error_msg = f'节点状态异常: {health_data.get("status")}'
                    logger.error(error_msg)
                    return Response(
                        {'error': error_msg},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                    
            except requests.exceptions.RequestException as e:
                error_msg = f'无法连接到节点: {str(e)}'
                logger.error(error_msg)
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # 如果任务已经在运行，先停止
            old_node = task.node
            if task.status == 'active' and old_node:
                logger.info(f"停止旧节点上的任务: task_id={task.id}, old_node={old_node.name}")
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = requests.post(
                            f"http://{old_node.host}:{old_node.port}/tasks/{task.id}/stop",
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            logger.info(f'成功停止旧节点上的任务: {task.id}')
                            break
                        elif response.status_code == 404:
                            # 任务不存在，可以继续
                            logger.debug(f'旧节点上不存在任务: {task.id}')
                            break
                        else:
                            logger.warning(f'停止旧任务失败 (尝试 {attempt+1}/{max_retries}): {response.text}')
                            if attempt == max_retries - 1:
                                # 最后一次尝试失败，但仍继续分配新节点
                                logger.error(f'停止旧任务失败，但将继续分配新节点')
                    except Exception as e:
                        logger.warning(f'停止旧任务时出错 (尝试 {attempt+1}/{max_retries}): {str(e)}')
                        if attempt == max_retries - 1:
                            # 最后一次尝试失败，但仍继续分配新节点
                            logger.error(f'停止旧任务失败，但将继续分配新节点')
                    
                    # 如果不是最后一次尝试，等待后重试
                    if attempt < max_retries - 1:
                        time.sleep(1)

            # 更新任务的执行节点
            task.node = node
            task.save()
            logger.info(f"已将任务分配给新节点: task_id={task.id}, node={node.name}")
            
            # 如果任务是活动状态，发送任务到新节点并启动
            success = True
            error_message = None
            
            if task.status == 'active':
                logger.info(f"开始在新节点上设置任务: task_id={task.id}, node={node.name}")
                # 准备任务数据
                task_data = {
                    "task_id": task.id,
                    "name": task.name,
                    "cron_expression": task.cron_expression,
                    "command": task.command,
                    "command_type": task.command_type,
                    "requirements": task.requirements
                }
                
                # 发送任务详情
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = requests.post(
                            f"http://{node.host}:{node.port}/tasks",
                            json=task_data,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            logger.info(f'成功发送任务详情到新节点: {task.id}')
                            break
                        else:
                            error_message = f'发送任务详情失败 (尝试 {attempt+1}/{max_retries}): {response.text}'
                            logger.warning(error_message)
                            if attempt == max_retries - 1:
                                logger.error(f'发送任务详情失败: {task.id}')
                                success = False
                    except Exception as e:
                        error_message = f'发送任务详情时出错 (尝试 {attempt+1}/{max_retries}): {str(e)}'
                        logger.warning(error_message)
                        if attempt == max_retries - 1:
                            logger.error(f'发送任务详情时出错: {task.id}, 错误: {str(e)}')
                            success = False
                    
                    # 如果不是最后一次尝试，等待后重试
                    if attempt < max_retries - 1:
                        time.sleep(1)
                
                # 如果发送任务详情成功，启动任务
                if success:
                    logger.info(f"开始启动新节点上的任务: task_id={task.id}")
                    for attempt in range(max_retries):
                        try:
                            response = requests.post(
                                f"http://{node.host}:{node.port}/tasks/{task.id}/start",
                                timeout=10
                            )
                            
                            if response.status_code == 200:
                                logger.info(f'成功启动新节点上的任务: {task.id}')
                                break
                            else:
                                error_message = f'启动任务失败 (尝试 {attempt+1}/{max_retries}): {response.text}'
                                logger.warning(error_message)
                                if attempt == max_retries - 1:
                                    logger.error(f'启动任务失败: {task.id}')
                                    success = False
                        except Exception as e:
                            error_message = f'启动任务时出错 (尝试 {attempt+1}/{max_retries}): {str(e)}'
                            logger.warning(error_message)
                            if attempt == max_retries - 1:
                                logger.error(f'启动任务时出错: {task.id}, 错误: {str(e)}')
                                success = False
                        
                        # 如果不是最后一次尝试，等待后重试
                        if attempt < max_retries - 1:
                            time.sleep(1)

            # 返回响应
            response_data = {
                'status': 'success' if success else 'partial_success',
                'message': '节点分配成功' + ('' if success else '，但任务部署失败'),
                'node': {
                    'id': node.id,
                    'name': node.name,
                    'host': node.host
                }
            }
            
            if not success and error_message:
                response_data['error_detail'] = error_message
                
            logger.info(f"节点分配完成: task_id={task.id}, node={node.name}, success={success}")
            return Response(response_data)

        except Node.DoesNotExist:
            logger.error(f"指定的节点不存在: task_id={task.id}, node_id={node_id}")
            return Response(
                {'error': '指定的节点不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def redeploy(self, request, pk=None):
        """重新下发任务脚本到执行节点"""
        task = self.get_object()
        
        # 检查节点状态
        if not task.node or task.node.status != 'active':
            logger.warning(f"尝试向非活动节点下发任务: {task.id}")
            return Response(
                {'error': '未分配活动节点'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"开始重新下发任务: {task.id}, 节点: {task.node.name}")
        
        # 准备任务数据
        task_data = {
            "task_id": task.id,
            "name": task.name,
            "cron_expression": task.cron_expression,
            "command": task.command,
            "command_type": task.command_type,
            "requirements": task.requirements,
            "is_active": task.status == 'active'
        }
        
        # 发送任务到执行节点
        max_retries = 3
        success = False
        
        for attempt in range(max_retries):
            try:
                logger.info(f"尝试下发任务 (尝试 {attempt+1}/{max_retries}): {task.id}")
                response = requests.post(
                    f"http://{task.node.host}:{task.node.port}/tasks",
                    json=task_data,
                    timeout=10,
                    headers={'Content-Type': 'application/json; charset=utf-8'}
                )
                
                # 确保响应内容使用UTF-8解码
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    logger.info(f"成功下发任务: {task.id}")
                    success = True
                    break
                else:
                    logger.error(f"下发任务失败 (尝试 {attempt+1}/{max_retries}): {response.text}")
            except Exception as e:
                logger.error(f"下发任务时出错 (尝试 {attempt+1}/{max_retries}): {str(e)}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                time.sleep(1)
        
        if not success:
            logger.error(f"重新下发任务失败，已达到最大重试次数: {task.id}")
            return Response(
                {'error': '重新下发任务失败，请检查执行节点状态'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # 如果任务状态为活动，重新启动任务
        if task.status == 'active':
            for attempt in range(max_retries):
                try:
                    logger.info(f"尝试启动任务 (尝试 {attempt+1}/{max_retries}): {task.id}")
                    start_response = requests.post(
                        f"http://{task.node.host}:{task.node.port}/tasks/{task.id}/start",
                        timeout=10,
                        headers={'Content-Type': 'application/json; charset=utf-8'}
                    )
                    
                    # 确保响应内容使用UTF-8解码
                    start_response.encoding = 'utf-8'
                    
                    if start_response.status_code == 200:
                        logger.info(f"成功启动任务: {task.id}")
                        break
                    else:
                        logger.error(f"启动任务失败 (尝试 {attempt+1}/{max_retries}): {start_response.text}")
                except Exception as e:
                    logger.error(f"启动任务时出错 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        logger.info(f"任务重新下发完成: {task.id}")
        return Response({'status': 'success', 'message': '任务已重新下发'})

    def destroy(self, request, *args, **kwargs):
        """删除任务"""
        task = self.get_object()
        
        # 如果任务在运行，先停止
        if task.status == 'active' and task.node:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        f"http://{task.node.host}:{task.node.port}/tasks/{task.id}/stop",
                        timeout=10,
                        headers={'Content-Type': 'application/json; charset=utf-8'}
                    )
                    
                    # 确保响应内容使用UTF-8解码
                    response.encoding = 'utf-8'
                    
                    if response.status_code == 200:
                        logger.info(f'成功停止任务: {task.id}')
                        break
                    elif response.status_code == 404:
                        # 任务不存在，可以继续
                        logger.info(f'执行节点上不存在任务: {task.id}')
                        break
                    else:
                        logger.error(f'停止任务失败 (尝试 {attempt+1}/{max_retries}): {response.text}')
                except Exception as e:
                    logger.error(f'停止任务时出错 (尝试 {attempt+1}/{max_retries}): {str(e)}')
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        # 删除执行节点上的任务
        if task.node:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.delete(
                        f"http://{task.node.host}:{task.node.port}/tasks/{task.id}",
                        timeout=10,
                        headers={'Content-Type': 'application/json; charset=utf-8'}
                    )
                    
                    # 确保响应内容使用UTF-8解码
                    response.encoding = 'utf-8'
                    
                    if response.status_code == 200:
                        logger.info(f'成功删除执行节点上的任务: {task.id}')
                        break
                    elif response.status_code == 404:
                        # 任务不存在，可以继续
                        logger.info(f'执行节点上不存在任务: {task.id}')
                        break
                    else:
                        logger.error(f'删除执行节点任务失败 (尝试 {attempt+1}/{max_retries}): {response.text}')
                except Exception as e:
                    logger.error(f'删除执行节点任务时出错 (尝试 {attempt+1}/{max_retries}): {str(e)}')
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        # 删除数据库中的任务
        return super().destroy(request, *args, **kwargs)
        
    def create(self, request, *args, **kwargs):
        """创建任务"""
        response = super().create(request, *args, **kwargs)
        
        # 如果创建成功且指定了节点，发送任务到执行节点
        if response.status_code == status.HTTP_201_CREATED:
            task_id = response.data.get('id')
            if task_id:
                task = Task.objects.get(id=task_id)
                if task.node and task.status == 'active':
                    # 检查节点健康状态
                    try:
                        health_response = requests.get(
                            f"http://{task.node.host}:{task.node.port}/health",
                            timeout=5
                        )
                        
                        # 确保响应内容使用UTF-8解码
                        health_response.encoding = 'utf-8'
                        
                        if health_response.status_code != 200 or health_response.json().get('status') != 'active':
                            logger.error(f'节点健康检查失败，任务创建后不会自动部署: {task.id}')
                            return response
                            
                    except requests.exceptions.RequestException as e:
                        logger.error(f'无法连接到节点，任务创建后不会自动部署: {task.id}, 错误: {str(e)}')
                        return response
                    
                    # 准备任务数据
                    task_data = {
                        "task_id": task.id,
                        "name": task.name,
                        "cron_expression": task.cron_expression,
                        "command": task.command,
                        "command_type": task.command_type,
                        "requirements": task.requirements
                    }
                    
                    # 发送任务详情
                    max_retries = 3
                    success = False
                    
                    for attempt in range(max_retries):
                        try:
                            send_response = requests.post(
                                f"http://{task.node.host}:{task.node.port}/tasks",
                                json=task_data,
                                timeout=10,
                                headers={'Content-Type': 'application/json; charset=utf-8'}
                            )
                            
                            # 确保响应内容使用UTF-8解码
                            send_response.encoding = 'utf-8'
                            
                            if send_response.status_code == 200:
                                logger.info(f'成功发送任务详情到节点: {task.id}')
                                success = True
                                break
                            else:
                                logger.error(f'发送任务详情失败 (尝试 {attempt+1}/{max_retries}): {send_response.text}')
                        except Exception as e:
                            logger.error(f'发送任务详情时出错 (尝试 {attempt+1}/{max_retries}): {str(e)}')
                        
                        # 如果不是最后一次尝试，等待后重试
                        if attempt < max_retries - 1:
                            time.sleep(1)
                    
                    # 如果发送任务详情成功，启动任务
                    if success:
                        for attempt in range(max_retries):
                            try:
                                start_response = requests.post(
                                    f"http://{task.node.host}:{task.node.port}/tasks/{task.id}/start",
                                    timeout=10,
                                    headers={'Content-Type': 'application/json; charset=utf-8'}
                                )
                                
                                # 确保响应内容使用UTF-8解码
                                start_response.encoding = 'utf-8'
                                
                                if start_response.status_code == 200:
                                    logger.info(f'成功启动节点上的任务: {task.id}')
                                    break
                                else:
                                    logger.error(f'启动任务失败 (尝试 {attempt+1}/{max_retries}): {start_response.text}')
                            except Exception as e:
                                logger.error(f'启动任务时出错 (尝试 {attempt+1}/{max_retries}): {str(e)}')
                            
                            # 如果不是最后一次尝试，等待后重试
                            if attempt < max_retries - 1:
                                time.sleep(1)
        
        return response
        
    def update(self, request, *args, **kwargs):
        """更新任务"""
        old_task = self.get_object()
        old_node = old_task.node
        old_status = old_task.status
        
        response = super().update(request, *args, **kwargs)
        
        # 如果更新成功，检查是否需要更新执行节点上的任务
        if response.status_code == status.HTTP_200_OK:
            task = self.get_object()
            
            # 如果节点发生变化或任务内容变化
            if task.node and (task.node != old_node or 
                             task.name != old_task.name or
                             task.cron_expression != old_task.cron_expression or
                             task.command != old_task.command or
                             task.command_type != old_task.command_type or
                             task.requirements != old_task.requirements):
                
                # 检查新节点健康状态
                try:
                    health_response = requests.get(
                        f"http://{task.node.host}:{task.node.port}/health",
                        timeout=5
                    )
                    
                    # 确保响应内容使用UTF-8解码
                    health_response.encoding = 'utf-8'
                    
                    if health_response.status_code != 200 or health_response.json().get('status') != 'active':
                        logger.error(f'节点健康检查失败，任务更新后不会自动部署: {task.id}')
                        return response
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f'无法连接到节点，任务更新后不会自动部署: {task.id}, 错误: {str(e)}')
                    return response
                
                # 如果旧节点存在且任务在运行，先停止旧任务
                if old_node and old_status == 'active':
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            stop_response = requests.post(
                                f"http://{old_node.host}:{old_node.port}/tasks/{task.id}/stop",
                                timeout=10,
                                headers={'Content-Type': 'application/json; charset=utf-8'}
                            )
                            
                            # 确保响应内容使用UTF-8解码
                            stop_response.encoding = 'utf-8'
                            
                            if stop_response.status_code == 200:
                                logger.info(f'成功停止旧节点上的任务: {task.id}')
                                break
                            elif stop_response.status_code == 404:
                                # 任务不存在，可以继续
                                logger.info(f'旧节点上不存在任务: {task.id}')
                                break
                            else:
                                logger.error(f'停止旧任务失败 (尝试 {attempt+1}/{max_retries}): {stop_response.text}')
                        except Exception as e:
                            logger.error(f'停止旧任务时出错 (尝试 {attempt+1}/{max_retries}): {str(e)}')
                        
                        # 如果不是最后一次尝试，等待后重试
                        if attempt < max_retries - 1:
                            time.sleep(1)
                
                # 准备任务数据
                task_data = {
                    "task_id": task.id,
                    "name": task.name,
                    "cron_expression": task.cron_expression,
                    "command": task.command,
                    "command_type": task.command_type,
                    "requirements": task.requirements
                }
                
                # 发送任务到新节点
                max_retries = 3
                success = False
                
                for attempt in range(max_retries):
                    try:
                        send_response = requests.post(
                            f"http://{task.node.host}:{task.node.port}/tasks",
                            json=task_data,
                            timeout=10,
                            headers={'Content-Type': 'application/json; charset=utf-8'}
                        )
                        
                        # 确保响应内容使用UTF-8解码
                        send_response.encoding = 'utf-8'
                        
                        if send_response.status_code == 200:
                            logger.info(f'成功发送任务详情到新节点: {task.id}')
                            success = True
                            break
                        else:
                            logger.error(f'发送任务详情失败 (尝试 {attempt+1}/{max_retries}): {send_response.text}')
                    except Exception as e:
                        logger.error(f'发送任务详情时出错 (尝试 {attempt+1}/{max_retries}): {str(e)}')
                    
                    # 如果不是最后一次尝试，等待后重试
                    if attempt < max_retries - 1:
                        time.sleep(1)
                
                # 如果任务是活动状态且发送任务详情成功，启动任务
                if task.status == 'active' and success:
                    for attempt in range(max_retries):
                        try:
                            start_response = requests.post(
                                f"http://{task.node.host}:{task.node.port}/tasks/{task.id}/start",
                                timeout=10,
                                headers={'Content-Type': 'application/json; charset=utf-8'}
                            )
                            
                            # 确保响应内容使用UTF-8解码
                            start_response.encoding = 'utf-8'
                            
                            if start_response.status_code == 200:
                                logger.info(f'成功启动新节点上的任务: {task.id}')
                                break
                            else:
                                logger.error(f'启动任务失败 (尝试 {attempt+1}/{max_retries}): {start_response.text}')
                        except Exception as e:
                            logger.error(f'启动任务时出错 (尝试 {attempt+1}/{max_retries}): {str(e)}')
                        
                        # 如果不是最后一次尝试，等待后重试
                        if attempt < max_retries - 1:
                            time.sleep(1)
        
        return response

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer

    def get_queryset(self):
        queryset = Job.objects.all()
        task_id = self.request.query_params.get('task_id', None)
        if task_id is not None:
            queryset = queryset.filter(task_id=task_id)
        return queryset

class NodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer

    @action(detail=True, methods=['get'])
    def check_health(self, request, pk=None):
        """
        检查执行节点的健康状态
        通过请求执行节点的/health接口，探测节点是否存活
        """
        node = self.get_object()

        try:
            # 设置较短的超时时间，避免长时间等待
            url = f"http://{node.host}:{node.port}/health"
            logger.info(f"正在检查节点健康状态: {node.name}, URL: {url}")

            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                # 更新节点状态
                node.status = 'active'
                node.last_heartbeat = timezone.now()
                node.save()

                # 返回执行节点的健康信息
                health_data = response.json()
                return Response({
                    'node': self.get_serializer(node).data,
                    'health': health_data,
                    'message': '节点健康检查成功'
                })
            else:
                logger.warning(f"节点健康检查失败: {node.name}, 状态码: {response.status_code}")
                return Response({
                    'node': self.get_serializer(node).data,
                    'error': f'节点返回非200状态码: {response.status_code}',
                    'message': '节点健康检查失败'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except requests.RequestException as e:
            logger.error(f"节点健康检查异常: {node.name}, 错误: {str(e)}")

            # 更新节点状态为不活跃
            node.status = 'inactive'
            node.save()

            return Response({
                'node': self.get_serializer(node).data,
                'error': str(e),
                'message': '节点健康检查失败，无法连接到节点'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @action(detail=False, methods=['post'])
    def heartbeat(self, request):
        name = request.data.get('name')
        host = request.data.get('host')
        port = request.data.get('port')

        logger.debug(f"收到心跳请求: name={name}, host={host}, port={port}")

        if not all([name, host, port]):
            logger.warning(f"心跳请求缺少必要字段: {request.data}")
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 只允许端口为 5001 的执行节点注册
        # if port != 5001:
        #     logger.warning(f"非执行节点尝试注册: port={port}")
        #     return Response(
        #         {'error': 'Only executor nodes (port 5001) are allowed to register'},
        #         status=status.HTTP_403_FORBIDDEN
        #     )

        node, created = Node.objects.update_or_create(
            name=name,
            defaults={
                'host': host,
                'port': port,
                'status': 'active',
                'last_heartbeat': timezone.now()
            }
        )

        if created:
            logger.info(f"新执行节点注册: name={name}, host={host}, port={port}")
        else:
            logger.debug(f"执行节点心跳更新: name={name}, host={host}, port={port}")

        serializer = self.get_serializer(node)
        return Response(serializer.data) 