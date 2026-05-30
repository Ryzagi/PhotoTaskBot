package com.pandasolve.app.data.repository

import com.pandasolve.app.domain.model.Album
import com.pandasolve.app.domain.model.AlbumCreateRequest
import com.pandasolve.app.domain.model.AssignAlbumRequest
import com.pandasolve.app.network.PandaApiService
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AlbumRepository @Inject constructor(
    private val api: PandaApiService,
) {
    suspend fun list(): List<Album> = api.listAlbums().items

    suspend fun create(name: String, emoji: String?, color: String?): Album =
        api.createAlbum(AlbumCreateRequest(name = name, emoji = emoji, color = color))

    suspend fun delete(id: String) = api.deleteAlbum(id)

    suspend fun assign(taskId: String, albumId: String?) =
        api.assignTaskAlbum(taskId, AssignAlbumRequest(albumId = albumId))
}
