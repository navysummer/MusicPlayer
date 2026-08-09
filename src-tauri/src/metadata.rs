use anyhow::{Context, Result};
use base64::Engine;
use lofty::file::TaggedFileExt;
use lofty::prelude::*;
use lofty::read_from_path;
use serde::Serialize;
use std::path::Path;

#[derive(Debug, Serialize, Clone)]
pub struct AudioMetadata {
    pub title: String,
    pub artist: String,
    pub album: String,
    pub duration: f64,
    pub cover_art: Option<String>,
    pub lyrics: Option<String>,
    pub has_lyrics: bool,
    pub sample_rate: u32,
    pub channels: u16,
    pub bitrate: u32,
}

pub fn read_metadata(path: &str) -> Result<AudioMetadata> {
    let file_path = Path::new(path);
    let tagged_file = read_from_path(file_path)
        .with_context(|| format!("Failed to read audio file: {}", path))?;

    let properties = tagged_file.properties();

    let (title, artist, album, cover_art, lyrics) = extract_tags(&tagged_file, file_path);

    let duration = properties.duration().as_secs_f64();
    let sample_rate = properties.sample_rate().unwrap_or(0);
    let channels = properties.channels().unwrap_or(0) as u16;
    let bitrate = properties.audio_bitrate().unwrap_or(0) as u32;

    let has_lyrics = lyrics.is_some();

    Ok(AudioMetadata {
        title,
        artist,
        album,
        duration,
        cover_art,
        lyrics,
        has_lyrics,
        sample_rate,
        channels,
        bitrate,
    })
}

fn extract_tags(
    tagged_file: &(impl AudioFile + TaggedFileExt),
    file_path: &Path,
) -> (String, String, String, Option<String>, Option<String>) {
    let mut title = String::new();
    let mut artist = String::new();
    let mut album = String::new();
    let mut cover_art: Option<String> = None;
    let mut lyrics: Option<String> = None;

    for tag in tagged_file.tags() {
        if title.is_empty() {
            title = tag
                .title()
                .map(|s| s.to_string())
                .unwrap_or_default();
        }
        if artist.is_empty() {
            artist = tag
                .artist()
                .map(|s| s.to_string())
                .unwrap_or_default();
        }
        if album.is_empty() {
            album = tag
                .album()
                .map(|s| s.to_string())
                .unwrap_or_default();
        }
        if cover_art.is_none() {
            if let Some(pic) = tag.pictures().first() {
                let mime_type = pic
                    .mime_type()
                    .map(|m| m.as_str().to_string())
                    .unwrap_or_else(|| "image/jpeg".to_string());
                if mime_type.starts_with("image/") {
                    let b64 = base64::engine::general_purpose::STANDARD.encode(pic.data());
                    cover_art = Some(format!("data:{};base64,{}", mime_type, b64));
                }
            }
        }
        if lyrics.is_none() {
            for item in tag.items() {
                let key = format!("{:?}", item.key()).to_uppercase();
                if key.contains("LYRIC") {
                    lyrics = item.value().text().map(|s| s.to_string());
                }
            }
        }
    }

    let file_name = file_path
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("未知曲目")
        .to_string();

    if title.is_empty() {
        title = file_name;
    }

    (title, artist, album, cover_art, lyrics)
}

pub fn load_lrc_file(path: &str) -> Option<String> {
    let p = Path::new(path);
    let lrc_path = p.with_extension("lrc");
    if lrc_path.exists() {
        std::fs::read_to_string(&lrc_path).ok()
    } else {
        None
    }
}