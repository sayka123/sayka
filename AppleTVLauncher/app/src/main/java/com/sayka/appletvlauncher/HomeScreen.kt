package com.sayka.appletvlauncher

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.Crossfade
import androidx.compose.animation.core.animateFloatAsState
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.input.key.Key
import androidx.compose.ui.input.key.KeyEventType
import androidx.compose.ui.input.key.key
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.input.key.type
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Shadow
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.geometry.Offset
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
private val Secondary = Color.White.copy(alpha = 0.78f)
private val EdgeInset = 64.dp

// Sized so the Top Shelf plus two full rows of tiles fit a 1080p (960x540dp) TV screen.
private val ShelfHeight = 250.dp
private const val Columns = 5

/**
 * Apple TV style home: a cinematic Top Shelf for the focused app (its ambient
 * color washing the whole screen), then two visible rows of rounded 16:9 tiles
 * that lift, glow and catch a glass highlight on focus.
 */
@Composable
fun HomeScreen(
    apps: List<LauncherApp>?,
    onOpen: (LauncherApp) -> Unit,
    wallpaper: ImageBitmap? = null,
    onAssistant: () -> Unit = {},
    onReorder: (List<String>) -> Unit = {},
) {
    var focused by remember { mutableStateOf<LauncherApp?>(null) }
    var moving by remember { mutableStateOf<String?>(null) }
    val firstTile = remember { FocusRequester() }
    val tileFocus = remember { mutableMapOf<String, FocusRequester>() }
    val current = focused ?: apps?.firstOrNull()

    Box(Modifier.fillMaxSize().background(Color.Black)) {
        // Backdrop is always black; only a personal photo (if bundled) shows through.
        if (wallpaper != null) WallpaperBackdrop(wallpaper)

        if (apps != null) {
            LazyVerticalGrid(
                columns = GridCells.Fixed(Columns),
                modifier = Modifier.fillMaxSize().onPreviewKeyEvent { event ->
                    val packageName = moving ?: return@onPreviewKeyEvent false
                    if (event.type != KeyEventType.KeyDown) return@onPreviewKeyEvent true
                    val delta = when (event.key) {
                        Key.DirectionLeft -> -1
                        Key.DirectionRight -> 1
                        Key.DirectionUp -> -Columns
                        Key.DirectionDown -> Columns
                        else -> null
                    }
                    when {
                        delta != null -> AppOrder.shift(apps.map { it.packageName }, packageName, delta)?.let(onReorder)
                        event.key == Key.DirectionCenter || event.key == Key.Enter -> moving = null
                        event.key == Key.Back || event.key == Key.Escape -> moving = null
                    }
                    true
                },
                contentPadding = PaddingValues(start = EdgeInset, end = EdgeInset, bottom = 20.dp),
                horizontalArrangement = Arrangement.spacedBy(36.dp),
                verticalArrangement = Arrangement.spacedBy(22.dp),
            ) {
                item(span = { GridItemSpan(maxLineSpan) }) { TopShelf(current, onAssistant, moving != null) }
                itemsIndexed(apps, key = { _, app -> app.packageName }) { index, app ->
                    AppTile(
                        app = app,
                        moving = moving == app.packageName,
                        onFocus = { focused = app },
                        onClick = { if (moving != null) moving = null else onOpen(app) },
                        onLongClick = { moving = app.packageName },
                        modifier = if (index == 0) Modifier.focusRequester(firstTile)
                        else Modifier.focusRequester(tileFocus.getOrPut(app.packageName) { FocusRequester() }),
                    )
                }
            }
            LaunchedEffect(apps.isNotEmpty()) {
                if (apps.isNotEmpty()) runCatching { firstTile.requestFocus() }
            }
            // Voice commands: "ileri"/"sonraki" moves focus forward, "geri" moves it back.
            LaunchedEffect(Unit) {
                VoiceBus.events.collect { command ->
                    val list = apps ?: return@collect
                    if (list.isEmpty()) return@collect
                    val delta = when (command) {
                        VoiceCommand.NEXT -> 1
                        VoiceCommand.BACK -> -1
                        else -> return@collect
                    }
                    val idx = list.indexOfFirst { it.packageName == focused?.packageName }
                    val target = list.getOrNull(if (idx < 0) 0 else (idx + delta).coerceIn(0, list.lastIndex))
                    if (target != null) tileFocus[target.packageName]?.requestFocus()
                }
            }
        }

        StatusBar(Modifier.align(Alignment.TopEnd).padding(top = 40.dp, end = EdgeInset))
    }
}

/** A personal photo, kept sharp; scrims only where text and tiles need contrast. */
@Composable
private fun WallpaperBackdrop(wallpaper: ImageBitmap) {
    // TopCenter keeps faces (usually in the upper half) clear of the tile rows.
    Image(
        wallpaper, contentDescription = null, contentScale = ContentScale.Crop,
        alignment = Alignment.TopCenter, modifier = Modifier.fillMaxSize(),
    )
    Box(Modifier.fillMaxSize().background(WallpaperScrim))
    Box(Modifier.fillMaxSize().background(CornerScrim))
}

