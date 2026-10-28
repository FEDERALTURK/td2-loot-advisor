import java.util.Properties

plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

val playSigningFile = rootProject.file("key.properties")
val usePlaySigning = providers.gradleProperty("playRelease").orNull == "true"
val playSigningProperties = Properties()
if (usePlaySigning) {
    require(playSigningFile.isFile) {
        "Play signing requested, but android/key.properties is missing. See mobile/PLAY_STORE_RELEASE_TR.md."
    }
    playSigningFile.inputStream().use { playSigningProperties.load(it) }
    listOf("storeFile", "storePassword", "keyAlias", "keyPassword").forEach { key ->
        require(!playSigningProperties.getProperty(key).isNullOrBlank()) {
            "Play signing property '$key' is missing in android/key.properties."
        }
    }
}

android {
    namespace = "com.federalturk.td2companion"
    compileSdk = 36
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        applicationId = "com.federalturk.td2companion"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = 36
        // Uses the version code from pubspec.yaml. When using split APKs, 1000 * ABI_VERSION
        // is added automatically by Flutter. (https://developer.android.com/studio/build/configure-apk-splits#configure-APK-versions)
        // You can force using the value of versionCode by specifying the `-P force-version-code-ignoring-abi=true`
        // flag during build.
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        if (usePlaySigning) {
            create("playRelease") {
                storeFile = rootProject.file(playSigningProperties.getProperty("storeFile"))
                storePassword = playSigningProperties.getProperty("storePassword")
                keyAlias = playSigningProperties.getProperty("keyAlias")
                keyPassword = playSigningProperties.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            // GitHub beta builds stay debug-signed; Play builds require explicit opt-in and a private upload key.
            signingConfig = if (usePlaySigning) {
                signingConfigs.getByName("playRelease")
            } else {
                signingConfigs.getByName("debug")
            }
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
