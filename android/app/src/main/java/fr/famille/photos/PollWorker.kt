package fr.famille.photos

import android.content.Context
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.TimeUnit

/**
 * Contrôle périodique du serveur (toutes les 30 minutes environ, quand le téléphone a du réseau) :
 *  - nouvelles photos      -> au plus UNE notification par heure ;
 *  - message de l'administrateur -> une notification par nouveau message ;
 *  - nouvelle version de l'APK   -> une notification par version.
 */
class PollWorker(private val ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        val code = Prefs.code(ctx)
        val api = Prefs.api(ctx)
        if (code.isNullOrBlank() || api.isNullOrBlank()) return@withContext Result.success()
        try {
            val body = JSONObject()
                .put("fn", "updates")
                .put("args", JSONArray().put(code).put(Prefs.since(ctx)))
                .toString()
            val json = JSONObject(postJson(api, body))
            if (!json.optBoolean("ok")) return@withContext Result.success()   // lien désactivé, erreur serveur… on réessaiera
            handle(json.getJSONObject("data"))
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }

    private fun handle(d: JSONObject) {
        val now = d.getString("now")
        val msg = d.optJSONObject("message")
        val app = d.optJSONObject("app")

        // Premier contrôle : on fixe le point de départ sans rien notifier (pas de rafale d'anciennes nouvelles).
        if (Prefs.since(ctx).isEmpty()) {
            Prefs.setSince(ctx, now)
            Prefs.setLastMsg(ctx, msg?.optString("id") ?: "")
            Prefs.setLastApp(ctx, maxOf(BuildConfig.VERSION_CODE, app?.optInt("versionCode") ?: 0))
            return
        }

        // 1) Nouvelles photos : au plus une notification par heure. Si on est dans l'heure, on ne bouge pas
        //    le point de départ : ces photos seront comptées à la notification suivante.
        val newPhotos = d.optInt("newPhotos", 0)
        if (newPhotos > 0) {
            val nowMs = System.currentTimeMillis()
            if (nowMs - Prefs.lastPhotoNotif(ctx) >= TimeUnit.HOURS.toMillis(1)) {
                val text = if (newPhotos == 1) "Une nouvelle photo a été ajoutée." else "$newPhotos nouvelles photos ont été ajoutées."
                Notifier.show(ctx, Notifier.CH_PHOTOS, Notifier.ID_PHOTOS, "Photos de famille", text)
                Prefs.setLastPhotoNotif(ctx, nowMs)
                Prefs.setSince(ctx, now)
            }
        } else {
            Prefs.setSince(ctx, now)
        }

        // 2) Message de l'administrateur
        if (msg != null) {
            val id = msg.optString("id")
            if (id.isNotEmpty() && id != Prefs.lastMsg(ctx)) {
                Notifier.show(ctx, Notifier.CH_MESSAGES, Notifier.ID_MESSAGE, "Message de Mathieu", msg.optString("texte").take(400))
                Prefs.setLastMsg(ctx, id)
            }
        }

        // 3) Nouvelle version de l'application
        if (app != null) {
            val v = app.optInt("versionCode", 0)
            if (v > BuildConfig.VERSION_CODE && v > Prefs.lastApp(ctx)) {
                val notes = app.optString("notes")
                val text = if (notes.isNotBlank()) "Une nouvelle version est disponible : $notes" else "Une nouvelle version de l'application est disponible. Touchez pour la télécharger."
                Notifier.show(ctx, Notifier.CH_UPDATES, Notifier.ID_UPDATE, "Mise à jour disponible", text, app.optString("url"))
                Prefs.setLastApp(ctx, v)
            }
        }
    }

    /** POST en texte brut. Apps Script répond par une redirection (302) vers l'adresse du résultat, à lire en GET. */
    private fun postJson(url: String, body: String): String {
        var c = URL(url).openConnection() as HttpURLConnection
        c.instanceFollowRedirects = false
        c.requestMethod = "POST"
        c.doOutput = true
        c.connectTimeout = 20000
        c.readTimeout = 40000
        c.setRequestProperty("Content-Type", "text/plain;charset=utf-8")
        c.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
        val status = c.responseCode
        if (status in 300..399) {
            val loc = c.getHeaderField("Location") ?: throw IllegalStateException("Redirection sans destination")
            c.disconnect()
            c = URL(loc).openConnection() as HttpURLConnection
            c.connectTimeout = 20000
            c.readTimeout = 40000
        }
        return c.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }.also { c.disconnect() }
    }

    companion object {
        fun schedule(ctx: Context) {
            val constraints = Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()
            val request = PeriodicWorkRequestBuilder<PollWorker>(30, TimeUnit.MINUTES).setConstraints(constraints).build()
            WorkManager.getInstance(ctx).enqueueUniquePeriodicWork("pf-poll", ExistingPeriodicWorkPolicy.KEEP, request)
        }
    }
}
