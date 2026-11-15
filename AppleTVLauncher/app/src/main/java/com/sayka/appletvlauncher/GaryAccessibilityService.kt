package com.sayka.appletvlauncher

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

/**
 * Lets the "geri" voice command press Back in ANY app, not just this launcher.
 * The user must enable it once under Settings > Accessibility > Gary TV.
 */
class GaryAccessibilityService : AccessibilityService() {
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() {}

    override fun onServiceConnected() {
        instance = this
        VoiceBusListener.register(this)
    }

    override fun onDestroy() {
        if (instance === this) instance = null
        VoiceBusListener.unregister(this)
        super.onDestroy()
    }

    fun goBack(): Boolean = performGlobalAction(GLOBAL_ACTION_BACK)

    companion object {
        @Volatile
        var instance: GaryAccessibilityService? = null
    }
}

/** Bridges voice events to the accessibility service while it is enabled. */
private object VoiceBusListener {
    private var service: GaryAccessibilityService? = null
    private var job: kotlinx.coroutines.Job? = null

    fun register(s: GaryAccessibilityService) {
        service = s
        job = CoroutineScope(Dispatchers.Main).launch {
            VoiceBus.events.collect { command ->
                if (command == VoiceCommand.BACK) s.goBack()
            }
        }
    }

    fun unregister(s: GaryAccessibilityService) {
        if (service === s) {
            job?.cancel()
            job = null
            service = null
        }
    }
}
