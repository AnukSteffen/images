package com.wu.personai.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import com.wu.personai.entity.ChatEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ChatDao {

    @Query("SELECT * FROM chat_messages ORDER BY timestamp ASC")
    fun getAllMessages() : Flow<List<ChatEntity>>

    @Insert
    suspend fun insertMessage(message:ChatEntity)

    @Query("DELETE FROM chat_messages")
    suspend fun clearHistory()

    // 根据传入的数量拿最新的消息
    @Query("SELECT * FROM chat_messages ORDER BY timestamp DESC LIMIT :limit")
    fun getMessages(limit: Int): Flow<List<ChatEntity>>

}