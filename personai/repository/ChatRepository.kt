package com.wu.personai.repository

import android.content.Context
import com.wu.personai.dao.ChatDao
import com.wu.personai.data.ChatMessage
import com.wu.personai.entity.ChatEntity
import com.wu.personai.net.CloudEngine
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ChatRepository @Inject constructor (
    @ApplicationContext private val context: Context,
    private val chatDao : ChatDao
){
    private val cloudEngine = CloudEngine()
    private val localEngine = LocalLLMEngine(context)

    fun getAllMessages() = chatDao.getAllMessages()
    suspend fun saveMessage(content : String,isUser :Boolean){
        chatDao.insertMessage(
            ChatEntity(content = content, isUser = isUser, timestamp = System.currentTimeMillis())
        )
    }
    suspend fun clearAll() = chatDao.clearHistory()

    fun getResponse(messages: List<ChatMessage>, forceOffline:Boolean): Flow<String> {
        return if (forceOffline) localEngine.generateResponse(messages) else cloudEngine.generateResponse(messages)
    }

    suspend fun getMessages(limit:Int) : Flow<List<ChatEntity>> = chatDao.getMessages(limit)
}