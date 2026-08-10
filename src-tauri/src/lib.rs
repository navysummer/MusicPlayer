mod metadata;
mod stream;
mod update;

use anyhow::Result;
use metadata::AudioMetadata;
use serde::Serialize;
use std::sync::Mutex;
use tauri_plugin_dialog::DialogExt;
use tauri_plugin_opener::OpenerExt;

struct AppState {
    stream_server: Mutex<stream::StreamServer>,
    current_path: Mutex<Option<String>>,
}

#[derive(Debug, Serialize)]
struct MediaResult {
    metadata: AudioMetadata,
    stream_url: String,
    lrc_content: Option<String>,
}

#[tauri::command]
async fn open_media(state: tauri::State<'_, AppState>, uri: String) -> Result<MediaResult, String> {
    let path = uri.clone();

    let meta = metadata::read_metadata(&path).map_err(|e| e.to_string())?;

    let lrc_content = metadata::load_lrc_file(&path);

    let stream_url = {
        let mut server = state.stream_server.lock().map_err(|e| e.to_string())?;
        if !server.is_active() {
            server.start().map_err(|e| e.to_string())?;
        }
        let port = server.port();
        let encoded_path = urlencoding(&path);
        format!("http://127.0.0.1:{}/stream?path={}", port, encoded_path)
    };

    {
        let mut current = state.current_path.lock().map_err(|e| e.to_string())?;
        *current = Some(path);
    }

    Ok(MediaResult {
        metadata: meta,
        stream_url,
        lrc_content,
    })
}

#[tauri::command]
async fn open_file_dialog(app: tauri::AppHandle) -> Result<Vec<String>, String> {
    let files = app
        .dialog()
        .file()
        .add_filter("音频文件", &[
            "mp3", "flac", "wav", "ogg", "aac", "m4a", "wma", "opus",
            "ape", "alac", "aiff", "dsf", "dff",
        ])
        .add_filter("所有文件", &["*"])
        .blocking_pick_files();

    match files {
        Some(paths) => {
            let result: Vec<String> = paths
                .into_iter()
                .filter_map(|p| p.as_path().map(|p| p.to_string_lossy().to_string()))
                .collect();
            Ok(result)
        }
        None => Ok(vec![]),
    }
}

#[tauri::command]
async fn open_folder_dialog(app: tauri::AppHandle) -> Result<Option<String>, String> {
    let dir = app
        .dialog()
        .file()
        .blocking_pick_folder();

    match dir {
        Some(d) => Ok(d.as_path().map(|p| p.to_string_lossy().to_string())),
        None => Ok(None),
    }
}

#[tauri::command]
async fn stream_status(state: tauri::State<'_, AppState>) -> Result<serde_json::Value, String> {
    let server = state.stream_server.lock().map_err(|e| e.to_string())?;
    Ok(serde_json::json!({
        "active": server.is_active(),
        "bytes_written": server.bytes_written(),
    }))
}

#[tauri::command]
async fn stop_playback(state: tauri::State<'_, AppState>) -> Result<(), String> {
    let mut server = state.stream_server.lock().map_err(|e| e.to_string())?;
    server.stop();
    let mut current = state.current_path.lock().map_err(|e| e.to_string())?;
    *current = None;
    Ok(())
}

#[tauri::command]
async fn get_metadata(path: String) -> Result<AudioMetadata, String> {
    metadata::read_metadata(&path).map_err(|e| e.to_string())
}

#[tauri::command]
async fn load_lrc(path: String) -> Result<Option<String>, String> {
    Ok(metadata::load_lrc_file(&path))
}

#[tauri::command]
async fn scan_folder(path: String) -> Result<Vec<String>, String> {
    let mut files = Vec::new();
    let extensions = [
        "mp3", "flac", "wav", "ogg", "aac", "m4a", "wma", "opus",
        "ape", "alac", "aiff", "dsf", "dff",
    ];

    fn scan_dir(
        dir: &std::path::Path,
        extensions: &[&str],
        files: &mut Vec<String>,
        depth: u32,
    ) -> Result<(), String> {
        if depth > 10 {
            return Ok(());
        }
        let entries = std::fs::read_dir(dir).map_err(|e| e.to_string())?;
        for entry in entries {
            let entry = entry.map_err(|e| e.to_string())?;
            let path = entry.path();
            if path.is_dir() {
                scan_dir(&path, extensions, files, depth + 1)?;
            } else if path.is_file() {
                if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
                    if extensions.contains(&ext.to_lowercase().as_str()) {
                        files.push(path.to_string_lossy().to_string());
                    }
                }
            }
        }
        Ok(())
    }

    let p = std::path::Path::new(&path);
    if p.is_dir() {
        scan_dir(p, &extensions, &mut files, 0)?;
    }

    Ok(files)
}

#[tauri::command]
async fn open_external(app: tauri::AppHandle, url: String) -> Result<(), String> {
    app.opener()
        .open_url(&url, None::<String>)
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn check_update() -> Result<update::UpdateInfo, String> {
    tauri::async_runtime::spawn_blocking(|| {
        let version = env!("CARGO_PKG_VERSION").to_string();
        update::check_update(&version)
    })
    .await
    .map_err(|e| e.to_string())?
    .map_err(|e| e.to_string())
}

fn urlencoding(s: &str) -> String {
    let mut result = String::new();
    for byte in s.bytes() {
        match byte {
            b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => {
                result.push(byte as char);
            }
            _ => {
                result.push_str(&format!("%{:02X}", byte));
            }
        }
    }
    result
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .manage(AppState {
            stream_server: Mutex::new(stream::StreamServer::new()),
            current_path: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            open_media,
            open_file_dialog,
            open_folder_dialog,
            stream_status,
            stop_playback,
            get_metadata,
            load_lrc,
            scan_folder,
            open_external,
            check_update,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}