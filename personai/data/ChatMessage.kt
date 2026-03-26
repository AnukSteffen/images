package com.wu.personai.data

data class ChatMessage(
    val content : String,
    val isUser : Boolean,
    val timestamp : Long = System.currentTimeMillis()
)