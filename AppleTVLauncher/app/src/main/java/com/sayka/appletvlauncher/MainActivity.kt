package com.sayka.appletvlauncher

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LifecycleEventEffect
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableIntStateOf

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            val context = LocalContext.current
            var apps by remember { mutableStateOf<List<LauncherApp>?>(null) }
            var reloads by remember { mutableIntStateOf(0) }

            // Reload on every return to home so installed/removed apps show up.
            LifecycleEventEffect(Lifecycle.Event.ON_RESUME) { reloads++ }
            LaunchedEffect(reloads) {
                apps = withContext(Dispatchers.IO) { AppRepository.load(context) }
            }
            // As a home screen, Back has nowhere to go.
            BackHandler {}

            HomeScreen(apps = apps, onOpen = { app -> runCatching { startActivity(app.launchIntent) } })
        }
    }
}
