package com.federalturk.td2companion

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.content.pm.PackageManager
import android.provider.Settings
import androidx.core.content.FileProvider
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.embedding.android.FlutterActivity
import io.flutter.plugin.common.MethodChannel
import java.io.File

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "td2_companion/update")
            .setMethodCallHandler { call, result ->
                if (call.method == "packageVersion") {
                    val info = packageManager.getPackageInfo(packageName, 0)
                    result.success(info.versionName)
                    return@setMethodCallHandler
                }
                if (call.method != "installApk") {
                    result.notImplemented()
                    return@setMethodCallHandler
                }
                try {
                    val path = call.argument<String>("path") ?: throw IllegalArgumentException("APK yolu boş")
                    val apk = File(path)
                    if (!apk.isFile) throw IllegalArgumentException("APK bulunamadı")
                    val appFiles = filesDir.canonicalFile.toPath()
                    val apkPath = apk.canonicalFile.toPath()
                    if (!apkPath.startsWith(appFiles)) {
                        throw SecurityException("APK yolu uygulama dizini dışında")
                    }
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                        val flags = PackageManager.GET_SIGNING_CERTIFICATES
                        val candidate = packageManager.getPackageArchiveInfo(apk.path, flags)
                            ?: throw IllegalArgumentException("APK paketi okunamadı")
                        if (candidate.packageName != packageName) {
                            throw SecurityException("APK uygulama kimliği eşleşmiyor")
                        }
                        val installed = packageManager.getPackageInfo(packageName, flags)
                        val candidateSigners = candidate.signingInfo?.apkContentsSigners
                            ?: throw SecurityException("APK imza bilgisi yok")
                        val installedSigning = installed.signingInfo
                            ?: throw SecurityException("Kurulu uygulama imza bilgisi yok")
                        if (candidateSigners.isEmpty() || candidateSigners.any { signer ->
                                !packageManager.hasSigningCertificate(
                                    packageName,
                                    signer.toByteArray(),
                                    PackageManager.CERT_INPUT_RAW_X509,
                                )
                            }) {
                            throw SecurityException("APK imzası kurulu uygulamayla eşleşmiyor")
                        }
                        val candidateVersion = candidate.longVersionCode
                        if (candidateVersion <= installed.longVersionCode) {
                            throw SecurityException("APK sürümü kurulu sürümden yeni değil")
                        }
                    }
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O &&
                        !packageManager.canRequestPackageInstalls()) {
                        startActivity(Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                            Uri.parse("package:$packageName")))
                        result.error("INSTALL_PERMISSION",
                            "Bu uygulamadan yüklemeye izin verin; ardından geri dönüp güncelleme düğmesine tekrar basın.", null)
                        return@setMethodCallHandler
                    }
                    val uri = FileProvider.getUriForFile(this, "$packageName.fileprovider", apk)
                    startActivity(Intent(Intent.ACTION_VIEW).apply {
                        setDataAndType(uri, "application/vnd.android.package-archive")
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_GRANT_READ_URI_PERMISSION)
                    })
                    result.success(true)
                } catch (error: Exception) {
                    result.error("INSTALL_FAILED", error.message, null)
                }
            }
    }
}
