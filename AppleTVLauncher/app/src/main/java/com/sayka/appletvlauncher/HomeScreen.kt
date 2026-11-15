package com.sayka.appletvlauncher

import android.os.Build
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.tv.material3.Border
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Glow
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import kotlinx.coroutines.delay
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private val TileShape = RoundedCornerShape(16.dp)
private val TileGray = Color(0xFF1C1C1E)
private val Secondary = Color.White.copy(alpha = 0.6f)
private val EdgeInset = 64.dp

/**
 * Apple TV style home: a cinematic Top Shelf for the focused app (slow
 * Ken Burns backdrop, ambient color washing the whole screen), then a grid of
 * rounded 16:9 tiles that lift, glow and catch a glass highlight on focus.
 */
@Composable
fun HomeScreen(apps: List<LauncherApp>?, onOpen: (LauncherApp) -> Unit) {
    var focused by remember { mutableStateOf<LauncherApp?>(null) }
    val firstTile = remember { FocusRequester() }
    val current = focused ?: apps?.firstOrNull()

    Box(Modifier.fillMaxSize().background(Color.Black)) {
        AmbientBackdrop(current)

        if (apps != null) {
            LazyVerticalGrid(
                columns = GridCells.Fixed(5),
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(start = EdgeInset, end = EdgeInset, bottom = 64.dp),
                horizontalArrangement = Arrangement.spacedBy(36.dp),
                verticalArrangement = Arrangement.spacedBy(40.dp),
            ) {
                item(span = { GridItemSpan(maxLineSpan) }) { TopShelf(current) }
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

        StatusBar(Modifier.align(Alignment.TopEnd).padding(top = 40.dp, end = EdgeInset))
    }
}

/** Full-screen, heavily blurred copy of the focused app's art, so its colors tint the whole UI. */
@Composable
private fun AmbientBackdrop(app: LauncherApp?) {
    val drift = rememberInfiniteTransition(label = "kenBurns")
    val zoom by drift.animateFloat(
        initialValue = 1.05f, targetValue = 1.18f,
        animationSpec = infiniteRepeatable(tween(24_000, easing = LinearEasing), RepeatMode.Reverse),
        label = "zoom",
    )
    AnimatedContent(
        targetState = app,
        transitionSpec = { fadeIn(tween(700)) togetherWith fadeOut(tween(700)) },
        label = "backdrop",
        modifier = Modifier.fillMaxSize(),
    ) { current ->
        Box(Modifier.fillMaxSize()) {
            val art = current?.banner ?: current?.icon
            if (art != null) {
                // Blur needs Android 12+; older devices get a darker unblurred image.
                val look = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    Modifier.blur(56.dp).alpha(0.85f)
                } else {
                    Modifier.alpha(0.4f)
                }
                Image(
                    art, contentDescription = null, contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize().scale(zoom).then(look),
                )
            }
            // Cinematic scrims: darken the bottom for the grid and the left for the title.
            Box(
                Modifier.fillMaxSize().background(
                    Brush.verticalGradient(
                        0f to Color.Black.copy(alpha = 0.05f),
                        0.45f to Color.Black.copy(alpha = 0.55f),
                        0.75f to Color.Black.copy(alpha = 0.92f),
                        1f to Color.Black,
                    )
                )
            )
            Box(
                Modifier.fillMaxSize().background(
                    Brush.horizontalGradient(0f to Color.Black.copy(alpha = 0.55f), 0.6f to Color.Transparent)
                )
            )
        }
    }
}

@Composable
private fun TopShelf(app: LauncherApp?) {
    Box(Modifier.fillMaxWidth().height(330.dp)) {
        AnimatedContent(
            targetState = app,
            transitionSpec = { fadeIn(tween(500, delayMillis = 150)) togetherWith fadeOut(tween(250)) },
            label = "topShelf",
            modifier = Modifier.align(Alignment.BottomStart).padding(bottom = 36.dp),
        ) { current ->
            if (current != null) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    AppIcon(current.icon, size = 72)
                    Spacer(Modifier.width(24.dp))
                    Column {
                        Text(
                            text = current.label,
                            style = TextStyle(
                                color = Color.White, fontSize = 56.sp,
                                fontWeight = FontWeight.SemiBold, letterSpacing = (-0.5).sp,
                            ),
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                        Text(
                            text = "Açmak için OK tuşuna basın",
                            style = TextStyle(color = Secondary, fontSize = 18.sp, letterSpacing = 0.3.sp),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun AppIcon(icon: ImageBitmap, size: Int) {
    Box(
        Modifier.size(size.dp).clip(RoundedCornerShape((size * 0.22f).dp)).background(Color.White.copy(alpha = 0.12f)),
        contentAlignment = Alignment.Center,
    ) {
        Image(icon, contentDescription = null, modifier = Modifier.fillMaxSize().padding((size * 0.12f).dp))
    }
}

@Composable
private fun AppTile(app: LauncherApp, onFocus: () -> Unit, onClick: () -> Unit, modifier: Modifier = Modifier) {
    var isFocused by remember { mutableStateOf(false) }
    val focus by animateFloatAsState(if (isFocused) 1f else 0f, tween(220), label = "focus")

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
            scale = ClickableSurfaceDefaults.scale(focusedScale = 1.15f, pressedScale = 1.08f),
            colors = ClickableSurfaceDefaults.colors(containerColor = TileGray, focusedContainerColor = TileGray),
            glow = ClickableSurfaceDefaults.glow(
                focusedGlow = Glow(elevationColor = Color.White.copy(alpha = 0.22f), elevation = 24.dp),
            ),
            border = ClickableSurfaceDefaults.border(
                border = Border(BorderStroke(1.dp, Color.White.copy(alpha = 0.08f)), shape = TileShape),
                focusedBorder = Border(BorderStroke(2.dp, Color.White.copy(alpha = 0.55f)), shape = TileShape),
            ),
        ) {
            if (app.banner != null) {
                Image(app.banner, contentDescription = app.label, contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize())
            } else {
                Box(
                    Modifier.fillMaxSize().background(
                        Brush.verticalGradient(listOf(Color(0xFF3A3A3C), Color(0xFF1C1C1E)))
                    ),
                    contentAlignment = Alignment.Center,
                ) { AppIcon(app.icon, size = 72) }
            }
            // Glass highlight (tvOS "sheen"): a soft diagonal light across the focused tile.
            Box(
                Modifier.fillMaxSize().alpha(focus).background(
                    Brush.linearGradient(
                        0f to Color.White.copy(alpha = 0.28f),
                        0.45f to Color.White.copy(alpha = 0.04f),
                        1f to Color.Transparent,
                    )
                )
            )
            // Unfocused tiles sit slightly back so the focused one pops.
            Box(Modifier.fillMaxSize().alpha(1f - focus).background(Color.Black.copy(alpha = 0.22f)))
        }
        // Like tvOS, the name only appears under the focused tile.
        Text(
            text = app.label,
            style = TextStyle(color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.Medium),
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier.padding(top = 18.dp).alpha(focus),
        )
    }
}

@Composable
private fun StatusBar(modifier: Modifier = Modifier) {
    val now by produceState(initialValue = Date()) {
        while (true) {
            delay(1_000L * (60 - (System.currentTimeMillis() / 1000) % 60))
            value = Date()
        }
    }
    Column(modifier, horizontalAlignment = Alignment.End) {
        Text(
            text = SimpleDateFormat("HH:mm", Locale.getDefault()).format(now),
            style = TextStyle(color = Color.White, fontSize = 34.sp, fontWeight = FontWeight.Light, letterSpacing = 0.5.sp),
        )
        Text(
            text = SimpleDateFormat("EEEE, d MMMM", Locale.getDefault()).format(now),
            style = TextStyle(color = Secondary, fontSize = 16.sp, fontWeight = FontWeight.Medium),
        )
    }
}
