package com.example.smart_hrms_mobile

import io.flutter.embedding.android.FlutterActivity
import android.os.Bundle

class MainActivity : FlutterActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        try {
            super.onCreate(savedInstanceState)
        } catch (e: Exception) {
            e.printStackTrace()
            android.util.Log.e("MainActivity", "Failed to create MainActivity", e)
            finish()
        }
    }
}
