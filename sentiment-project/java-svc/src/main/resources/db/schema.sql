-- ============================================================
-- 舆情监控管理端 建表脚本
-- 对应实体：com.saas.kb.agent.entity.SentimentRecord
-- 数据库：MySQL 8.x，字符集 utf8mb4（支持 emoji 等 4 字节字符）
-- 使用方式：mysql -u root -p project06 < schema.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS sentiment_record (
    id          BIGINT       PRIMARY KEY COMMENT '主键，MyBatis-Plus 雪花算法生成',
    tenant_id   BIGINT       DEFAULT NULL COMMENT '租户 ID，不同租户数据隔离',
    title       VARCHAR(255) DEFAULT NULL COMMENT '舆情标题',
    content     TEXT         COMMENT '舆情正文',
    sentiment   VARCHAR(16)  DEFAULT NULL COMMENT '情感倾向：正面/中性/负面',
    level       VARCHAR(16)  DEFAULT NULL COMMENT '预警级别：高/中/低',
    source      VARCHAR(64)  DEFAULT NULL COMMENT '来源：微博/新闻/论坛等',
    create_time DATETIME     DEFAULT NULL COMMENT '入库时间',
    KEY idx_sentiment_record_tenant_id (tenant_id),
    KEY idx_sentiment_record_create_time (create_time)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci
  COMMENT = '舆情记录表';
