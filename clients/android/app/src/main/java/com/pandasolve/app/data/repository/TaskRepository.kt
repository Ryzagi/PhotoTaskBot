package com.pandasolve.app.data.repository

import com.pandasolve.app.domain.model.ChatMessage
import com.pandasolve.app.domain.model.ChatSendRequest
import com.pandasolve.app.domain.model.TaskCreateText
import com.pandasolve.app.domain.model.TaskDetail
import com.pandasolve.app.domain.model.TaskList
import com.pandasolve.app.network.PandaApiService
import javax.inject.Inject
import javax.inject.Singleton
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody

@Singleton
class TaskRepository @Inject constructor(
    private val api: PandaApiService,
) {
    suspend fun submitImage(bytes: ByteArray, caption: String?): String {
        val filePart = MultipartBody.Part.createFormData(
            name = "file",
            filename = "task.jpg",
            body = bytes.toRequestBody("image/jpeg".toMediaTypeOrNull()),
        )
        val captionPart = caption?.toRequestBody("text/plain".toMediaTypeOrNull())
        return api.submitImage(filePart, captionPart).taskId
    }

    suspend fun submitText(text: String): String =
        api.submitText(TaskCreateText(text = text)).taskId

    suspend fun get(id: String): TaskDetail = api.getTask(id)

    suspend fun chatHistory(taskId: String): List<ChatMessage> = api.getChat(taskId).messages

    suspend fun sendChat(taskId: String, message: String): List<ChatMessage> =
        api.postChat(taskId, ChatSendRequest(message)).messages

    suspend fun list(limit: Int, before: String?, albumId: String? = null, q: String? = null): TaskList =
        api.listTasks(limit = limit, before = before, albumId = albumId, q = q?.ifBlank { null })
}
