package com.sayka.appletvlauncher

import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Shader
import androidx.activity.ComponentActivity
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.isFocused
import androidx.compose.ui.test.requestFocus
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
import java.io.File
import java.util.Locale

/** Renders the home screen at TV size (1920x1080) and saves build/screenshots/home.png. */
@RunWith(RobolectricTestRunner::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = [34], qualifiers = "w960dp-h540dp-land-xhdpi")
class HomeScreenScreenshotTest {
    @get:Rule
    val compose = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun homeScreen() {
        val apps = listOf(
            "YouTube" to 0xFFE53935, "Netflix" to 0xFFB71C1C, "Prime Video" to 0xFF1E88E5,
            "Disney+" to 0xFF283593, "Spotify" to 0xFF1DB954, "Plex" to 0xFFF9A825,
            "Kodi" to 0xFF0277BD, "Ayarlar" to 0xFF546E7A, "TRT İzle" to 0xFFD32F2F, "BluTV" to 0xFF00ACC1,
        ).map { (name, color) -> fakeApp(name, color.toInt()) }

        Locale.setDefault(Locale("tr", "TR"))
        compose.setContent { HomeScreen(apps = apps, onOpen = {}) }
        compose.waitForIdle()
        // Robolectric windows never gain input focus on their own, so focus the first tile explicitly.
        compose.onAllNodes(hasClickAction())[0].requestFocus()
        compose.mainClock.advanceTimeBy(2_000) // let focus and crossfade animations settle
        compose.onAllNodes(isFocused()).assertCountEquals(1)
        // Top Shelf title plus the label under the focused first tile.
        compose.onAllNodesWithText("YouTube").assertCountEquals(2)

        val out = File("build/screenshots/home.png").apply { parentFile?.mkdirs() }
        // Software-draw the window; Compose's captureToImage never gets a frame under Robolectric.
        val root = compose.activity.window.decorView
        val shot = Bitmap.createBitmap(root.width, root.height, Bitmap.Config.ARGB_8888)
        compose.runOnUiThread { root.draw(Canvas(shot)) }
        out.outputStream().use { shot.compress(Bitmap.CompressFormat.PNG, 100, it) }
    }

    private fun fakeApp(name: String, color: Int): LauncherApp {
        val banner = Bitmap.createBitmap(480, 270, Bitmap.Config.ARGB_8888)
        Canvas(banner).apply {
            drawPaint(Paint().apply {
                shader = LinearGradient(0f, 0f, 480f, 270f, color, 0xFF111111.toInt(), Shader.TileMode.CLAMP)
            })
            drawText(name, 240f, 150f, Paint().apply {
                this.color = 0xFFFFFFFF.toInt(); textSize = 52f; isFakeBoldText = true
                textAlign = Paint.Align.CENTER; isAntiAlias = true
            })
        }
        val image = banner.asImageBitmap()
        return LauncherApp(name, "pkg.$name", Intent(), image, image)
    }
}
