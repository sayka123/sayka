package com.sayka.appletvlauncher

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow

/** Voice commands understood by the TV, matched against recognized Turkish text. */
enum class VoiceCommand { BACK, NEXT, VOLUME_DOWN, VOLUME_UP }

object VoiceParser {
    fun parse(text: String): VoiceCommand? {
        val t = text.lowercase()
            .replace('ı', 'i').replace('ç', 'c').replace('ğ', 'g')
            .replace('ş', 's').replace('ö', 'o').replace('ü', 'u')
        return when {
            "ses" in t && ("kis" in t || "kapat" in t || "dusur" in t || "azalt" in t) -> VoiceCommand.VOLUME_DOWN
            "ses" in t && ("ac" in t || "yukselt" in t || "arttir" in t) -> VoiceCommand.VOLUME_UP
            "ses" in t -> null
            "geri" in t -> VoiceCommand.BACK
            "ileri" in t || "sonraki" in t || "siradaki" in t -> VoiceCommand.NEXT
            else -> null
        }
    }
}

/** In-process bus between the microphone service and the UI / accessibility service. */
object VoiceBus {
    private val _events = MutableSharedFlow<VoiceCommand>(extraBufferCapacity = 8)
    val events: SharedFlow<VoiceCommand> = _events.asSharedFlow()

    fun emit(command: VoiceCommand) { _events.tryEmit(command) }
}