// Darkens the top-left corner behind the Top Shelf title, even over bright photos.
private val CornerScrim = Brush.radialGradient(
    0f to Color.Black.copy(alpha = 0.6f), 1f to Color.Transparent, center = Offset.Zero, radius = 1300f,
)
private val TextShadow = Shadow(Color.Black.copy(alpha = 0.6f), Offset(0f, 2f), blurRadius = 12f)
private val WallpaperScrim = Brush.verticalGradient(
    0f to Color.Black.copy(alpha = 0.6f),
    0.32f to Color.Transparent,
    0.5f to Color.Transparent,
    0.75f to Color.Black.copy(alpha = 0.55f),
    1f to Color.Black.copy(alpha = 0.85f),
)
private val TileSheen = Brush.linearGradient(
    0f to Color.White.copy(alpha = 0.28f),
    0.45f to Color.White.copy(alpha = 0.04f),
    1f to Color.Transparent,
)
private val TileFill = Brush.verticalGradient(listOf(Color(0xFF111113), Color(0xFF0A0A0C)))

@Composable
private fun TopShelf(app: LauncherApp?, onAssistant: () -> Unit, moving: Boolean) {
    Box(Modifier.fillMaxWidth().height(ShelfHeight)) {
        AnimatedContent(
            targetState = app,
            transitionSpec = { fadeIn(tween(200, delayMillis = 60)) togetherWith fadeOut(tween(120)) },
            label = "topShelf",
            modifier = Modifier.align(Alignment.TopStart).padding(top = 40.dp),
        ) { current ->
            if (current != null) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    AppIcon(current.icon, size = 72)
                    Spacer(Modifier.width(24.dp))
                    Column {
                        Text(
                            text = current.label,
                            style = TextStyle(
                                color = Color.White, fontSize = 52.sp,
                                fontWeight = FontWeight.SemiBold, letterSpacing = (-0.5).sp, shadow = TextShadow,
                            ),
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                        Text(
                            text = if (moving) "Yön tuşlarıyla taşıyın, OK ile bırakın" else "Açmak için OK, taşımak için basılı tutun",
                            style = TextStyle(color = Secondary, fontSize = 18.sp, letterSpacing = 0.3.sp, shadow = TextShadow),
                        )
                    }
                }
            }
        }
        AssistantButton(onAssistant, Modifier.align(Alignment.BottomEnd).padding(bottom = 4.dp))
    }
}

/** Opens the TV's AI assistant (Gemini / Google Assistant); reached with D-pad Up from the tiles. */
@Composable
private fun AssistantButton(onClick: () -> Unit, modifier: Modifier = Modifier) {
    val pill = RoundedCornerShape(50)
    Surface(
        onClick = onClick,
        modifier = modifier,
        shape = ClickableSurfaceDefaults.shape(pill),
        scale = ClickableSurfaceDefaults.scale(focusedScale = 1.08f),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = Color.White.copy(alpha = 0.14f),
            contentColor = Color.White,
            focusedContainerColor = Color.White,
            focusedContentColor = Color.Black,
        ),
        border = ClickableSurfaceDefaults.border(
            border = Border(BorderStroke(1.dp, Color.White.copy(alpha = 0.25f)), shape = pill),
        ),
    ) {
        Row(Modifier.padding(horizontal = 22.dp, vertical = 10.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("✦", style = TextStyle(brush = AssistantGradient, fontSize = 20.sp))
            Spacer(Modifier.width(10.dp))
            Text("Yapay Zekâ Asistanı", style = TextStyle(fontSize = 17.sp, fontWeight = FontWeight.Medium))
        }
    }
}

private val AssistantGradient = Brush.linearGradient(listOf(Color(0xFF4F8BFF), Color(0xFFB36BFF), Color(0xFFFF6B9A)))

@Composable
private fun AppIcon(icon: ImageBitmap, size: Int) {
    Box(
        Modifier.size(size.dp).clip(RoundedCornerShape((size * 0.22f).dp)).background(Color.White.copy(alpha = 0.12f)),
        contentAlignment = Alignment.Center,
    ) {
        Image(
            icon, contentDescription = null, filterQuality = FilterQuality.High,
            modifier = Modifier.fillMaxSize().padding((size * 0.12f).dp),
        )
    }
}

@Composable
private fun AppTile(
    app: LauncherApp,
    moving: Boolean,
    onFocus: () -> Unit,
    onClick: () -> Unit,
    onLongClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var isFocused by remember { mutableStateOf(false) }
    val focus by animateFloatAsState(if (isFocused) 1f else 0f, tween(140), label = "focus")

    Column(modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        Surface(
            onClick = onClick,
            onLongClick = onLongClick,
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
                focusedBorder = Border(
                    BorderStroke(if (moving) 4.dp else 3.dp, if (moving) Color(0xFFFFD60A) else Color.White),
                    shape = TileShape,
                ),
            ),
        ) {
            // Plain dark tile, no app artwork inside.
            Box(
                Modifier.fillMaxSize().background(TileFill).semantics { contentDescription = app.label },
            )
            // Glass highlight (tvOS "sheen"): a soft diagonal light across the focused tile.
            Box(Modifier.fillMaxSize().alpha(focus).background(TileSheen))
            // Unfocused tiles sit slightly back so the focused one pops.
            Box(Modifier.fillMaxSize().alpha(1f - focus).background(Color.Black.copy(alpha = 0.12f)))
        }
        // Like tvOS, the name only appears under the focused tile.
        Text(
            text = app.label,
            style = TextStyle(color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.Medium),
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier.padding(top = 6.dp).alpha(if (moving) 1f else focus),
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
            style = TextStyle(color = Color.White, fontSize = 34.sp, fontWeight = FontWeight.Light, letterSpacing = 0.5.sp, shadow = TextShadow),
        )
        Text(
            text = SimpleDateFormat("EEEE, d MMMM", Locale.getDefault()).format(now),
            style = TextStyle(color = Secondary, fontSize = 16.sp, fontWeight = FontWeight.Medium, shadow = TextShadow),
        )
    }
}
