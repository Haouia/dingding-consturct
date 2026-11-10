package com.saas.kb.agent.notifier;
//告警通知类：把告警内容 POST给N8N的webhook，由N8N转发到钉钉

import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;

@Component
public class AlertNotifier {

    //N8N告警工作流的webhook地址
    // Tips:Java跑在宿主机，N8N跑在Docker容器中并映射5678，所以这里用的是localhost
    private static final String N8N_WEBHOOK="http://localhost:5678/webhook/alert";

    //WebClient 是Spring提供的HTTP客户端，用来发送POST请求
    private final WebClient webClient=WebClient.create();

    // 只做一件事【把title/content】交给N8N，发钉钉是N8N的活
    public void sendAlert(String title, String content) {
        webClient.post()
                .uri(N8N_WEBHOOK)
                .bodyValue(Map.of("title", title, "content", content))//转成{"title":...,"content":...}
                .retrieve() //获取响应
                .bodyToMono(String.class) //把响应体读成String
                .block();//block()方法会阻塞等待响应，直到收到响应为止
    }
}