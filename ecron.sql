SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for tasks_job
-- ----------------------------
DROP TABLE IF EXISTS `tasks_job`;
CREATE TABLE `tasks_job`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '状态',
  `start_time` datetime(6) NOT NULL COMMENT '开始时间',
  `end_time` datetime(6) NULL DEFAULT NULL COMMENT '结束时间',
  `result` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '执行结果',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '错误信息',
  `task_id` bigint NOT NULL COMMENT '任务ID',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `tasks_job_task_id_fk`(`task_id` ASC) USING BTREE,
  CONSTRAINT `tasks_job_task_id_fk` FOREIGN KEY (`task_id`) REFERENCES `tasks_task` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 72 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '执行记录' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for tasks_node
-- ----------------------------
DROP TABLE IF EXISTS `tasks_node`;
CREATE TABLE `tasks_node`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点名称',
  `host` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '主机地址',
  `port` int NOT NULL COMMENT '端口',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'inactive' COMMENT '状态',
  `last_heartbeat` datetime(6) NULL DEFAULT NULL COMMENT '最后心跳',
  `created_at` datetime(6) NOT NULL COMMENT '创建时间',
  `updated_at` datetime(6) NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '节点' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for tasks_task
-- ----------------------------
DROP TABLE IF EXISTS `tasks_task`;
CREATE TABLE `tasks_task`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '任务名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '描述',
  `cron_expression` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'Cron表达式',
  `command` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '命令',
  `command_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '命令类型',
  `requirements` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '依赖包',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'active' COMMENT '状态',
  `created_at` datetime(6) NOT NULL COMMENT '创建时间',
  `updated_at` datetime(6) NOT NULL COMMENT '更新时间',
  `node_id` bigint NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `tasks_task_node_id_fk`(`node_id` ASC) USING BTREE,
  CONSTRAINT `tasks_task_node_id_fk` FOREIGN KEY (`node_id`) REFERENCES `tasks_node` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '任务' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
