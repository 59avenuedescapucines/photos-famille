package fr.famille.photos

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat

object Notifier {
    const val CH_PHOTOS = "photos"
    const val CH_MESSAGES = "messages"
    const val CH_UPDATES = "updates"

    const val ID_PHOTOS = 1
    const val ID_MESSAGE = 2
    const val ID_UPDATE = 3

    /** Trois canaux distincts : chacun peut les couper séparément dans les réglages du téléphone. */
    fun ensureChannels(ctx: Context) {
        if (Build.VERSION.SDK_INT < 26) return
        val nm = ctx.getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(NotificationChannel(CH_PHOTOS, ctx.getString(R.string.ch_photos), NotificationManager.IMPORTANCE_DEFAULT))
        nm.createNotificationChannel(NotificationChannel(CH_MESSAGES, ctx.getString(R.string.ch_messages), NotificationManager.IMPORTANCE_HIGH))
        nm.createNotificationChannel(NotificationChannel(CH_UPDATES, ctx.getString(R.string.ch_updates), NotificationManager.IMPORTANCE_DEFAULT))
    }

    /** openUrl : si renseigné, un appui ouvre ce lien (téléchargement de l'APK) ; sinon l'application s'ouvre. */
    fun show(ctx: Context, channel: String, id: Int, title: String, text: String, openUrl: String? = null) {
        if (!NotificationManagerCompat.from(ctx).areNotificationsEnabled()) return
        ensureChannels(ctx)
        val intent = if (!openUrl.isNullOrBlank()) Intent(Intent.ACTION_VIEW, Uri.parse(openUrl))
        else Intent(ctx, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)
        val pi = PendingIntent.getActivity(ctx, id, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val n = NotificationCompat.Builder(ctx, channel)
            .setSmallIcon(R.drawable.ic_stat)
            .setContentTitle(title)
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setContentIntent(pi)
            .setAutoCancel(true)
            .build()
        try { NotificationManagerCompat.from(ctx).notify(id, n) } catch (e: SecurityException) { /* permission refusée */ }
    }
}
