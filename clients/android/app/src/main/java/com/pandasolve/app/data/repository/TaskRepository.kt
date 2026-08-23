package com.pandasolve.app.data.repository

import com.pandasolve.app.domain.model.ChatSendRequest
import com.pandasolve.app.domain.model.ChatThread
import com.pandasolve.app.domain.model.TaskCreateText
import com.pandasolve.app.domain.model.TaskDetail
import com.pandasolve.app.domain.model.TaskList
import com.pandasolve.app.domain.model.TaskUpdateRequest
import com.pandasolve.app.network.PandaApiService
import java.util.concurrent.ConcurrentHashMap
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

    // Cache loaded tasks so re-opening one paints instantly while it refreshes.
    private val taskCache = ConcurrentHashMap<String, TaskDetail>()
    fun cachedTask(id: String): TaskDetail? = taskCache[id]

    suspend fun get(id: String): TaskDetail = api.getTask(id).also { taskCache[id] = it }

    suspend fun rename(id: String, title: String): TaskDetail =
        api.updateTask(id, TaskUpdateRequest(title = title)).also { taskCache[id] = it }

    suspend fun chatHistory(taskId: String): ChatThread = api.getChat(taskId)

    suspend fun sendChatImage(taskId: String, bytes: ByteArray, caption: String): ChatThread {
        val filePart = MultipartBody.Part.createFormData(
            name = "file", filename = "chat.jpg",
            body = bytes.toRequestBody("image/jpeg".toMediaTypeOrNull()),
        )
        val msgPart = caption.toRequestBody("text/plain".toMediaTypeOrNull())
        return api.postChatImage(taskId, filePart, msgPart)
    }

    suspend fun sendChat(taskId: String, message: String): ChatThread =
        api.postChat(taskId, ChatSendRequest(message))

    suspend fun list(limit: Int, before: String?, albumId: String? = null, q: String? = null): TaskList =
        api.listTasks(limit = limit, before = before, albumId = albumId, q = q?.ifBlank { null })
}
