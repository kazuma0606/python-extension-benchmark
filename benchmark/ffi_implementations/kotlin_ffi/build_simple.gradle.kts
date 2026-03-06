plugins {
    kotlin("multiplatform") version "1.9.21"
}

repositories {
    mavenCentral()
}

kotlin {
    mingwX64("native") {
        binaries {
            sharedLib {
                baseName = "libfunctions"
            }
        }
    }
    
    sourceSets {
        val nativeMain by getting
    }
}