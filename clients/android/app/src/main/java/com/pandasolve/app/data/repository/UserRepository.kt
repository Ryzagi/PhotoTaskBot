package com.pandasolve.app.data.repository

import com.pandasolve.app.domain.model.Me
import com.pandasolve.app.domain.model.UpdateMeRequest
import com.pandasolve.app.network.PandaApiService
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class UserRepository @Inject constructor(
    private val api: PandaApiService,
) {
    suspend fun me(): Me = api.getMe()

    suspend fun startLink(): String = api.startLink().code

    suspend fun updateLanguage(code: String): Me =
        api.updateMe(UpdateMeRequest(languageCode = code))
}
