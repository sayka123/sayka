package com.sayka.appletvlauncher

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioManager
import android.os.Build
import android.os.Bundle
import android.os.IBinder
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.core.content.ContextCompat

/**
 * Always-on microphone listener for TV voice commands ("geri", "ileri", "ses kıs", "ses aç").
 * Runs as a foreground service so it also works while another app is in the foreground.
 */
class VoiceCommandsService : Service() {
    private var recognizer: SpeechRecognizer? = null
    private var listening = false

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        startForeground(NOTIF_ID, notification())
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED
        ) {
            stopSelf()
            return
        }
        startRecognizer()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // Restart the loop if the system kills and restarts us.
        if (recognizer == null && ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            == PackageManager.PERMISSION_GRANTED
        ) startRecognizer()
        return START_STICKY
    }

    override fun onDestroy() {
        listening = false
        runCatching { recognizer?.destroy() }
        recognizer = null
        super.onDestroy()
    }

    private fun startRecognizer() {
        if (listening || !SpeechRecognizer.isRecognitionAvailable(this)) return
        listening = true
        recognizer = SpeechRecognizer.createSpeechRecognizer(this).apply {
            setRecognitionListener(object : RecognitionListener {
                override fun onResults(results: Bundle) {
                    handle(results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION))
                    restart()
                }
                override fun onError(error: Int) { if (listening) restart() }
                override fun onReadyForSpeech(params: Bundle?) {}
                override fun onBeginningOfSpeech() {}
                override fun onRmsChanged(rmsdB: Float) {}
                override fun onBufferReceived(buffer: ByteArray?) {}
                override fun onEndOfSpeech() {}
                override fun onPartialResults(partialResults: Bundle?) {}
                override fun onEvent(eventType: Int, params: Bundle?) {}
            })
            startListening(intent())
        }
    }

    private fun restart() {
        runCatching { recognizer?.stopListening() }
        runCatching { recognizer?.startListening(intent()) }
    }

    private fun intent() = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
        putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
        putExtra(RecognizerIntent.EXTRA_LANGUAGE, "tr-TR")
        putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
        putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
    }

    private fun handle(results: ArrayList<String>?) {
        val text = results?.firstOrNull() ?: return
        when (VoiceParser.parse(text)) {
            VoiceCommand.VOLUME_DOWN -> adjustVolume(AudioManager.ADJUST_LOWER)
            VoiceCommand.VOLUME_UP -> adjustVolume(AudioManager.ADJUST_RAISE)
            VoiceCommand.BACK, VoiceCommand.NEXT -> VoiceParser.parse(text)?.let { VoiceBus.emit(it) }
            null -> {}
        }
    }

    private fun adjustVolume(direction: Int) {
        val audio = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        audio.adjustStreamVolume(AudioManager.STREAM_MUSIC, direction, AudioManager.FLAG_SHOW_UI)
    }

    private fun notification(): Notification {
        val nm = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            nm.createNotificationChannel(
                NotificationChannel(CHANNEL_ID, "Sesli komutlar", NotificationManager.IMPORTANCE_LOW).apply {
                    description = "Mikrofonu dinler: geri, ileri, ses kıs, ses aç"
                },
            )
        }
        return Notification.Builder(this, CHANNEL_ID)
            .setContentTitle("Gary TV sesli komutlar")
            .setContentText("“geri”, “ileri”, “ses kıs”, “ses aç” komutlarını dinliyor")
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setOngoing(true)
            .build()
    }

    companion object {
        private const val CHANNEL_ID = "voice_commands"
        private const val NOTIF_ID = 42

        fun start(context: Context) {
            val intent = Intent(context, VoiceCommandsService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) context.startForegroundService(intent)
            else context.startService(intent)
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, VoiceCommandsService::class.java))
        }
    }
}
