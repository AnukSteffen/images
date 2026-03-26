package com.wu.personai.net

import com.google.gson.Gson
import com.wu.personai.data.ChatMessage
import com.wu.personai.data.ChatRequest
import com.wu.personai.data.ChatStreamResponse
import com.wu.personai.local.LLMEngine
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.flowOn
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody

class CloudEngine : LLMEngine{
    private val client = OkHttpClient.Builder().build()
    private val gson = Gson()

    private val API_KEY = "ec538ce4-76a2-429a-b76d-885fbf285441"
    private val ENDPOINT_ID = "ep-20260323181337-nr4sg"

    override fun generateResponse(messages: List<ChatMessage>) : Flow<String> = callbackFlow {

        val apiMessages = messages.takeLast(10).map { // 1. 转换数据格式
            mapOf(
                "role" to (if(it.isUser) "user" else "assistant"),
                "content" to it.content
            )
        }

        val requestBody = ChatRequest(
            model = ENDPOINT_ID,
            messages = apiMessages, // 2. 发送完整的历史记录
            stream = true
        )

        val request = Request.Builder()
            .url("https://ark.cn-beijing.volces.com/api/v3/chat/completions")
            .header("Authorization", "Bearer $API_KEY")
            .post(gson.toJson(requestBody).toRequestBody("application/json".toMediaType()))
            .build()

        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) {
                trySend("出错了: ${response.code}")
                close()
                return@use
            }

            response.body?.source()?.let { source ->
                while (!source.exhausted()) { //还有数据
                    val line = source.readUtf8Line() //readUtf8Line()：每次只抓取其中一行
                    if (line != null && line.startsWith("data: ")) {
                        val data = line.substring(6)
                        if (data == "[DONE]") break // 传输结束

                        val res = gson.fromJson(data, ChatStreamResponse::class.java) //把过滤后的字符串交给 Gson，转成 ChatStreamResponse 对象
                        res.choices.firstOrNull()?.delta?.content?.let {
                            trySend(it) // 发送每一个字给UI
                        }
                    }
                }
            }
        }
        close()
    }.flowOn(Dispatchers.IO)
}