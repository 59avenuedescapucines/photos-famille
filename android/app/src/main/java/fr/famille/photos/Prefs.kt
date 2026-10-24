package fr.famille.photos

import android.content.Context

/** Mémoire locale de l'application (lien personnel, dernier contrôle, dernières notifications). */
object Prefs {
    private fun sp(ctx: Context) = ctx.getSharedPreferences("pf", Context.MODE_PRIVATE)

    fun saveCredentials(ctx: Context, code: String, api: String) {
        sp(ctx).edit().putString("code", code).putString("api", api).apply()
    }
    fun code(ctx: Context): String? = sp(ctx).getString("code", null)
    fun api(ctx: Context): String? = sp(ctx).getString("api", null)

    /** Date (ISO) du dernier contrôle des nouvelles photos ; vide tant que le premier contrôle n'a pas eu lieu. */
    fun since(ctx: Context): String = sp(ctx).getString("since", "") ?: ""
    fun setSince(ctx: Context, v: String) = sp(ctx).edit().putString("since", v).apply()

    fun lastMsg(ctx: Context): String = sp(ctx).getString("lastMsg", "") ?: ""
    fun setLastMsg(ctx: Context, v: String) = sp(ctx).edit().putString("lastMsg", v).apply()

    fun lastPhotoNotif(ctx: Context): Long = sp(ctx).getLong("lastPhotoNotif", 0L)
    fun setLastPhotoNotif(ctx: Context, v: Long) = sp(ctx).edit().putLong("lastPhotoNotif", v).apply()

    fun lastApp(ctx: Context): Int = sp(ctx).getInt("lastApp", 0)
    fun setLastApp(ctx: Context, v: Int) = sp(ctx).edit().putInt("lastApp", v).apply()
}
