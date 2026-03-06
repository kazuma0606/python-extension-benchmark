plugins {
    kotlin("multiplatform") version "1.9.21"
}

repositories {
    mavenCentral()
}

kotlin {
    val hostOs = System.getProperty("os.name")
    val isArm64 = System.getProperty("os.arch") == "aarch64"
    val isMingwX64 = hostOs.startsWith("Windows")
    
    val nativeTarget = when {
        hostOs == "Mac OS X" && isArm64 -> macosArm64("native")
        hostOs == "Mac OS X" && !isArm64 -> macosX64("native")
        hostOs == "Linux" && isArm64 -> linuxArm64("native")
        hostOs == "Linux" && !isArm64 -> linuxX64("native")
        isMingwX64 -> mingwX64("native")
        else -> throw GradleException("Host OS is not supported in Kotlin/Native.")
    }

    nativeTarget.apply {
        binaries {
            sharedLib {
                baseName = "libfunctions"
                
                // Configure compilation options for performance
                freeCompilerArgs += listOf(
                    "-opt",  // Enable optimizations
                    "-Xallocator=mimalloc"  // Use fast allocator
                )
            }
        }
        
        compilations.getByName("main") {
            cinterops {
                // No additional C interop needed for this implementation
            }
        }
    }

    sourceSets {
        val nativeMain by getting {
            dependencies {
                // No additional dependencies needed for FFI implementation
            }
        }
        
        val nativeTest by getting {
            dependencies {
                implementation(kotlin("test"))
            }
        }
    }
}

// Task to copy the built library to the correct location
tasks.register<Copy>("copySharedLib") {
    dependsOn("linkReleaseSharedNative")
    
    val hostOs = System.getProperty("os.name")
    val isArm64 = System.getProperty("os.arch") == "aarch64"
    val isMingwX64 = hostOs.startsWith("Windows")
    
    val libExtension = when {
        hostOs == "Mac OS X" -> "dylib"
        isMingwX64 -> "dll"
        else -> "so"
    }
    
    val libPrefix = if (isMingwX64) "" else "lib"
    val libName = "${libPrefix}libfunctions.$libExtension"
    
    from("build/bin/native/releaseShared/")
    into(".")
    include("*libfunctions*")
    
    doLast {
        println("Copied Kotlin FFI library to current directory")
    }
}

// Make the copy task run after building
tasks.named("build") {
    finalizedBy("copySharedLib")
}

// Clean task to remove generated libraries
tasks.register<Delete>("cleanLibs") {
    delete(fileTree(".") {
        include("*.so", "*.dll", "*.dylib")
        include("lib*.so", "lib*.dll", "lib*.dylib")
    })
}

tasks.named("clean") {
    dependsOn("cleanLibs")
}