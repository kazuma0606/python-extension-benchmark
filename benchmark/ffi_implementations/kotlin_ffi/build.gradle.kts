plugins {
    kotlin("multiplatform") version "1.9.21"
}

repositories {
    mavenCentral()
}

kotlin {
    linuxX64("native") {
        binaries {
            sharedLib {
                baseName = "libfunctions"
                // Ensure C-compatible exports
                export(project(":"))
            }
        }
    }
    
    sourceSets {
        val nativeMain by getting {
            dependencies {
                // Add any required dependencies here
            }
        }
    }
}

// Ensure proper compilation
tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinNativeCompile> {
    kotlinOptions {
        freeCompilerArgs += listOf(
            "-opt-in=kotlinx.cinterop.ExperimentalForeignApi"
        )
    }
}