plugins {
    kotlin("multiplatform") version "1.9.24"
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
        val nativeTest by getting
    }
}

tasks.register<Copy>("copyLib") {
    dependsOn("linkReleaseSharedNative")
    from("build/bin/native/releaseShared/")
    into(".")
    include("*.dll")
}

tasks.named("build") {
    finalizedBy("copyLib")
}