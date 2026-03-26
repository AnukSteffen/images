package com.wu.personai.repository

import android.content.Context
import android.util.Log
import com.google.mediapipe.tasks.genai.llminference.LlmInference
import com.google.mediapipe.tasks.genai.llminference.LlmInferenceSession
import com.wu.personai.data.ChatMessage
import com.wu.personai.local.LLMEngine
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.Dispatchers
import java.util.concurrent.atomic.AtomicReference
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class LocalLLMEngine @Inject constructor(
    @ApplicationContext private val context: Context
) : LLMEngine {

    private var llmInference: LlmInference? = null
    private var session: LlmInferenceSession? = null
    private val isBusy = AtomicReference(false)
    private var isSeeded = false //是否已经注入了初始人设（种子）

    init{
        initialize()
    }

    private fun initialize(): Boolean {
        val modelPath = context.filesDir.absolutePath + "/gemma-1.1-2b-it-cpu-int4.bin"
        try {
            val options = LlmInference.LlmInferenceOptions.builder() // 1. 配置引擎：指定 CPU 推理，避免 libvndksupport 报错
                .setModelPath(modelPath)
                .setMaxTokens(1024)
                .setPreferredBackend(LlmInference.Backend.CPU)
                .build()
            llmInference = LlmInference.createFromOptions(context, options)

            if (llmInference != null) {
                createNewSession()// 2. 创建持久化 Session
            }


            Log.d("LocalLLM", "模型加载成功")
            return true
        } catch (e: Exception) {
            Log.e("LocalLLM", "初始化失败", e)
            return false
        }
    }

    private fun createNewSession() {
        llmInference?.let {
            val sessionOptions = LlmInferenceSession.LlmInferenceSessionOptions.builder()
                .setTemperature(0.7f) // 参考原项目，使用标准温度
                .setTopK(40)
                .build()
            session = LlmInferenceSession.createFromOptions(it, sessionOptions)
            isSeeded = false // 重置种子状态
        }
    }

    override fun generateResponse(messages: List<ChatMessage>): Flow<String> = callbackFlow {
        val currentSession = session ?: run {
            trySend("本地模型未就绪")
            close()
            return@callbackFlow
        }

        val systemPrompt = """
            你是御云岛虚拟社交平台上的一个AI角色。
            【回复要求】
            1. 回复要极短，一两句话
            2. 严禁括号和心理描写
            3. 要口语化、自然
        """.trimIndent()

        val historyText = messages.takeIf { it.size > 1 }
            ?.dropLast(1)  // 去掉最后的用户消息
            ?.joinToString("\n") {
                "${if(it.isUser) "用户" else "助手"}: ${it.content}"
            } ?: ""

        val userMessage = messages.lastOrNull()?.content ?: ""

        val fullPrompt = """
            $systemPrompt
            
            对话历史:
            $historyText
            
            用户: $userMessage
        """.trimIndent()

        // ✅ 防止并发请求
        if (!isBusy.compareAndSet(false, true)) {
            trySend("模型正忙，请稍后再试")
            close()
            return@callbackFlow
        }

        try {
            currentSession.addQueryChunk(fullPrompt)
            currentSession.generateResponseAsync { chunk, isDone ->
                trySend(chunk)
                if (isDone) {
                    isBusy.set(false)
                    close()
                }
            }
        } catch (e: Exception) {
            isBusy.set(false)
            if(e.message?.contains("too long")==true){
                reset()
                session = LlmInferenceSession.createFromOptions(llmInference!!, LlmInferenceSession.LlmInferenceSessionOptions.builder()
                    .setTemperature(0.7f) // 参考原项目，使用标准温度
                    .setTopK(40)
                    .build())
                trySend("[系统]检测到当前对话过长，已重置记忆窗口")
            }
            trySend("推理出错: ${e.message}")
            close()
        }

        awaitClose {
            isBusy.set(false)
        }

    }.flowOn(Dispatchers.IO)


    fun reset() {
        try {
            session?.close()
            //重新给与初始化权限，但是不重新走一遍init
            isSeeded = false
            session = null
        } catch (e: Exception) {
            Log.e("LocalLLM", "重置失败: ${e.message}")
        }
    }

}