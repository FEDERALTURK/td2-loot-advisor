import java.util.Properties

plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
    // Push bildirimi (Faz 4): google-services.json eklenince bu satırın başındaki "//" kaldırılmalı.
    // Dosya yokken açılırsa Gradle "File google-services.json is missing" ile patlar — bkz.
    // docs/push_notifications_setup.md (depo köküne göre).
    // id("com.google.gms.google-services")
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

// GitHub beta kanalı: her CI çalışmasının farklı bir Gradle "debug" anahtarıyla
// imzalamasını (ve dolayısıyla kullanıcıların eski APK üstüne güncelleyememesini)
// önlemek için kalıcı, özel bir "beta" anahtarı kullanılır. Bu, Play yükleme
// anahtarından (playSigning) tamamen ayrıdır — iki dağıtım kanalı birbirinin
// anahtarını paylaşmaz. Bkz. docs/mobile_beta_signing_tr.md.
val betaSigningFile = rootProject.file("beta-key.properties")
val useBetaSigning = providers.gradleProperty("githubBetaRelease").orNull == "true"
val betaSigningProperties = Properties()
if (useBetaSigning) {
    require(betaSigningFile.isFile) {
        "GitHub beta signing requested, but android/beta-key.properties is missing. See docs/mobile_beta_signing_tr.md."
    }
    betaSigningFile.inputStream().use { betaSigningProperties.load(it) }
    listOf("storeFile", "storePassword", "keyAlias", "keyPassword").forEach { key ->
        require(!betaSigningProperties.getProperty(key).isNullOrBlank()) {
            "Beta signing property '$key' is missing in android/beta-key.properties."
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
        // flutter_local_notifications, Android 16 ve Java 17 kombinasyonunda
        // desugared java.time API'lerine ihtiyaç duyar.
        isCoreLibraryDesugaringEnabled = true
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
        if (useBetaSigning) {
            create("githubBetaRelease") {
                storeFile = rootProject.file(betaSigningProperties.getProperty("storeFile"))
                storePassword = betaSigningProperties.getProperty("storePassword")
                keyAlias = betaSigningProperties.getProperty("keyAlias")
                keyPassword = betaSigningProperties.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            // Öncelik: Play yükleme anahtarı > kalıcı GitHub beta anahtarı > yerel/geçici
            // debug anahtarı (sadece dağıtılmayan yerel denemeler için — bkz. yukarıdaki not).
            signingConfig = if (usePlaySigning) {
                signingConfigs.getByName("playRelease")
            } else if (useBetaSigning) {
                signingConfigs.getByName("githubBetaRelease")
            } else {
                signingConfigs.getByName("debug")
            }
        }
    }
}

dependencies {
    implementation("androidx.core:core:1.13.1")
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.5")
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
