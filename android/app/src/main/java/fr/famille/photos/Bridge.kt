package fr.famille.photos

import android.content.Context
import android.webkit.JavascriptInterface

/** Pont appelé par le site (window.PFApp) : il transmet le lien personnel pour que les notifications fonctionnent. */
class Bridge(private val ctx: Context) {
    @JavascriptInterface
    fun saveCredentials(code: String, apiUrl: String) {
        if (code.isBlank() || !apiUrl.startsWith("https://")) return
        Prefs.saveCredentials(ctx, code, apiUrl)
        PollWorker.schedule(ctx)
    }

    @JavascriptInterface
    fun versionCode(): Int = BuildConfig.VERSION_CODE
}
