// Improved ChatScreen.kt

import androidx.compose.foundation.layout.*;
import androidx.compose.material.*;
import androidx.compose.runtime.*;
import androidx.compose.ui.Modifier;
import androidx.compose.ui.unit.dp;
import androidx.compose.ui.unit.sp;
import androidx.compose.ui.tooling.preview.Preview;
import androidx.compose.ui.text.input.TextFieldValue;

@Composable
fun ChatScreen() {
    var message by remember { mutableStateOf(TextFieldValue("")) }
    var isLoading by remember { mutableStateOf(false) }
    var isButtonEnabled by remember { mutableStateOf(true) }
    
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        if (isLoading) {
            CircularProgressIndicator(modifier = Modifier.padding(bottom = 16.dp))
        }
        Text(
            text = "Chat",
            fontSize = 24.sp,
            modifier = Modifier.padding(bottom = 16.dp)
        )
        TextField(
            value = message,
            onValueChange = { message = it },
            placeholder = { Text("Type your message...") },
            enabled = isButtonEnabled
        )
        Button(
            onClick = { /* send message logic */ },
            enabled = isButtonEnabled,
            modifier = Modifier.padding(top = 16.dp)
        ) {
            Text("Send")
        }
    }
}

@Preview(showBackground = true)
@Composable
fun PreviewChatScreen() {
    ChatScreen()
}