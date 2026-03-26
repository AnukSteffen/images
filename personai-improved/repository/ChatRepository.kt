import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.flow

class ChatRepository(private val cloudEngine: CloudEngine, private val localLLMEngine: LocalLLMEngine) {

    fun sendMessage(message: String): Flow<Response> {
        return flow {
            val cloudResponse = cloudEngine.sendMessage(message)
            emit(cloudResponse)
        }.catch { e ->
            emit(localLLMEngine.sendMessage(message)) // Fallback to LocalLLMEngine
        }
    }
}