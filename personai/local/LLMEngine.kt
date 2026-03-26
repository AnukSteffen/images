package com.wu.personai.local

import com.wu.personai.data.ChatMessage
import kotlinx.coroutines.flow.Flow

interface LLMEngine {
    fun generateResponse(messages : List<ChatMessage>) : Flow<String>
}