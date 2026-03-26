package com.wu.personai

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.wu.personai.data.ChatMessage
import com.wu.personai.entity.toChatMessage
import com.wu.personai.repository.ChatRepository
import com.wu.personai.viewmodel.ChatViewModel
import kotlinx.coroutines.launch
import com.halilibo.richtext.markdown.Markdown
import com.halilibo.richtext.ui.material3.Material3RichText
import com.halilibo.richtext.ui.RichTextScope

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(viewModel: ChatViewModel){

    var inputText by remember { mutableStateOf("") }
    val listState = rememberLazyListState()

    val scope = rememberCoroutineScope()
    val messages by viewModel.allMessages.collectAsState()

    val shouldLoadMore = remember{ //定义一个动作状态
        derivedStateOf{
            listState.firstVisibleItemIndex == 0 && listState.isScrollInProgress // 第0项可见 且 正在滚动
        }
    }
    LaunchedEffect (shouldLoadMore.value){
        if(shouldLoadMore.value){//到顶
            viewModel.loadMoreHistory()//加载更多
        }
    }

    LaunchedEffect(messages.size) { //监测message.size是否变化，变则执行
        if(messages.isNotEmpty()){
            listState.animateScrollToItem(messages.size-1) //记录滚动
        }
    }
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(if (viewModel.isOffline) "离线模式 (Gemma)" else "在线模式 (豆包)") },
                actions = {
                    Switch(
                        checked = viewModel.isOffline,
                        onCheckedChange = { viewModel.toggleOffline(it) }
                    )
                }
            )
        }
    ) {padding ->
        Column (modifier = Modifier
            .fillMaxSize()
            .imePadding() // 1. 让整个布局避开键盘
            .padding(padding)) {
            //1.消息展示区
            LazyColumn (state = listState, modifier = Modifier
                .weight(1f) // 2. 它在键盘弹起时自动收缩高度
                .fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(messages) { msg ->
                    ChatBubble(msg.toChatMessage())
                }
                //如果正在打字，显示实时变化的气泡
                if(viewModel.currentTypingText.isNotEmpty()){
                    item{
                        ChatBubble(ChatMessage(viewModel.currentTypingText,false))
                    }
                }
            }
            //2.输入区
            Row(modifier = Modifier
                .fillMaxWidth()
                .padding(top = 8.dp)){
                TextField(value = inputText, onValueChange = { inputText = it }, modifier = Modifier.weight(1f), placeholder = { Text("请输入消息...") })
                Button(
                    onClick = {
                        if(inputText.isNotBlank()) {
                            viewModel.sendMessage(inputText)
                            inputText = ""
                        }
                    },
                    modifier = Modifier.padding(start = 8.dp)
                ){
                    Text("发送")
                }
            }
        }
    }

}

@Composable
fun ChatBubble(message: ChatMessage){
    val alignment = if (message.isUser)  Alignment.End  else  Alignment.Start
    val color = if(message.isUser) Color(0xFFD1E7FF) else Color(0xFFF0F0F0)

    Column(modifier = Modifier.fillMaxWidth(), horizontalAlignment = alignment){
        Surface(
            color = color,
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
        ){
            if(!message.isUser){
                Material3RichText(modifier = Modifier.padding(12.dp)){
                    Markdown(content = message.content,)
                }
            }
            else {
                Text(text = message.content, modifier = Modifier.padding(12.dp), style = MaterialTheme.typography.bodyLarge)
            }
        }
    }
}