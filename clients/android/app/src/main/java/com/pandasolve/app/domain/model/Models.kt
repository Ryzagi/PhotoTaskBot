package com.pandasolve.app.domain.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Balance(val daily: Int, val subscription: Int)

@Serializable
data class Me(
    val id: String,
    @SerialName("telegram_linked") val telegramLinked: Boolean,
    @SerialName("language_code") val languageCode: String,
    val balance: Balance,
    @SerialName("created_at") val createdAt: String,
    @SerialName("solved_count") val solvedCount: Int = 0,
    val streak: Int = 0,
)

@Serializable
data class UpdateMeRequest(
    @SerialName("language_code") val languageCode: String? = null,
)

@Serializable
data class LinkStartResponse(
    val code: String,
    @SerialName("expires_at") val expiresAt: String,
)

@Serializable
data class RegisterDeviceRequest(
    val platform: String,                       // "android"
    val token: String,
    @SerialName("app_version") val appVersion: String? = null,
    val locale: String? = null,
)

@Serializable
data class RegisteredDevice(val id: String)

@Serializable
data class Album(
    val id: String,
    val name: String,
    val emoji: String? = null,
    val color: String? = null,
    @SerialName("task_count") val taskCount: Int = 0,
    @SerialName("updated_at") val updatedAt: String,
)

@Serializable
data class AlbumListResponse(val items: List<Album>)

@Serializable
data class AlbumCreateRequest(val name: String, val emoji: String? = null, val color: String? = null)

@Serializable
data class AlbumUpdateRequest(val name: String? = null, val emoji: String? = null, val color: String? = null)

@Serializable
data class AssignAlbumRequest(@SerialName("album_id") val albumId: String? = null)

@Serializable
data class SolutionBlock(val type: String, val content: String)

@Serializable
data class ProblemDto(
    val problem: String,
    val steps: List<SolutionBlock>,
    val solution: List<SolutionBlock>,
)

@Serializable
data class Solution(val solutions: List<ProblemDto>)

@Serializable
data class TaskCreateText(val text: String)

@Serializable
data class TaskRef(
    @SerialName("task_id") val taskId: String,
    val status: String,
)

@Serializable
data class TaskDetail(
    val id: String,
    val status: String,
    @SerialName("input_kind") val inputKind: String,
    @SerialName("input_text") val inputText: String? = null,
    val solution: Solution? = null,
    @SerialName("album_id") val albumId: String? = null,
    @SerialName("error_code") val errorCode: String? = null,
    @SerialName("thumbnail_url") val thumbnailUrl: String? = null,
    @SerialName("image_url") val imageUrl: String? = null,
    @SerialName("model_used") val modelUsed: String? = null,
    @SerialName("created_at") val createdAt: String,
    @SerialName("completed_at") val completedAt: String? = null,
)

@Serializable
data class TaskListItem(
    val id: String,
    val status: String,
    @SerialName("input_kind") val inputKind: String,
    val preview: String,
    @SerialName("thumbnail_url") val thumbnailUrl: String? = null,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class TaskList(
    val items: List<TaskListItem>,
    @SerialName("next_before") val nextBefore: String? = null,
)

@Serializable
data class TopupUrl(val url: String)

@Serializable
data class ChatMessage(
    val role: String,                               // "user" | "assistant"
    val content: String,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class ChatThread(val messages: List<ChatMessage>)

@Serializable
data class ChatSendRequest(val message: String)
