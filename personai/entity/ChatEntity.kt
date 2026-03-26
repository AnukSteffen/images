package com.wu.personai.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.wu.personai.data.ChatMessage

@Entity(tableName = "chat_messages")
data class ChatEntity (
    @PrimaryKey(autoGenerate = true)
    val id : Int = 0,
    val content : String,
    val isUser : Boolean,
    val timestamp : Long
)

fun ChatEntity.toChatMessage(): ChatMessage {
    return ChatMessage(
        content = this.content,
        isUser = this.isUser
    )
}