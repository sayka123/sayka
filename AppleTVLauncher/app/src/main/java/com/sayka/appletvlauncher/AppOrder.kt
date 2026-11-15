package com.sayka.appletvlauncher

import android.content.Context

/** User-chosen tile order, kept across launches. New apps land at the end. */
object AppOrder {
    private const val PREFS = "gary_tv"
    private const val KEY = "order"

    fun apply(context: Context, apps: List<LauncherApp>): List<LauncherApp> {
        val saved = load(context)
        if (saved.isEmpty()) return apps
        val rank = saved.withIndex().associate { it.value to it.index }
        return apps.sortedWith(compareBy({ rank[it.packageName] ?: Int.MAX_VALUE }, { it.label.lowercase() }))
    }

    fun save(context: Context, packages: List<String>) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY, packages.joinToString("\n"))
            .apply()
    }

    /** Moves the package by [delta] slots. Returns null when the move would leave the list. */
    fun shift(packages: List<String>, moving: String, delta: Int): List<String>? {
        val from = packages.indexOf(moving)
        val to = from + delta
        if (from < 0 || to !in packages.indices) return null
        return packages.toMutableList().apply {
            add(to, removeAt(from))
        }
    }

    private fun load(context: Context): List<String> =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(KEY, null)
            ?.split('\n')
            ?.filter { it.isNotEmpty() }
            .orEmpty()
}
