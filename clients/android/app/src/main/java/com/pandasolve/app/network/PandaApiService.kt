package com.pandasolve.app.network

import com.pandasolve.app.domain.model.Album
import com.pandasolve.app.domain.model.AlbumCreateRequest
import com.pandasolve.app.domain.model.AlbumListResponse
import com.pandasolve.app.domain.model.AlbumUpdateRequest
import com.pandasolve.app.domain.model.AssignAlbumRequest
import com.pandasolve.app.domain.model.ChatSendRequest
import com.pandasolve.app.domain.model.ChatThread
import com.pandasolve.app.domain.model.LinkStartResponse
import com.pandasolve.app.domain.model.Me
import com.pandasolve.app.domain.model.RegisterDeviceRequest
import com.pandasolve.app.domain.model.RegisteredDevice
import com.pandasolve.app.domain.model.TaskCreateText
import com.pandasolve.app.domain.model.TaskDetail
import com.pandasolve.app.domain.model.TaskList
import com.pandasolve.app.domain.model.TaskRef
import com.pandasolve.app.domain.model.TaskUpdateRequest
import com.pandasolve.app.domain.model.TopupUrl
import com.pandasolve.app.domain.model.UpdateMeRequest
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * Retrofit interface mirroring the /v1 surface (see bot/openapi.json). Once the
 * OpenAPI codegen plugin runs (`./gradlew openApiGenerate`), this file is
 * replaced by the generated equivalent. Kept hand-rolled here so the app
 * compiles before codegen is configured.
 */
interface PandaApiService {

    @GET("/v1/me")
    suspend fun getMe(): Me

    @POST("/v1/me")
    suspend fun updateMe(@Body body: UpdateMeRequest): Me

    @POST("/v1/auth/link/start")
    suspend fun startLink(): LinkStartResponse

    @POST("/v1/devices")
    suspend fun registerDevice(@Body body: RegisterDeviceRequest): RegisteredDevice

    @DELETE("/v1/devices/{token}")
    suspend fun unregisterDevice(@Path("token") token: String)

    @Multipart
    @POST("/v1/tasks")
    suspend fun submitImage(
        @Part file: MultipartBody.Part,
        @Part("caption") caption: RequestBody? = null,
    ): TaskRef

    @POST("/v1/tasks/text")
    suspend fun submitText(@Body body: TaskCreateText): TaskRef

    @GET("/v1/tasks/{task_id}")
    suspend fun getTask(@Path("task_id") taskId: String): TaskDetail

    @PATCH("/v1/tasks/{task_id}")
    suspend fun updateTask(@Path("task_id") taskId: String, @Body body: TaskUpdateRequest): TaskDetail

    @GET("/v1/tasks/{task_id}/chat")
    suspend fun getChat(@Path("task_id") taskId: String): ChatThread

    @POST("/v1/tasks/{task_id}/chat")
    suspend fun postChat(@Path("task_id") taskId: String, @Body body: ChatSendRequest): ChatThread

    @GET("/v1/tasks")
    suspend fun listTasks(
        @Query("limit") limit: Int = 20,
        @Query("before") before: String? = null,
        @Query("album_id") albumId: String? = null,
        @Query("q") q: String? = null,
    ): TaskList

    @GET("/v1/topup/url")
    suspend fun topupUrl(): TopupUrl

    @GET("/v1/albums")
    suspend fun listAlbums(): AlbumListResponse

    @POST("/v1/albums")
    suspend fun createAlbum(@Body body: AlbumCreateRequest): Album

    @PATCH("/v1/albums/{id}")
    suspend fun updateAlbum(@Path("id") id: String, @Body body: AlbumUpdateRequest): Album

    @DELETE("/v1/albums/{id}")
    suspend fun deleteAlbum(@Path("id") id: String)

    @POST("/v1/tasks/{id}/album")
    suspend fun assignTaskAlbum(@Path("id") taskId: String, @Body body: AssignAlbumRequest)
}
