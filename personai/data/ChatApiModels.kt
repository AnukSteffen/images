package com.wu.personai.data

data class ChatRequest(
    val model: String,
    val messages: List<Map<String, String>>,
    val stream: Boolean = true // 必须开启流式
)

data class ChatStreamResponse(// 用于解析每一行返回的 Data
    val choices : List<Choice>
){
    data class Choice(val delta : Delta)
    data class Delta(val content : String)
}
