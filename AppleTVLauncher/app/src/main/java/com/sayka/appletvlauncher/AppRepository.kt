package com.sayka.appletvlauncher

import android.content.Context
import android.content.Intent
import android.graphics.drawable.Drawable
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.core.graphics.drawable.toBitmap

/** An installed TV app. [banner] is the app's 16:9 TV banner when it has one. */
data class LauncherApp(
    val label: String,
    val packageName: String,
    val launchIntent: Intent,
    val banner: ImageBitmap?,
    val icon: ImageBitmap,
)

object AppRepository {
    fun load(context: Context): List<LauncherApp> {
        val pm = context.packageManager
        val query = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LEANBACK_LAUNCHER)
        return pm.queryIntentActivities(query, 0)
            .filter { it.activityInfo.packageName != context.packageName }
            .distinctBy { it.activityInfo.packageName }
            .map { info ->
                val activity = info.activityInfo
                val banner = activity.loadBanner(pm) ?: activity.applicationInfo.loadBanner(pm)
                LauncherApp(
                    label = info.loadLabel(pm).toString(),
                    packageName = activity.packageName,
                    launchIntent = Intent(Intent.ACTION_MAIN)
                        .addCategory(Intent.CATEGORY_LEANBACK_LAUNCHER)
                        .setClassName(activity.packageName, activity.name)
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED),
                    banner = banner?.toImage(480, 270),
                    icon = info.loadIcon(pm).toImage(192, 192),
                )
            }
            .sortedBy { it.label.lowercase() }
    }

    private fun Drawable.toImage(fallbackWidth: Int, fallbackHeight: Int): ImageBitmap {
        val w = intrinsicWidth.takeIf { it > 0 } ?: fallbackWidth
        val h = intrinsicHeight.takeIf { it > 0 } ?: fallbackHeight
        return toBitmap(w, h).asImageBitmap()
    }
}
