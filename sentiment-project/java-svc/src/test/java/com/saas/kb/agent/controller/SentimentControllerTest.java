package com.saas.kb.agent.controller;

import com.saas.kb.agent.entity.SentimentRecord;
import com.saas.kb.agent.mapper.SentimentRecordMapper;
import com.saas.kb.agent.notifier.AlertNotifier;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;

/**
 * SentimentController 单元测试。
 *
 * <p>纯 Mockito 单测：@Mock 掉 Mapper 和 AlertNotifier，不启动 Spring 容器、不连 MySQL，
 * 只验证 Controller 内部的落库与告警决策逻辑。</p>
 */
@ExtendWith(MockitoExtension.class)
class SentimentControllerTest {

    /** 模拟 MyBatis-Plus 雪花算法生成的主键，用于断言返回值 id。 */
    private static final long SNOWFLAKE_ID = 123L;

    @Mock
    private SentimentRecordMapper sentimentRecordMapper;

    @Mock
    private AlertNotifier alertNotifier;

    @InjectMocks
    private SentimentController sentimentController;

    @BeforeEach
    void setUp() {
        // insert 是 BaseMapper 的默认方法，Mockito 不会自动生成主键，
        // 这里用 doAnswer 回填 id（等价于雪花算法在 insert 时赋值），并返回受影响行数 1。
        doAnswer(invocation -> {
            SentimentRecord record = invocation.getArgument(0);
            record.setId(SNOWFLAKE_ID);
            return 1;
        }).when(sentimentRecordMapper).insert(any(SentimentRecord.class));
    }

    @Test
    @DisplayName("负面 + 高危：落库一次并触发一次告警，返回 code=200、id 非空")
    void save_negativeAndHigh_shouldPersistAndNotifyAlert() {
        SentimentRecord record = buildRecord("负面", "高");

        Map<String, Object> result = sentimentController.save(record);

        // 1. 落库恰好一次
        verify(sentimentRecordMapper, times(1)).insert(any(SentimentRecord.class));
        // 2. 高危告警恰好一次，且透传 title/content
        verify(alertNotifier, times(1)).sendAlert("测试标题", "测试正文");

        // 3. 返回值断言：code / id / msg
        assertThat(result.get("code")).isEqualTo(200);
        assertThat(result.get("id")).isEqualTo(SNOWFLAKE_ID);
        assertThat(result.get("msg")).isEqualTo("落库成功");
        // 4. Controller 补写的入库时间不能为空
        assertThat(record.getCreateTime()).isNotNull();
    }

    @Test
    @DisplayName("正面/低危：只落库，不触发告警，返回 code=200")
    void save_positiveOrLow_shouldPersistWithoutAlert() {
        SentimentRecord record = buildRecord("正面", "低");

        Map<String, Object> result = sentimentController.save(record);

        verify(sentimentRecordMapper, times(1)).insert(any(SentimentRecord.class));
        // 非【负面+高】组合，AlertNotifier 完全不应该被调用
        verifyNoInteractions(alertNotifier);

        assertThat(result.get("code")).isEqualTo(200);
        assertThat(result.get("id")).isEqualTo(SNOWFLAKE_ID);
        assertThat(result.get("msg")).isEqualTo("落库成功");
        assertThat(record.getCreateTime()).isNotNull();
    }

    private SentimentRecord buildRecord(String sentiment, String level) {
        SentimentRecord record = new SentimentRecord();
        record.setTenantId(1L);
        record.setTitle("测试标题");
        record.setContent("测试正文");
        record.setSentiment(sentiment);
        record.setLevel(level);
        record.setSource("微博");
        return record;
    }
}
