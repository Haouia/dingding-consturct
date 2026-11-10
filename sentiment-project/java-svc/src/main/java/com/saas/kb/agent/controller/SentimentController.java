package com.saas.kb.agent.controller;

import com.saas.kb.agent.entity.SentimentRecord;
import com.saas.kb.agent.mapper.SentimentRecordMapper;
import com.saas.kb.agent.notifier.AlertNotifier;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map; // 引入 Map

@RestController
@RequestMapping("/sentiment")
public class SentimentController {

    @Autowired
    private SentimentRecordMapper sentimentRecordMapper;

    @Autowired
    private AlertNotifier alertNotifier;

    @PostMapping("/save")
    public Map<String, Object> save(@RequestBody SentimentRecord sentimentRecord) {
        // 补上入库时间
        System.out.println("【N8N发来的数据】: " + sentimentRecord.toString());
        sentimentRecord.setCreateTime(LocalDateTime.now());
        sentimentRecordMapper.insert(sentimentRecord);

        // 告警决策：只要【负面+高危】才惊动负责人，其余静默
        if ("负面".equals(sentimentRecord.getSentiment()) && "高".equals(sentimentRecord.getLevel())) {
            alertNotifier.sendAlert(sentimentRecord.getTitle(), sentimentRecord.getContent());
        }

        // 返回标准的 JSON 结构给 N8N
        return Map.of("code", 200, "msg", "落库成功", "id", sentimentRecord.getId());
    }

    // 新增：获取所有数据（实际生产可以加个按日期筛选）
    @GetMapping("/list")
    public List<SentimentRecord> getList() {
        return sentimentRecordMapper.selectList(null);
    }
}