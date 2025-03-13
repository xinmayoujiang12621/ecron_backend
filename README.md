### 运行环境
- python=3.12
- mysql=8.0

### 环境变量处理
将`.env.example`改名为`.env`，修改其内容。


### 镜像处理
```
打包镜像
docker build -t ecron_backend:1.0 .
运行镜像
docker run -d -p 20130:20130 --name ecron_backend --network host ecron_backend:1.0
```