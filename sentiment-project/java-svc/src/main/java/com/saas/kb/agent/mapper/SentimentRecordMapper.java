package com.saas.kb.agent.mapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.saas.kb.agent.entity.SentimentRecord;
import org.apache.ibatis.annotations.Mapper;
// 继承BaseMapper，insert/selectById/selectList等方法自动可用，基本不用写SQL
@Mapper //标记为Mapper，Spring启动自动扫描并生成实体类注入容器中
public interface SentimentRecordMapper extends BaseMapper<SentimentRecord>
{
//先留空，后续复杂业务需要可以再自定义方法
}