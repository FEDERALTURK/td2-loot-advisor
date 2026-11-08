plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.federalturk.gamletsol"
    compileSdk = 36
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        applicationId = "com.federalturk.gamletsol"
        minSdk = flutter.minSdkVersion
        targetSdk = 36
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    buildTypes {
        release {
            // NOT (dürüstlük ilkesi, AGENTS.md): Bu ilk sürümde Play/beta imzalama
            // YOK — yalnızca derleme doğrulaması için debug anahtarıyla imzalanıyor.
            // mobile/ projesindeki kalıcı beta-imzalama düzeni (bkz.
            // docs/mobile_beta_signing_tr.md) gerçek bir yayın öncesi buraya da
            // eklenmeli.
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

dependencies {
    implementation("androidx.core:core:1.13.1")
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
