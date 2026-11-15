package com.sayka.appletvlauncher

import android.content.Context
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.drawable.Drawable
import android.util.DisplayMetrics
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.core.graphics.drawable.toBitmap
import androidx.core.graphics.scale
import java.util.concurrent.ConcurrentHashMap

/**
 * An installed TV app. [banner] is the app's 16:9 TV banner when it has one;
 * [backdrop] is a tiny copy of its art that, stretched full screen, reads as a soft blur.
 */
data class LauncherApp(
    val label: String,
    val packageName: String,
    val launchIntent: Intent,
    val banner: ImageBitmap?,
    val icon: ImageBitmap,
    val backdrop: ImageBitmap? = null,
)

object AppRepository {
    private class Art(val updatedAt: Long, val banner: ImageBitmap?, val icon: ImageBitmap, val backdrop: ImageBitmap)

    // Rendered at 2x the largest on-screen size (focused tile, Top Shelf icon) so art stays crisp on 1080p/4K.
    private const val BannerWidth = 640
    private const val BannerHeight = 360
    private const val IconSize = 512

    // Decoding banners is the slow part of a reload; reuse them until the app is updated.
    private val artCache = ConcurrentHashMap<String, Art>()

    fun load(context: Context): List<LauncherApp> {
        val pm = context.packageManager
        val query = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LEANBACK_LAUNCHER)
        val infos = pm.queryIntentActivities(query, 0)
            .filter { it.activityInfo.packageName != context.packageName }
            .distinctBy { it.activityInfo.packageName }
        artCache.keys.retainAll(infos.map { it.activityInfo.packageName }.toSet())

        return infos.map { info ->
            val activity = info.activityInfo
            val app = activity.applicationInfo
            val updatedAt = runCatching { pm.getPackageInfo(activity.packageName, 0).lastUpdateTime }.getOrDefault(0L)
            val art = artCache[activity.packageName]?.takeIf { it.updatedAt == updatedAt } ?: run {
                val bannerArt = hiRes(pm, app, activity.banner) ?: hiRes(pm, app, app.banner)
                    ?: activity.loadBanner(pm) ?: app.loadBanner(pm)
                val banner = bannerArt?.toBitmap(BannerWidth, BannerHeight)
                val icon = (hiRes(pm, app, info.iconResource) ?: info.loadIcon(pm)).toBitmap(IconSize, IconSize)
                Art(updatedAt, banner?.asImageBitmap(), icon.asImageBitmap(), backdropOf(banner ?: icon))
                    .also { artCache[activity.packageName] = it }
            }
            LauncherApp(
                label = info.loadLabel(pm).toString(),
                packageName = activity.packageName,
                launchIntent = Intent(Intent.ACTION_MAIN)
                    .addCategory(Intent.CATEGORY_LEANBACK_LAUNCHER)
                    .setClassName(activity.packageName, activity.name)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED),
                banner = art.banner,
                icon = art.icon,
                backdrop = art.backdrop,
            )
        }.sortedBy { it.label.lowercase() }.let { AppOrder.apply(context, it) }
    }

    /** Two filtered downscales give a smooth blur for free on every Android version. */
    fun backdropOf(source: Bitmap): ImageBitmap =
        source.scale(64, 36, filter = true).scale(24, 14, filter = true).asImageBitmap()

    /** Optional personal wallpaper bundled as assets/wallpaper.jpg (git-ignored, so public builds have none). */
    fun loadWallpaper(context: Context): ImageBitmap? = runCatching {
        context.assets.open("wallpaper.jpg").use { BitmapFactory.decodeStream(it) }?.asImageBitmap()
    }.getOrNull()

    /** The app's art from its highest-density resources, instead of the TV's (often lower) density bucket. */
    private fun hiRes(pm: PackageManager, app: ApplicationInfo, resId: Int): Drawable? =
        if (resId == 0) null else runCatching {
            pm.getResourcesForApplication(app).getDrawableForDensity(resId, DisplayMetrics.DENSITY_XXXHIGH, null)
        }.getOrNull()
}
