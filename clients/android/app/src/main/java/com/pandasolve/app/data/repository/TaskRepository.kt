package com.pandasolve.app.data.repository

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

    suspend fun list(limit: Int, before: String?): TaskList =
        api.listTasks(limit = limit, before = before)
}
