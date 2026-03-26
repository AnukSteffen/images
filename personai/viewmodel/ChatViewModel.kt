package com.wu.personai.viewmodel

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.wu.personai.data.ChatMessage
import com.wu.personai.entity.ChatEntity
import com.wu.personai.entity.toChatMessage
import com.wu.personai.repository.ChatRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val repository: ChatRepository
) : ViewModel() {

    private val loadLimit = MutableStateFlow(50)

    //维护完整的消息列表
    val allMessages: StateFlow<List<ChatEntity>> = loadLimit
        .flatMapLatest { limit ->
            // 每次 limit 改变，Room 都会重新推数据
            repository.getMessages(limit)
        }
        .map { it.reversed() } // 让新消息在下面
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )


    //加载更对历史消息记录
    fun loadMoreHistory() {
        loadLimit.value += 50 // 只要增加这个值，allMessages 就会自动刷新
    }


    var isOffline by mutableStateOf(false)
        private set

    //1.正在输入的临时文本
    var currentTypingText by mutableStateOf("")
        private set


    fun toggleOffline(offline: Boolean) {
        isOffline = offline
    }

    fun sendMessage(text: String) {
        if(text.isBlank()) return

        viewModelScope.launch {
            //2.先存用户消息（UI 会自动刷新）
            repository.saveMessage(text,true)//用户消息

            currentTypingText = ""
            val history = allMessages.value.takeLast(6).map { it.toChatMessage() }//只取数据库中最近的 6 条消息

            repository.getResponse(history,isOffline).collect{ chunk ->
                currentTypingText += chunk
            }
            repository.saveMessage(currentTypingText,false)
            currentTypingText=""
        }
    }

    fun clearHistory() {
        viewModelScope.launch {
            repository.clearAll()
        }
    }
}