package com.sayka.appletvlauncher

import android.app.ActivityOptions
import android.app.SearchManager
import android.content.Intent
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import androidx.activity.ComponentActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LifecycleEventEffect
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.Locale

private const val WELCOME_TEXT = "Molla ailesi hoş geldiniz"

class MainActivity : ComponentActivity() {
    private var tts: TextToSpeech? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (savedInstanceState == null) speakWelcome()
        ensureMicAndStartVoice()
        setContent {
            val context = LocalContext.current
            var apps by remember { mutableStateOf<List<LauncherApp>?>(null) }
            var reloads by remember { mutableIntStateOf(0) }
            val wallpaper by produceState<ImageBitmap?>(null) {
                value = withContext(Dispatchers.IO) { AppRepository.loadWallpaper(context) }
            }

            // Reload on every return to home so installed/removed apps show up (art is cached).
            LifecycleEventEffect(Lifecycle.Event.ON_RESUME) { reloads++ }
            LaunchedEffect(reloads) {
                apps = withContext(Dispatchers.IO) { AppRepository.load(context) }
            }
            // As a home screen, Back has nowhere to go.
            BackHandler {}

            HomeScreen(
                apps = apps,
                onOpen = { app -> launch(app.launchIntent) },
                wallpaper = wallpaper,
                onAssistant = ::openAssistant,
                onReorder = { packages ->
                    AppOrder.save(context, packages)
                    val rank = packages.withIndex().associate { it.value to it.index }
                    apps = apps?.sortedBy { rank[it.packageName] ?: Int.MAX_VALUE }
                },
            )
        }
    }

    private fun ensureMicAndStartVoice() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            == PackageManager.PERMISSION_GRANTED
        ) {
            VoiceCommandsService.start(this)
        } else {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.RECORD_AUDIO), REQ_MIC)
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQ_MIC && grantResults.firstOrNull() == PackageManager.PERMISSION_GRANTED) {
            VoiceCommandsService.start(this)
        }
    }

    companion object {
        private const val REQ_MIC = 7
    }

    override fun onDestroy() {
        tts?.shutdown()
        tts = null
        super.onDestroy()
    }

    /** Speaks the family greeting once per launch; silently skipped if no Turkish voice is installed. */
    private fun speakWelcome() {
        tts = TextToSpeech(this) { status ->
            val engine = tts ?: return@TextToSpeech
            if (status == TextToSpeech.SUCCESS) {
                val result = engine.setLanguage(Locale("tr", "TR"))
                if (result != TextToSpeech.LANG_MISSING_DATA && result != TextToSpeech.LANG_NOT_SUPPORTED) {
                    engine.speak(WELCOME_TEXT, TextToSpeech.QUEUE_FLUSH, null, "welcome")
                }
            }
        }
    }

    // No window transition: the app appears the moment its first frame is ready.
    private fun launch(intent: Intent): Boolean = runCatching {
        startActivity(intent, ActivityOptions.makeCustomAnimation(this, 0, 0).toBundle())
    }.isSuccess

    /** Gemini / Google Assistant on Google TV, falling back to voice and then text search on other boxes. */
    private fun openAssistant() {
        listOf(
            Intent(Intent.ACTION_ASSIST),
            Intent(Intent.ACTION_VOICE_COMMAND),
            Intent(SearchManager.INTENT_ACTION_GLOBAL_SEARCH),
            Intent(Intent.ACTION_WEB_SEARCH),
        ).firstOrNull { launch(it.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
    }
}
