package com.saas.kb.agent.entity;
//舆情记录实体类 一个Java类对应一张MySQL表，字段对应列
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data //自动生成setter/getter/toString
@TableName("sentiment_record") // 告诉MyBatis-Plus 对应哪一张表
public class SentimentRecord {
    @TableId(type = IdType.ASSIGN_ID) // 主键策略：雪花算法自动生成，insert 时不用setId操作
    private Long id;
    private Long tenantId; //租户id,不同租户数据不互通
    private String title; //舆情标题
    private String content; //舆情正文
    private String sentiment; // 情感：正面/中性/负面
    private String level; // 预警级别 高/中/低【和Python输出字段名一致】
    private String source; //来源：微博/新闻/论坛……
    private LocalDateTime createTime; //入库时间
}