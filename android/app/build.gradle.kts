plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// Paramètres passés à la construction :  -PsiteUrl=https://mon-site.example/  -PversionCode=2
val siteUrl = (project.findProperty("siteUrl") as String?) ?: "https://A-REMPLIR.example/"
val siteHost = java.net.URI(siteUrl).host ?: "a-remplir.example"
val appVersionCode = ((project.findProperty("versionCode") as String?) ?: "1").toInt()

android {
    namespace = "fr.famille.photos"
    compileSdk = 34

    defaultConfig {
        applicationId = "fr.famille.photos"
        minSdk = 24
        targetSdk = 34
        versionCode = appVersionCode
        versionName = "1.$appVersionCode"
        buildConfigField("String", "SITE_URL", "\"$siteUrl\"")
        manifestPlaceholders["siteHost"] = siteHost
    }

    buildFeatures { buildConfig = true }

    signingConfigs {
        create("release") {
            val path = System.getenv("KEYSTORE_PATH")
            if (path != null) {
                storeFile = file(path)
                storePassword = System.getenv("KEYSTORE_PASSWORD")
                keyAlias = System.getenv("KEY_ALIAS")
                keyPassword = System.getenv("KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            // Sans clé de signature fournie, on signe avec la clé de debug (installable, mais les mises à jour exigeront la même clé).
            signingConfig = if (System.getenv("KEYSTORE_PATH") != null) signingConfigs.getByName("release") else signingConfigs.getByName("debug")
        }
    }

    lint {
        checkReleaseBuilds = false
        abortOnError = false
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.activity:activity-ktx:1.9.2")
    implementation("androidx.work:work-runtime-ktx:2.9.1")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
}
