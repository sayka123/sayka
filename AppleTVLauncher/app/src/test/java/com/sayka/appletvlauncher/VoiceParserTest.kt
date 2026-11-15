package com.sayka.appletvlauncher

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class VoiceParserTest {
    @Test fun back() = assertEquals(VoiceCommand.BACK, VoiceParser.parse("geri git"))
    @Test fun next() {
        assertEquals(VoiceCommand.NEXT, VoiceParser.parse("ileri"))
        assertEquals(VoiceCommand.NEXT, VoiceParser.parse("sonraki kanal"))
    }
    @Test fun volume() {
        assertEquals(VoiceCommand.VOLUME_DOWN, VoiceParser.parse("sesi kıs"))
        assertEquals(VoiceCommand.VOLUME_DOWN, VoiceParser.parse("sesi kapat"))
        assertEquals(VoiceCommand.VOLUME_UP, VoiceParser.parse("sesi aç"))
        assertEquals(VoiceCommand.VOLUME_UP, VoiceParser.parse("ses aç"))
    }
    @Test fun unrelated() = assertNull(VoiceParser.parse("hava durumu nasıl"))
    @Test fun sesWithoutAction() = assertNull(VoiceParser.parse("ses"))
}
