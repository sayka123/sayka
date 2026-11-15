package com.sayka.appletvlauncher

import android.os.Build
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.blur
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import kotlinx.coroutines.delay
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private val TileShape = RoundedCornerShape(14.dp)
private val TileGray = Color(0xFF2C2C2E)

/**
 * Apple TV style home: a "Top Shelf" area showing the focused app large and
 * blurred behind its name, then a 5-column grid of rounded 16:9 app tiles that
 * lift when focused and reveal their name below.
 */
@Composable
fun HomeScreen(apps: List<LauncherApp>?, onOpen: (LauncherApp) -> Unit) {
    var focused by remember { mutableStateOf<LauncherApp?>(null) }
    val firstTile = remember { FocusRequester() }

    Box(Modifier.fillMaxSize().background(Color.Black)) {
        TopShelf(app = focused ?: apps?.firstOrNull())
        Clock(Modifier.align(Alignment.TopEnd).padding(top = 32.dp, end = 56.dp))

        if (apps != null) {
            LazyVerticalGrid(
                columns = GridCells.Fixed(5),
                modifier = Modifier.fillMaxSize(),
                // Top padding leaves the upper half of the screen to the Top Shelf.
                contentPadding = PaddingValues(start = 56.dp, end = 56.dp, top = 300.dp, bottom = 48.dp),
                horizontalArrangement = Arrangement.spacedBy(32.dp),
                verticalArrangement = Arrangement.spacedBy(36.dp),
            ) {
                itemsIndexed(apps, key = { _, app -> app.packageName }) { index, app ->
                    AppTile(
                        app = app,
                        onFocus = { focused = app },
                        onClick = { onOpen(app) },
                        modifier = if (index == 0) Modifier.focusRequester(firstTile) else Modifier,
                    )
                }
            }
            LaunchedEffect(apps.isNotEmpty()) {
                if (apps.isNotEmpty()) runCatching { firstTile.requestFocus() }
            }
        }
    }
}

@Composable
private fun TopShelf(app: LauncherApp?) {
    Box(Modifier.fillMaxWidth().height(340.dp)) {
        AnimatedContent(
            targetState = app,
            transitionSpec = { fadeIn() togetherWith fadeOut() },
            label = "topShelf",
        ) { current ->
            Box(Modifier.fillMaxSize()) {
                val art = current?.banner ?: current?.icon
                if (art != null) {
                    // Blur needs Android 12+; older devices get a dimmed image instead.
                    val backdrop = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                        Modifier.fillMaxSize().blur(40.dp).alpha(0.7f)
                    } else {
                        Modifier.fillMaxSize().alpha(0.35f)
                    }
                    Image(art, contentDescription = null, contentScale = ContentScale.Crop, modifier = backdrop)
                }
                Box(
                    Modifier.fillMaxSize().background(
                        Brush.verticalGradient(0f to Color.Black.copy(alpha = 0.2f), 1f to Color.Black)
                    )
                )
                if (current != null) {
                    Text(
                        text = current.label,
                        style = TextStyle(color = Color.White, fontSize = 44.sp, fontWeight = FontWeight.Bold),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.align(Alignment.BottomStart).padding(start = 56.dp, bottom = 56.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun AppTile(app: LauncherApp, onFocus: () -> Unit, onClick: () -> Unit, modifier: Modifier = Modifier) {
    var isFocused by remember { mutableStateOf(false) }
    val labelAlpha by animateFloatAsState(if (isFocused) 1f else 0f, label = "label")

    Column(modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        Surface(
            onClick = onClick,
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(16f / 9f)
                .onFocusChanged {
                    isFocused = it.isFocused
                    if (it.isFocused) onFocus()
                },
            shape = ClickableSurfaceDefaults.shape(TileShape),
            scale = ClickableSurfaceDefaults.scale(focusedScale = 1.12f),
            colors = ClickableSurfaceDefaults.colors(containerColor = TileGray, focusedContainerColor = TileGray),
        ) {
            if (app.banner != null) {
                Image(app.banner, contentDescription = app.label, contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize())
            } else {
                Image(app.icon, contentDescription = app.label,
                    modifier = Modifier.align(Alignment.Center).size(64.dp))
            }
        }
        // Like tvOS, the name only appears under the focused tile.
        Text(
            text = app.label,
            style = TextStyle(color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Medium),
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier.padding(top = 14.dp).alpha(labelAlpha),
        )
    }
}

@Composable
private fun Clock(modifier: Modifier = Modifier) {
    val time by produceState(initialValue = now()) {
        while (true) {
            delay(1_000L * (60 - (System.currentTimeMillis() / 1000) % 60))
            value = now()
        }
    }
    Text(
        text = time,
        style = TextStyle(color = Color.White, fontSize = 26.sp, fontWeight = FontWeight.Medium),
        modifier = modifier,
    )
}

private fun now(): String = SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date())
