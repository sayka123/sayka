package com.sayka.appletvlauncher

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import kotlin.math.roundToInt

/** Current conditions, ready to draw. */
data class Weather(val celsius: Int, val label: String, val glyph: String)

/**
 * Live weather for Tekirdağ / Süleymanpaşa from Open-Meteo, which needs no API key.
 * Returns null on any failure so the launcher simply shows a placeholder.
 */
object WeatherRepository {
    private const val ENDPOINT =
        "https://api.open-meteo.com/v1/forecast?latitude=40.9781&longitude=27.5111" +
            "&current=temperature_2m,weather_code&timezone=Europe%2FIstanbul"

    suspend fun load(): Weather? = withContext(Dispatchers.IO) {
        val body = runCatching {
            val connection = (URL(ENDPOINT).openConnection() as HttpURLConnection).apply {
                connectTimeout = 5_000
                readTimeout = 5_000
            }
            try {
                connection.inputStream.bufferedReader().use { it.readText() }
            } finally {
                connection.disconnect()
            }
        }.getOrNull() ?: return@withContext null

        runCatching {
            val current = JSONObject(body).getJSONObject("current")
            val code = current.getInt("weather_code")
            Weather(current.getDouble("temperature_2m").roundToInt(), describe(code), glyph(code))
        }.getOrNull()
    }

    /** WMO weather codes, as documented by Open-Meteo. */
    private fun describe(code: Int): String = when (code) {
        0 -> "Açık"
        1 -> "Az bulutlu"
        2 -> "Parçalı bulutlu"
        3 -> "Kapalı"
        45, 48 -> "Sisli"
        51, 53, 55 -> "Çisenti"
        56, 57 -> "Dondurucu çisenti"
        61 -> "Hafif yağmurlu"
        63 -> "Yağmurlu"
        65 -> "Şiddetli yağmur"
        66, 67 -> "Dondurucu yağmur"
        71, 73, 75 -> "Karlı"
        77 -> "Kar taneleri"
        80, 81, 82 -> "Sağanak"
        85, 86 -> "Kar sağanağı"
        95 -> "Gök gürültülü"
        96, 99 -> "Dolulu fırtına"
        else -> "Bilinmiyor"
    }

    private fun glyph(code: Int): String = when (code) {
        0 -> "☀"
        1, 2 -> "⛅"
        3 -> "☁"
        45, 48 -> "🌫"
        51, 53, 55, 56, 57 -> "🌦"
        61, 63, 65, 66, 67, 80, 81, 82 -> "🌧"
        71, 73, 75, 77, 85, 86 -> "❄"
        95, 96, 99 -> "⛈"
        else -> "☁"
    }
}
