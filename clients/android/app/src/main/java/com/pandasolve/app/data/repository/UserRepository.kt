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
    /** Last successfully-loaded profile, kept in memory so screens can show counts
     *  instantly on re-open instead of waiting for a fresh /v1/me. */
    @Volatile
    var lastMe: Me? = null
        private set

    suspend fun me(): Me = api.getMe().also { lastMe = it }

    suspend fun startLink(): String = api.startLink().code

    suspend fun updateLanguage(code: String): Me =
        api.updateMe(UpdateMeRequest(languageCode = code))

    suspend fun updateDisplayName(name: String): Me =
        api.updateMe(UpdateMeRequest(displayName = name))
}
